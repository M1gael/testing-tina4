# chapter 2: middleware on routes
from tina4_python.core.router import get, middleware
import time

class LogRequest:
    def before_request(self, request, response):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}")
        return request, response

    def after_request(self, request, response):
        print(f"  Completed: {response.status_code}")
        return request, response

@middleware(LogRequest)
@get("/api/data")
async def get_data(request, response):
    return response.json({"data": [1, 2, 3]})

class RequireApiKey:
    def before_check(self, request, response):
        api_key = request.headers.get("x-api-key", "")
        if api_key != "my-secret-key":
            return request, response.json({"error": "Invalid API key"}, 401)
        return request, response

@middleware(RequireApiKey)
@get("/api/secret")
async def secret_data(request, response):
    return response.json({"secret": "The answer is 42"})

@middleware(LogRequest, RequireApiKey)
@get("/api/important")
async def important_data(request, response):
    return response.json({"data": "important stuff"})
