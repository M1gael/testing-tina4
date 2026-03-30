from tina4_python.core.router import get

@get("/hello")
async def hello(request, response):
    return response.json({"message": "Hello, World!"})

@get("/hello-redirect")
async def hello_redirect(request, response):
    return response.redirect("/hello")