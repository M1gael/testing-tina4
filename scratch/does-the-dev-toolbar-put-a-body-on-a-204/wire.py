"""Put the 204 on a REAL socket, through uvicorn (keep-alive), and read what a
client sees — including the NEXT response on the same connection."""
import os, sys, socket, threading, time, tempfile, pathlib

os.environ["TINA4_DEBUG"] = "true"
work = tempfile.mkdtemp(); pathlib.Path(work, "src", "public").mkdir(parents=True); os.chdir(work)

from tina4_python.core.router import Router, get as route_get, delete as route_delete
from tina4_python.core.server import app
import uvicorn

Router.clear()

@route_get("/page")
async def _page(request, response):
    return response("<html><body><h1>hi</h1></body></html>")

@route_delete("/item/1", auth_required=False)
async def _del(request, response):
    return response(None, 204)

PORT = int(sys.argv[1])
cfg = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
srv = uvicorn.Server(cfg)
t = threading.Thread(target=srv.run, daemon=True); t.start()
for _ in range(100):
    time.sleep(0.05)
    if getattr(srv, "started", False): break

s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
s.sendall(b"DELETE /item/1 HTTP/1.1\r\nHost: x\r\nConnection: keep-alive\r\n\r\n")
time.sleep(0.4)
s.sendall(b"GET /page HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
time.sleep(0.6)
buf = b""
s.settimeout(2)
try:
    while True:
        c = s.recv(65536)
        if not c: break
        buf += c
except socket.timeout:
    pass
s.close()
print("=== RAW BYTES ON THE WIRE (DELETE then GET, one connection) ===")
print(repr(buf[:400]))
print("...")
print("total bytes:", len(buf))
print("responses seen:", buf.count(b"HTTP/1.1 "))
srv.should_exit = True
