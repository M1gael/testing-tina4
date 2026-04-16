from tina4_python.core.router import Router, get, post

# 5. Route Groups — Imperative style (documented in Chapter 2/10)
def register_api_v1(group):
    @group.get("/users")
    async def list_users(request, response):
        return response.json({"users": []})

    @group.get("/users/{id:int}")
    async def get_user(id, request, response):
        return response.json({"user": {"id": id, "name": "Alice"}})

    @group.post("/users")
    async def create_user(request, response):
        return response.json({"created": True}, 201)

    @group.get("/products")
    async def list_products(request, response):
        return response.json({"products": []})

Router.group("/api/v1", register_api_v1)

# Nested Groups
def register_v1(group):
    @group.get("/status")
    async def status_v1(request, response):
        return response.json({"version": "1.0"})

def register_v2(group):
    @group.get("/status")
    async def status_v2(request, response):
        return response.json({"version": "2.0"})

def register_api(group):
    Router.group("/v1", register_v1)
    Router.group("/v2", register_v2)

Router.group("/api", register_api)
