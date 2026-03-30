from tina4_python.core.router import get, post, put, delete

# testing full crud api for products based on documentation exercise
# testing in-memory store, path parameters, query parameters, and json request bodies

# in-memory product store (resets on server restart)
products = [
    {"id": 1, "name": "Wireless Keyboard", "category": "Electronics", "price": 79.99, "in_stock": True},
    {"id": 2, "name": "Yoga Mat", "category": "Fitness", "price": 29.99, "in_stock": True},
    {"id": 3, "name": "Coffee Grinder", "category": "Kitchen", "price": 49.99, "in_stock": False},
    {"id": 4, "name": "Standing Desk", "category": "Office", "price": 549.99, "in_stock": True},
    {"id": 5, "name": "Running Shoes", "category": "Fitness", "price": 119.99, "in_stock": True}
]

next_id = 6


# list all products, optionally filter by category
@get("/api/products")
async def list_products(request, response):
    category = request.params.get("category")

    if category is not None:
        filtered = [p for p in products if p["category"].lower() == category.lower()]
        return response.json({"products": filtered, "count": len(filtered)})

    return response.json({"products": products, "count": len(products)})


# get a single product by ID
@get("/api/products/{id:int}")
async def get_product(id, request, response):
    for product in products:
        if product["id"] == id:
            return response.json(product)

    return response.json({"error": "Product not found", "id": id}, 404)


# create a new product
@post("/api/products")
async def create_product(request, response):
    global next_id
    body = request.body

    if not body.get("name"):
        return response.json({"error": "Name is required"}, 400)

    product = {
        "id": next_id,
        "name": body["name"],
        "category": body.get("category", "Uncategorized"),
        "price": float(body.get("price", 0)),
        "in_stock": bool(body.get("in_stock", True))
    }
    next_id += 1

    products.append(product)

    return response.json(product, 201)


# replace a product
@put("/api/products/{id:int}")
async def replace_product(id, request, response):
    body = request.body

    for i, product in enumerate(products):
        if product["id"] == id:
            products[i] = {
                "id": id,
                "name": body.get("name", product["name"]),
                "category": body.get("category", product["category"]),
                "price": float(body.get("price", product["price"])),
                "in_stock": bool(body.get("in_stock", product["in_stock"]))
            }
            return response.json(products[i])

    return response.json({"error": "Product not found", "id": id}, 404)


# delete a product
@delete("/api/products/{id:int}")
async def delete_product(id, request, response):
    for i, product in enumerate(products):
        if product["id"] == id:
            products.pop(i)
            # note: response.json(None, 204) is used to return empty 204 response
            return response.json(None, 204)

    return response.json({"error": "Product not found", "id": id}, 404)
