from tina4_python.core.router import get, post, noauth
from tina4_python.auth import Auth

@get("/ping")
async def ping(request, response):
    return response({"pong": True})

@get("/login")  # identity token in the session: the auth gate passes, only CSRF decides
async def login(request, response):
    request.session.set("token", Auth.get_token_static({"user_id": 1}))
    return response({"logged_in": True})

@post("/api/save")  # default write route
async def save(request, response):
    return response({"saved": True})

@noauth()
@post("/api/open")
async def open_route(request, response):
    return response({"saved": True})

from tina4_python.core import run
run()
