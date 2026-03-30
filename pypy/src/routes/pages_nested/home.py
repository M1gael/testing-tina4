from tina4_python.core.router import get

# testing nested route directory discovery
@get("/nested/home")
async def nested_home(request, response):
    return response.html("<h1>Nested Home</h1>")
