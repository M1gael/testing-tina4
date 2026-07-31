from tina4_python.core.router import get


@get("/other")
async def other(request, response):
    return response.html(
        "<html><body>"
        "<h1>the other route</h1>"
        "<p>Somewhere that is not <code>/</code>.</p>"
        "<p><a href='/'>back to /</a></p>"
        "</body></html>"
    )
