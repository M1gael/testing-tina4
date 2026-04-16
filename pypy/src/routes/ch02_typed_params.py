# chapter 2: typed parameters
from tina4_python.core.router import get

# integer parameter -- only digits match, auto-cast to int
@get("/orders/{id:int}")
async def get_order(id, request, response):
    # id is already an integer thanks to :int
    return response.json({
        "order_id": id,
        "type": type(id).__name__
    })

# integer parameter -- only digits match, auto-cast to int
@get("/products-typed/{id:int}")
async def get_product_typed(id, request, response):
    # id is an integer, e.g. 42
    return response.json({
        "product_id": id,
        "type": type(id).__name__
    })

# float parameter -- decimal numbers, auto-cast to float
@get("/products-typed/{id:int}/price/{price:float}")
async def check_price(id, price, request, response):
    return response.json({
        "product_id": id,
        "price": price,
        "type": type(price).__name__
    })

# path parameter -- catch-all, captures remaining segments as a string
@get("/files/{filepath:path}")
async def serve_file(filepath, request, response):
    # filepath could be "images/photos/cat.jpg"
    return response.json({
        "filepath": filepath,
        "type": type(filepath).__name__
    })
