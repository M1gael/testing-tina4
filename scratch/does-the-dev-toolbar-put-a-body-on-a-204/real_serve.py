"""Start the REAL `tina4 serve` dev server (server.run) — blocking, main thread.
usage: real_serve.py <port> <appdir>   (the earlier harness re-implemented the
bridge; this one runs the shipped code path.)"""
import os, sys, pathlib

PORT, root = int(sys.argv[1]), sys.argv[2]
app = pathlib.Path(root, "src", "routes"); app.mkdir(parents=True, exist_ok=True)
pathlib.Path(root, "src", "public").mkdir(parents=True, exist_ok=True)
(app / "items.py").write_text('''
from tina4_python.core.router import get, delete

@get("/page")
async def page(request, response):
    return response("<html><body><h1>hi</h1></body></html>")

@delete("/item/{id}", auth_required=False)
async def del_item(request, response):
    return response(None, 204)
''')
os.chdir(root)
os.environ["TINA4_DEBUG"] = "true"
os.environ["TINA4_OVERRIDE_CLIENT"] = "true"

from tina4_python.core import server
server.run(host="127.0.0.1", port=PORT, no_browser=True, no_reload=True)
