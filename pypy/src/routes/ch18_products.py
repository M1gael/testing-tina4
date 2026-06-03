# Supporting routes for Ch 18 testing — Section 5 assumes /api/products endpoints
# exist but the chapter never shows how to define them. These are minimal
# implementations following Ch 2's documented routing patterns so the patched
# test_ch18_routes.py can hit real handlers.

from tina4_python.core.router import get, post, delete
from src.orm.product import Product


def _to_dict(product):
    return {
        "id": product.id,
        "name": product.name,
        "category": getattr(product, "category", None),
        "price": product.price,
        "in_stock": getattr(product, "in_stock", True),
    }


@get("/api/products")
async def list_products(request, response):
    products = Product.where("1=1")
    return response.json({"data": [_to_dict(p) for p in products]}, 200)


@post("/api/products")
async def create_product(request, response):
    body = request.body
    if not body or not body.get("name"):
        return response.json({"error": "name is required"}, 400)
    product = Product()
    product.name = body.get("name")
    product.category = body.get("category")
    product.price = body.get("price", 0.0)
    if "in_stock" in body:
        product.in_stock = body["in_stock"]
    product.save()
    return response.json(_to_dict(product), 201)


@get("/api/products/{id:int}")
async def get_product(request, response):
    # Note: chapter 2 docs show `async def get_product(id, request, response)` with
    # path params as positional args, but the framework actually calls handlers as
    # `handler(request, response)` and exposes path params via request.params.
    id = int(request.params.get("id"))
    product = Product.find(id)
    if product is None:
        return response.json({"error": "Product not found"}, 404)
    return response.json(_to_dict(product), 200)


@delete("/api/products/{id:int}")
async def delete_product(request, response):
    id = int(request.params.get("id"))
    product = Product.find(id)
    if product is None:
        return response.json({"error": "Product not found"}, 404)
    product.delete()
    return response.json(None, 204)
