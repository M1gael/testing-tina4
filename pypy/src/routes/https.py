from tina4_python.core.router import get, post, put, patch, delete

@get("/products")
async def list_products(request, response):
    return response.json({"action": "list all products"})

@post("/products")
async def create_product(request, response):
    return response.json({"action": "create a product"}, 201)

@put("/products/{id}")
async def replace_product(id, request, response):
    return response.json({"action": f"replace product {id}"})

@patch("/products/{id}")
async def update_product(id, request, response):
    return response.json({"action": f"update product {id}"})

@delete("/products/{id}")
async def delete_product(id, request, response):
    return response.json({"action": f"delete product {id}"})