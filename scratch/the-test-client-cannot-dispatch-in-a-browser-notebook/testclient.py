from tina4_python.core.router import get
from tina4_python.test_client import TestClient
@get("/hello/{name}")
async def hi(name, request, response):
    return response({"hi": name})
try:
    r = TestClient().get("/hello/Ann"); print("sync-run TestClient:", r.status, r.json())
except Exception as e:
    print("sync-run TestClient FAIL:", type(e).__name__, e)
