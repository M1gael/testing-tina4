# chapter 2: route groups
from tina4_python.core.router import Router, get, post

async def group_list_users(request, response):
    return response.json({"users": []})

async def group_get_user(id, request, response):
    return response.json({"user": {"id": id, "name": "Alice"}})

async def group_create_user(request, response):
    return response.json({"created": True}, 201)

async def group_list_products(request, response):
    return response.json({"products": []})

Router.group("/api/v1", lambda: [
    Router.get("/users", group_list_users),
    Router.get("/users/{id:int}", group_get_user),
    Router.post("/users", group_create_user),
    Router.get("/products", group_list_products),
])

async def v1_status(request, response):
    return response.json({"version": "1.0"})

async def v2_status(request, response):
    return response.json({"version": "2.0"})

Router.group("/api", lambda: [
    Router.group("/v1", lambda: [
        Router.get("/status", v1_status),
    ]),
    Router.group("/v2", lambda: [
        Router.get("/status", v2_status),
    ]),
])
