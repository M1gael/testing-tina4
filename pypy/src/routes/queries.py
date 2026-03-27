from tina4_python.core.router import get

# 4. Query Parameters
@get("/search")
async def search(request, response):
    q = request.params.get("q", "")
    page = int(request.params.get("page", 1))
    limit = int(request.params.get("limit", 10))

    return response.json({
        "query": q,
        "page": page,
        "limit": limit,
        "offset": (page - 1) * limit
    })
