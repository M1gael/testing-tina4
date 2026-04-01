from tina4_python.core.router import get

@get("/test/slicing")
async def test_slicing(request, response):
    return response.render("slicing_test.html", {"text": "0123456789"})
