from tina4_python.core.router import get


@get("/")
async def home(request, response):
    return response.html(
        "<html><body>"
        "<h1>my own root route</h1>"
        "<p>This is MY route at <code>/</code>, not the framework landing page.</p>"
        "<p><a href='/other'>go to /other</a></p>"
        "</body></html>"
    )
