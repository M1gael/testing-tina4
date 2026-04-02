from tina4_python.core.router import Router, get, post

# 5. Route Groups — Imperative style (documented in Chapter 2)
def register_api_v1():
    Router.get("/users", list_users)
    Router.get("/users/{id:int}", get_user)
    Router.post("/users", create_user)
    Router.get("/products", list_products)

async def list_users(request, response):
    return response.json({"users": []})

async def get_user(id, request, response):
    return response.json({"user": {"id": id, "name": "Alice"}})

async def create_user(request, response):
    return response.json({"created": True}, 201)

async def list_products(request, response):
    return response.json({"products": []})

Router.group("/api/v1", register_api_v1)

# Nested Groups
def register_v1():
    Router.get("/status", lambda req, res: res.json({"version": "1.0"}))

def register_v2():
    Router.get("/status", lambda req, res: res.json({"version": "2.0"}))

def register_api():
    Router.group("/v1", register_v1)
    Router.group("/v2", register_v2)

Router.group("/api", register_api)
