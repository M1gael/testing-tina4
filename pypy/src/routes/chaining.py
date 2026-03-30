from tina4_python.core.router import get, Router

# 8. route chaining: .secure() and .cache()
# testing if the object returned by decorators or Router.add is chainable

@get("/api/account")
async def get_account(request, response):
    # this route should be secured via chaining
    return response.json({"account": getattr(request, "user", "no user found")})

# applying .secure() method as per documentation
try:
    get_account.secure()
except AttributeError as e:
    print(f"error: get_account.secure() failed: {e}")

# testing inline chaining with Router class
async def list_catalog(request, response):
    return response.json({"catalog": []})

try:
    Router.get("/api/catalog", list_catalog).cache()
except AttributeError as e:
    print(f"ERROR: Router.get().cache() failed: {e}")

# testing chained combination
async def handle_important_data(request, response):
    return response.json({"data": "important stuff"})

try:
    Router.get("/api/important_data", handle_important_data).secure().cache()
except AttributeError as e:
    print(f"error: Router.get().secure().cache() failed: {e}")
