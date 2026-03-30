from tina4_python.core.router import get, noauth, secured

# 7. route decorators: @noauth() and @secured()
# note: in python, decorators apply from bottom to top. 
# flags like @noauth or @secured must be below @get to be seen during registration.

@get("/api/public/info")
@noauth()
async def public_info(request, response):
    return response.json({
        "app": "My Store",
        "version": "1.0.0"
    })

@get("/api/profile")
@secured()
async def profile(request, response):
    # request.user is populated by the auth middleware
    user = getattr(request, "user", "no user object found")
    return response.json({
        "user": user
    })
