from tina4_python.core.router import get

# Integer parameter -- only digits match, auto-cast to int
@get("/products/{id:int}")
async def get_product(id, request, response):
    # id is an integer, e.g. 42
    return response.json({
        "product_id": id,
        "type": type(id).__name__
    })

# Float parameter -- decimal numbers, auto-cast to float
@get("/products/{id:int}/price/{price:float}")
async def check_price(id, price, request, response):
    return response.json({
        "product_id": id,
        "price": price,
        "type": type(price).__name__
    })

# Path parameter -- catch-all, captures remaining segments as a string
@get("/files/{filepath:path}")
async def serve_file(filepath, request, response):
    # filepath could be "images/photos/cat.jpg"
    return response.json({
        "filepath": filepath,
        "type": type(filepath).__name__
    })