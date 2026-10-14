from tina4_python.core.router import get
from tina4_python.core.server import app
@get("/hello/{name}")
async def hi(name, request, response):
    return response({"hi": name})
out = {}
async def receive(): return {"type": "http.request", "body": b"", "more_body": False}
async def send(m): out.setdefault(m["type"], m)
scope = {"type":"http","method":"GET","path":"/hello/Ann","raw_path":b"/hello/Ann","query_string":b"","headers":[(b"host",b"localhost")],"scheme":"http","server":("localhost",80),"client":("127.0.0.1",1),"http_version":"1.1","asgi":{"version":"3.0"},"root_path":""}
await app(scope, receive, send)
print("direct await app:", out["http.response.start"]["status"], out["http.response.body"]["body"])
