from tina4_python.core.router import get

@get("/api/hello/{name}")
async def hello(name, request, response):
    # routing, JSON, and /swagger docs: handled
    return response({"hello": name})
