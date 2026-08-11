from tina4_python.auth import Auth
from tina4_python.core.router import noauth, post


@post("/api/login")
@noauth()
async def login(request, response):
    data = request.body or {}
    if data.get("username") != "demo" or data.get("password") != "demo":
        return response.json({"error": "invalid credentials"}, 401)
    return response.json({"token": Auth.get_token({"username": "demo"})})
