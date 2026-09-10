#!/usr/bin/env python3
"""Two local stand-in hosts for the skills installer, in one process.

  primary  127.0.0.1:<p>   answers every request 503, and counts them
  mirror   127.0.0.1:<m>   serves ./mirror, the real bytes for one ref

The 503 body copies what Fastly puts in front of raw.githubusercontent.com, so the
reproduction looks like the reported outage rather than a generic error.

Binds loopback only. Writes the primary's request count to --count-file on exit and
on every request, so a harness can read it without stopping the server.

  MODE=dead-primary   primary 503s always      (the reported outage)
  MODE=live-primary   primary serves ./mirror  (control: no outage)
  MODE=flaky-primary  primary 503s FAIL_RATE of the time (the reporter's actual run)
  MODE=dead-mirror    mirror 503s, primary healthy   (the fallback in reverse)
  MODE=dead-both      neither host answers           (nothing must be silently skipped)
"""
import http.server, os, socketserver, sys, threading, random

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")
MODE = os.environ.get("MODE", "dead-primary")
FAIL_RATE = float(os.environ.get("FAIL_RATE", "0.5"))
SEED = int(os.environ.get("SEED", "1"))
COUNT_FILE = os.environ.get("COUNT_FILE", "primary-requests.txt")

BODY = b"""<!DOCTYPE html><html><head><title>Fastly error: unknown domain</title></head>
<body><p>Error 54113</p><p>Details: cache-jnb-faor730034-JNB 1788852665 266338151</p>
<p>Varnish cache server</p></body></html>"""

count_lock = threading.Lock()
counts = {"primary": 0, "primary_503": 0, "mirror": 0, "mirror_503": 0}
rng = random.Random(SEED)


def bump(key):
    with count_lock:
        counts[key] += 1
        with open(COUNT_FILE, "w") as fh:
            fh.write("primary=%d primary_503=%d mirror=%d mirror_503=%d\n"
                     % (counts["primary"], counts["primary_503"],
                        counts["mirror"], counts["mirror_503"]))


def local_path(path):
    # Both hosts are asked for paths in their own shape. The mirror shape is
    # <repo>@<ref>/...; the primary shape is <repo>/<ref>/.... Normalise the
    # primary's shape onto the mirror tree so `live-primary` can serve real bytes.
    rel = path.lstrip("/").split("?")[0]
    parts = rel.split("/")
    if len(parts) >= 2 and "@" not in parts[0]:
        rel = "%s@%s" % (parts[0], parts[1])
        if len(parts) > 2:
            rel += "/" + "/".join(parts[2:])
    full = os.path.normpath(os.path.join(ROOT, rel))
    return full if full.startswith(ROOT) else None


class Base(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def send_503(self):
        self.send_response(503)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def send_file(self, full):
        if not full or not os.path.isfile(full):
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        with open(full, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Primary(Base):
    def do_GET(self):
        bump("primary")
        # "recover": the primary fails its first walk -- long enough to be written
        # off -- and is healthy from then on. Paired with a mirror that is missing
        # one file, this is the only shape that reaches the second pass.
        recovering = MODE == "recover" and counts["primary"] <= int(
            os.environ.get("RECOVER_AFTER", "4"))
        dead = MODE in ("dead-primary", "dead-both") or recovering or (
            MODE == "flaky-primary" and rng.random() < FAIL_RATE)
        if dead:
            bump("primary_503")
            self.send_503()
        else:
            self.send_file(local_path(self.path))

    do_HEAD = do_GET


class Mirror(Base):
    def do_GET(self):
        bump("mirror")
        if MODE in ("dead-mirror", "dead-both"):
            bump("mirror_503")
            self.send_503()
            return
        gap = os.environ.get("MIRROR_MISSING")
        if gap and self.path.endswith(gap):
            bump("mirror_503")
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_file(local_path(self.path))

    do_HEAD = do_GET


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    pport, mport = int(sys.argv[1]), int(sys.argv[2])
    bump("primary"); counts["primary"] = 0; bump("primary")  # reset count file
    counts["primary"] = 0
    with open(COUNT_FILE, "w") as fh:
        fh.write("primary=0 primary_503=0 mirror=0 mirror_503=0\n")
    a = Server(("127.0.0.1", pport), Primary)
    b = Server(("127.0.0.1", mport), Mirror)
    threading.Thread(target=a.serve_forever, daemon=True).start()
    threading.Thread(target=b.serve_forever, daemon=True).start()
    print("primary=%d mirror=%d mode=%s" % (pport, mport, MODE), flush=True)
    threading.Event().wait()


if __name__ == "__main__":
    main()
