from tina4_python.core.router import get
from tina4_python.core.server import run


@get("/hello")
async def hello(request, response):
    return response.html("<html><body><p>hello</p></body></html>")


if __name__ == "__main__":
    run(no_browser=True, no_reload=True)
