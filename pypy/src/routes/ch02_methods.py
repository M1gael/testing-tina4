# chapter 2: http methods
from tina4_python.core.router import get, post, put, patch, delete

@get("/products-test")
async def list_products(request, response):
    return response.json({"action": "list all products"})

@post("/products-test")
async def create_product(request, response):
    return response.json({"action": "create a product"}, 201)

@put("/products-test/{id}")
async def replace_product(id, request, response):
    return response.json({"action": f"replace product {id}"})

@patch("/products-test/{id}")
async def update_product(id, request, response):
    return response.json({"action": f"update product {id}"})

@delete("/products-test/{id}")
async def delete_product(id, request, response):
    return response.json({"action": f"delete product {id}"})
