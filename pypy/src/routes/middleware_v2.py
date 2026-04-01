from tina4_python.core.router import get, middleware

# test class-based middleware with before_ hook
class SimpleMiddleware:
    def before_simple(self, request, response):
        print(f"SimpleMiddleware before_ hook called for {request.path}")
        # we can attach data to request
        request.simple_data = "hello from middleware"
        return request, response

@get("/api/middleware-test")
@middleware(SimpleMiddleware)
async def middleware_test(request, response):
    data = getattr(request, "simple_data", "middleware NOT called")
    return response.json({"status": "ok", "middleware_data": data})
