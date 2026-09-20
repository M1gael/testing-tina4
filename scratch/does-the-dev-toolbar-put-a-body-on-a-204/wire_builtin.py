"""Same 204, but through tina4's OWN HTTP/1.1 bridge (`tina4 serve`), not uvicorn."""
import os, sys, socket, asyncio, threading, time, tempfile, pathlib
os.environ["TINA4_DEBUG"] = "true"
work = tempfile.mkdtemp(); pathlib.Path(work, "src", "public").mkdir(parents=True); os.chdir(work)

from tina4_python.core.router import Router, get as route_get, delete as route_delete
from tina4_python.core.server import app, _http_reason

Router.clear()

@route_delete("/item/1", auth_required=False)
async def _del(request, response):
    return response(None, 204)

PORT = int(sys.argv[1])

# The bridge's connection handler, lifted verbatim from server.py::run->_serve
async def _handle_connection(reader, writer):
    raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=30)
    lines = raw.decode(errors="replace").split("\r\n")
    parts = lines[0].split(" ", 2)
    method, raw_path = parts[0], parts[1]
    path, _, qs = raw_path.partition("?")
    headers = []
    for line in lines[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers.append((k.strip().lower().encode(), v.strip().encode()))
    scope = {"type": "http", "method": method, "path": path, "query_string": qs.encode(),
             "headers": headers, "server": ("127.0.0.1", PORT), "client": ("127.0.0.1", 1)}
    body = b""
    resp_status, resp_headers, resp_body = 200, [], b""
    async def receive(): return {"type": "http.request", "body": body, "more_body": False}
    async def send(msg):
        nonlocal resp_status, resp_headers, resp_body
        if msg["type"] == "http.response.start":
            resp_status, resp_headers = msg["status"], msg.get("headers", [])
        elif msg["type"] == "http.response.body":
            resp_body = msg.get("body", b"")
    await app(scope, receive, send)
    writer.write(f"HTTP/1.1 {resp_status} {_http_reason(resp_status)}\r\n".encode())
    for n, v in resp_headers:
        writer.write(n + b": " + v + b"\r\n")
    writer.write(b"\r\n"); writer.write(resp_body)
    await writer.drain(); writer.close()

async def main():
    server = await asyncio.start_server(_handle_connection, "127.0.0.1", PORT)
    async with server:
        await asyncio.sleep(6)

threading.Thread(target=lambda: asyncio.run(main()), daemon=True).start()
time.sleep(1)

# 1. what a raw socket sees
s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
s.sendall(b"DELETE /item/1 HTTP/1.1\r\nHost: x\r\n\r\n")
time.sleep(0.5); buf = b""
s.settimeout(2)
try:
    while True:
        c = s.recv(65536)
        if not c: break
        buf += c
except socket.timeout: pass
s.close()
print("raw bytes:", len(buf), "| head:", repr(buf[:150]))

# 2. what a real HTTP client makes of it
import http.client
c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=5)
try:
    c.request("DELETE", "/item/1")
    r = c.getresponse()
    print(f"http.client: status={r.status} read={len(r.read())} bytes  (no exception)")
except Exception as e:
    print("http.client RAISED:", type(e).__name__, e)
