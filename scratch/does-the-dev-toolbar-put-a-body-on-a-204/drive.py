"""Drive the REAL ASGI app and report what goes on the wire for each case.

Modelled on tests/test_head_no_body_conformance.py::drive, which is the
project's own instrument for "MUST NOT carry content" conformance.
"""
import asyncio, os, sys, json, tempfile, pathlib

os.environ["TINA4_DEBUG"] = os.environ.get("TINA4_DEBUG", "true")
work = tempfile.mkdtemp()
pathlib.Path(work, "src", "public").mkdir(parents=True)
os.chdir(work)

from tina4_python.core.router import Router, get as route_get, delete as route_delete
from tina4_python.core.server import app

Router.clear()

@route_get("/page")
async def _page(request, response):
    return response("<html><body><h1>hi</h1></body></html>")

@route_delete("/item/1", auth_required=False)
async def _del(request, response):
    return response(None, 204)

@route_get("/weird")
async def _weird(request, response):
    return response("<b>a 204 the handler gave a body to</b>", 204)


def drive(method, path, headers=None):
    sent = []
    scope = {"type": "http", "method": method, "path": path, "query_string": b"",
             "headers": headers or [], "client": ("127.0.0.1", 1)}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    hdrs = {k.decode().lower(): v.decode() for k, v in start.get("headers", [])}
    return start["status"], body, hdrs


CASES = [
    ("DELETE", "/item/1", "scaffolded delete: response(None, 204)"),
    ("OPTIONS", "/item/1", "OPTIONS on a known path -> 204 + Allow"),
    ("GET", "/page", "ordinary HTML 200 (the toolbar SHOULD land here)"),
    ("GET", "/weird", "handler returned a 204 WITH a body of its own"),
    ("HEAD", "/page", "HEAD (already covered by _stage_head_strip)"),
]

out = []
for method, path, why in CASES:
    status, body, hdrs = drive(method, path, [(b"origin", b"http://x.test")] if method == "OPTIONS" else [])
    out.append({
        "case": f"{method} {path}",
        "why": why,
        "status": status,
        "body_bytes": len(body),
        "content_length": hdrs.get("content-length"),
        "content_type": hdrs.get("content-type"),
        "toolbar_present": b"tina4-dev-toolbar" in body or b"__dev" in body,
    })
print(json.dumps(out, indent=2))
