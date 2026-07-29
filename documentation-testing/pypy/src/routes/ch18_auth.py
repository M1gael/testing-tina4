# Supporting routes for Ch 18 S6 testing — assumes /api/auth/login + /api/profile
# exist but the chapter never shows how to define them (PY-18-11). These are
# minimal implementations using Tina4's built-in Auth class so the verbatim
# test_ch18_auth.py file can hit real handlers.
#
# Hardcoded admin user matches the chapter's test credentials verbatim:
#   email    = "admin@example.com"
#   password = "correct-password"

from tina4_python.core.router import get, post, noauth, secured
from tina4_python.auth import Auth


_ADMIN_USER = {
    "email": "admin@example.com",
    "password": "correct-password",
    "name": "Admin",
}


@noauth()
@post("/api/auth/login")
async def login(request, response):
    body = request.body or {}
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return response.json({"error": "email and password required"}, 400)

    if email != _ADMIN_USER["email"] or password != _ADMIN_USER["password"]:
        return response.json({"error": "invalid credentials"}, 401)

    # JWT with user payload — Auth.get_token() pads to >50 chars per S6 expectation
    token = Auth.get_token({"email": email, "name": _ADMIN_USER["name"]})
    return response.json({"token": token, "user": {"email": email, "name": _ADMIN_USER["name"]}}, 200)


@secured()
@get("/api/profile")
async def profile(request, response):
    # @secured() gate already rejected missing/invalid tokens with 401.
    # Decode the token to surface the user payload back to the caller.
    token = request.bearer_token()
    payload = Auth().valid_token(token)
    if not payload:
        return response.json({"error": "invalid token"}, 401)
    return response.json({"user": {"email": payload.get("email"), "name": payload.get("name")}}, 200)
