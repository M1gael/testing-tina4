from tina4_python.core.router import get, post, noauth
from tina4_python.auth import Auth

@get("/ping")
async def ping(request, response):
    return response({"pong": True})

@get("/login")  # a logged-in browser: identity token held in the session, no Bearer
async def login(request, response):
    request.session.set("token", Auth.get_token_static({"user_id": 1}))
    return response({"logged_in": True})

@get("/profile")
async def profile(request, response):
    return response.render("profile.twig", {})

@post("/api/profile")  # default write route: auth required, no @noauth
async def save_profile(request, response):
    return response({"saved": True})

@noauth()
@post("/api/open")  # the ch10 exercise shape: a public write route
async def open_route(request, response):
    return response({"saved": True})

from tina4_python.core import run
run()
