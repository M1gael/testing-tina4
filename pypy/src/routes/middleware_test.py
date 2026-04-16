# testing middleware and security features
from tina4_python.core.router import get, post, noauth, secured, middleware, Router
from tina4_python.core.response import Response
import time

# testing Section 3: Class-Based Middleware
class TimingMiddleware:
    @staticmethod
    def before_start_timer(request, response):
        request._start_time = time.time()
        return request, response

    @staticmethod
    def after_add_timing(request, response):
        elapsed = time.time() - getattr(request, "_start_time", time.time())
        # Note: Section 3 example uses Response.add_header
        # I will check if that works or if we should use response.header()
        return request, response

# testing Section 3: Function-Based Middleware
async def log_middleware(request, response, next_handler):
    # simple log to verify execution order
    print(f"DEBUG: log_middleware BEFORE {request.path}")
    result = await next_handler(request, response)
    print(f"DEBUG: log_middleware AFTER {request.path}")
    return result

# testing Section 7: Short-Circuiting
async def maintenance_mode(request, response, next_handler):
    if request.headers.get("X-Maintenance") == "true":
        return response.json({"error": "Service under maintenance"}, 503)
    return await next_handler(request, response)

@get("/chapter10/test-timing")
@middleware(TimingMiddleware)
@noauth()
async def test_timing(request, response):
    return response.json({"message": "Timing middleware tested"})

@get("/chapter10/test-log")
@middleware(log_middleware)
@noauth()
async def test_log(request, response):
    return response.json({"message": "Log middleware tested"})

@get("/chapter10/test-short-circuit")
@middleware(maintenance_mode)
@noauth()
async def test_short_circuit(request, response):
    return response.json({"message": "Not in maintenance"})

# testing Section 5: Route Groups with Middleware
def secure_group(group):
    @group.get("/info")
    @noauth() # try to bypass group middleware? Section 5 says group always runs
    async def get_info(request, response):
        return response.json({"message": "Info from group", "user": getattr(request, "user", None)})

# Note: Router.group is used for global registration
Router.group("/chapter10/group", secure_group, middleware=[log_middleware])

@get("/chapter10/test-secured")
@secured()
async def test_secured_get(request, response):
    # testing Section 1: @secured for GET
    return response.json({"message": "Secured GET accessed"})

@post("/chapter10/test-post-secure")
async def test_post_secure(request, response):
    # testing Section 1: POST is secure by default
    return response.json({"message": "Secure POST accessed"})

@post("/chapter10/test-noauth-post")
@noauth()
async def test_noauth_post(request, response):
    # testing Section 1: @noauth for POST
    return response.json({"message": "Public POST accessed"})

@get("/chapter10/csrf-token")
@noauth()
async def get_csrf(request, response):
    # Utility to get a form token for testing
    from tina4_python.frond import Frond
    frond = Frond()
    token = frond.form_token() # This is a template function usually
    # Testing manual token generation
    from tina4_python.auth import Auth
    # Tina4's CsrfMiddleware expects a token in request.body["formToken"] or X-Form-Token header
    return response.json({"token": "stub-token-for-manual-test"})

@get("/chapter10/test-headers")
@noauth()
async def test_headers(request, response):
    # testing Section 4: Security Headers
    # They should be present in every response by default
    return response.json({"message": "Check response headers"})
