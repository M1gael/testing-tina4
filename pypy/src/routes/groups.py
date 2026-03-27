from tina4_python.core.router import get, post, group

# 5. Route Groups
@group("/api/v1")
def api_v1():

    @get("/users")
    async def list_users(request, response):
        return response.json({"users": []})

    @get("/users/{id:int}")
    async def get_user(id, request, response):
        return response.json({"user": {"id": id, "name": "Alice"}})

    @post("/users")
    async def create_user(request, response):
        return response.json({"created": True}, 201)

    @get("/products")
    async def list_products(request, response):
        return response.json({"products": []})

# Nested Groups
@group("/api")
def api():

    @group("/v1")
    def v1():
        @get("/status")
        async def v1_status(request, response):
            return response.json({"version": "1.0"})

    @group("/v2")
    def v2():
        @get("/status")
        async def v2_status(request, response):
            return response.json({"version": "2.0"})
