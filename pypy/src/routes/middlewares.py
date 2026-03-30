from tina4_python.core.router import get, middleware
import time

# 6. middleware on routes

async def log_request(request, response, next_handler):
    start = time.time()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}")

    result = await next_handler(request, response)

    duration = round((time.time() - start) * 1000, 2)
    print(f"  Completed in {duration}ms")

    return result

@get("/api/data")
@middleware(log_request)
async def get_data(request, response):
    return response.json({"data": [1, 2, 3]})

# blocking middleware
async def require_api_key(request, response, next_handler):
    api_key = request.headers.get("x-api-key", "") # headers are lowercase in Request object

    if api_key != "my-secret-key":
        return response.json({"error": "Invalid API key"}, 401)

    return await next_handler(request, response)

@get("/api/secret")
@middleware(require_api_key)
async def secret_data(request, response):
    return response.json({"secret": "The answer is 42"})

# multiple middleware
@get("/api/important")
@middleware(log_request, require_api_key)
async def important_data(request, response):
    return response.json({"data": "important stuff"})
