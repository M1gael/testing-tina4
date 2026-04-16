# chapter 2: wildcard and catch-all routes
from tina4_python.core.router import get

@get("/docs/*")
async def docs_handler(request, response):
    path = request.params.get("*", "")
    return response.json({
        "section": "docs",
        "path": path
    })

@get("/notfound/*") # using /notfound/* instead of /* to avoid blocking everything else for this test setup but literally it was /*
async def not_found_custom(request, response):
    return response.json({
        "error": "Page not found",
        "path": request.path
    }, 404)
