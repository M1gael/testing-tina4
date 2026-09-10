#!/usr/bin/env python3
"""Reproduce a raw.githubusercontent.com outage locally, without touching the network path
of anything else.

  MODE=proxy   an HTTPS forward proxy. Hosts listed in BLOCK get 503 on CONNECT; every
               other host is tunnelled normally. BLOCK=all blocks everything.
  MODE=origin  a plain-HTTP origin that answers every GET with 503, for measuring how many
               attempts a given curl invocation makes.

The 503 body copies the shape Fastly/Varnish returned to the reporter:
"Error 503 Backend.max_conn reached".

Binds 127.0.0.1 only. Stores nothing. Prints one line per blocked request to stderr.
"""
import os, select, socket, socketserver, sys, time

MODE  = os.environ.get("MODE", "proxy")
# Seconds to stall before answering a blocked request. Models a CDN that is slow
# as well as broken -- the case that decides whether retrying is bounded.
DELAY = float(os.environ.get("DELAY", "0"))
PORT  = int(os.environ.get("PORT", "0"))
BLOCK = [h for h in os.environ.get("BLOCK", "all").split(",") if h]

BODY = (b"<html><head><title>503 Backend.max_conn reached</title></head><body>"
        b"<h1>Error 503 Backend.max_conn reached</h1><p>Backend.max_conn reached</p>"
        b"<h3>Error 54113</h3><p>Varnish cache server</p></body></html>")
RESP_503 = (b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/html\r\n"
            b"Content-Length: " + str(len(BODY)).encode() + b"\r\n"
            b"Connection: close\r\n\r\n" + BODY)


def blocked(host):
    return "all" in BLOCK or host in BLOCK


def pump(a, b):
    socks = [a, b]
    while socks:
        r, _, x = select.select(socks, [], socks, 30)
        if x or not r:
            break
        for s in r:
            try:
                data = s.recv(65536)
            except OSError:
                return
            if not data:
                return
            (b if s is a else a).sendall(data)


class Handler(socketserver.StreamRequestHandler):
    timeout = 30

    def handle(self):
        line = self.rfile.readline(65536)
        if not line:
            return
        parts = line.decode("latin-1").split()
        while True:                                  # drain headers
            h = self.rfile.readline(65536)
            if h in (b"\r\n", b"\n", b""):
                break

        if MODE == "origin":
            self.log(line); self.wfile.write(RESP_503); return

        if len(parts) < 2 or parts[0].upper() != "CONNECT":
            self.log(line); self.wfile.write(RESP_503); return

        host, _, port = parts[1].partition(":")
        if blocked(host):
            if DELAY:
                time.sleep(DELAY)
            self.log(line); self.wfile.write(RESP_503); return

        try:
            upstream = socket.create_connection((host, int(port or 443)), 15)
        except OSError:
            self.wfile.write(RESP_503); return
        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n"); self.wfile.flush()
        with upstream:
            pump(self.connection, upstream)

    def log(self, line):
        sys.stderr.write("503 <- %s" % line.decode("latin-1"))
        sys.stderr.flush()

    def handle_error(self, *a):                      # a closed client is not news
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, *a):
        pass


if __name__ == "__main__":
    with Server(("127.0.0.1", PORT), Handler) as srv:
        sys.stderr.write("fake503 mode=%s block=%s port=%d\n"
                         % (MODE, ",".join(BLOCK), srv.server_address[1]))
        sys.stderr.flush()
        print(srv.server_address[1], flush=True)
        srv.serve_forever()
