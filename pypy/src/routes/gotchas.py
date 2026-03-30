from tina4_python.core.router import get, middleware

# 14. gotchas
# testing documented gotchas and their fixes

# gotcha 2: parameter names must be unique
@get("/gotcha/users/{id}/posts/{id}")
async def param_collision(id, request, response):
    # testing if the second {id} overwrites the first in request.params
    return response.json({
        "params": request.params,
        "note": "testing if second 'id' overwrote first"
    })

# gotcha 3: method conflicts and typed parameters
@get("/items/{id:int}")
async def item_by_id(id, request, response):
    return response.json({"type": "int", "value": id})

@get("/items/export")
async def item_export(request, response):
    return response.json({"type": "static", "value": "export"})

# gotcha 5: decorator order matters
# documentation says: @get first (closest to function), then middleware above it
async def log_gotcha(request, response, next_handler):
    print("gotcha middleware executed")
    return await next_handler(request, response)

@middleware(log_gotcha)
@get("/gotcha/order")
async def decorator_order_test(request, response):
    # testing if this order (documented as correct) actually works
    return response.json({"status": "executed"})

# gotcha 6: forgetting async def
@get("/gotcha/sync")
def sync_handler(request, response):
    # testing if the framework crashes or handles sync handlers
    return response.json({"status": "sync_executed"})
