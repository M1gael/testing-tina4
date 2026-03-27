from tina4_python.core.router import get

# 9. Wildcard and Catch-All Routes
# testing if the framework supports the '*' wildcard and correctly populates it in request.params

@get("/docs/*")
async def docs_handler(request, response):
    # testing if '*' is the key or if 'wildcard' is the key as suspected in framework analysis
    path_from_star = request.params.get("*", "Not Found with '*'")
    path_from_wildcard = request.params.get("wildcard", "Not Found with 'wildcard'")
    
    return response.json({
        "section": "docs",
        "path": path_from_star,
        "actual_params": request.params
    })

# Catch-All Route (Custom 404)
# This will handle any unmatched URL at the root level
# We use 'zzz_wildcards.py' or similar to ensure it's loaded last if needed
@get("/*")
async def not_found(request, response):
    return response.json({
        "error": "Page not found",
        "path": request.path,
        "actual_params": request.params
    }, 404)
