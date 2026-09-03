#!/usr/bin/env python3
"""Transparent proxy in front of https://mcp.tina4.com/mcp.

MODE=passthrough  forward the upstream envelope byte for byte  (control)
MODE=drop         remove the top-level "signature" key         (candidate fix A)
MODE=into-result  move it to result.signature                  (candidate fix B)

Varies exactly one factor: the placement of the `signature` key. Everything
else on the wire is upstream's own bytes.
"""
import json, os, sys, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

UPSTREAM = "https://mcp.tina4.com/mcp"
MODE = os.environ.get("MODE", "passthrough")
PORT = int(os.environ.get("PORT", "8931"))


def transform(payload: bytes) -> bytes:
    if MODE == "passthrough":
        return payload
    try:
        msg = json.loads(payload)
    except Exception:
        return payload
    if not isinstance(msg, dict) or "signature" not in msg:
        return payload
    sig = msg.pop("signature")
    if MODE == "into-result" and isinstance(msg.get("result"), dict):
        msg["result"]["signature"] = sig
    return json.dumps(msg).encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        req = urllib.request.Request(UPSTREAM, data=body, method="POST")
        for h in ("Authorization", "Content-Type", "Accept"):
            if self.headers.get(h):
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                status, raw = r.status, r.read()
                ctype = r.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read()
            ctype = e.headers.get("Content-Type", "application/json")
        out = transform(raw)
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"proxy mode={MODE} on 127.0.0.1:{PORT}", file=sys.stderr, flush=True)
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
