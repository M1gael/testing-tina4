# Echo server (GET /slow sleeps 3s): replies JSON {method, path, query, ctype, auth, xh, body}. GET /ping -> 200.
import json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
class H(BaseHTTPRequestHandler):
    def _go(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n).decode() if n else ""
        u = urlsplit(self.path)
        if u.path == '/slow': time.sleep(3)
        out = json.dumps({"method": self.command, "path": u.path, "query": u.query, "ctype": self.headers.get("Content-Type"),
                          "auth": self.headers.get("Authorization"), "xh": self.headers.get("X-Probe"), "body": body}).encode()
        self.send_response(201 if self.command == "POST" else 200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _go
    def log_message(self, *a): pass
HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
