from tina4_python.core.router import get, noauth, secured

# 7. Route Decorators: @noauth() and @secured()
# NOTE: In Python, decorators apply from bottom to top. 
# Flags like @noauth or @secured must be BELOW @get to be seen during registration.

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
    user = getattr(request, "user", "No User Object Found")
    return response.json({
        "user": user
    })
