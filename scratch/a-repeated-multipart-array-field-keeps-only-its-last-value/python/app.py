from tina4_python.core.router import get, noauth, post
from tina4_python.core.server import run


@noauth()
@post("/echo")
async def echo(request, response):
    return response.json({"body": request.body})


@noauth()
@get("/q")
async def q(request, response):
    return response.json({"query": request.query})


if __name__ == "__main__":
    run(no_browser=True, no_reload=True)
