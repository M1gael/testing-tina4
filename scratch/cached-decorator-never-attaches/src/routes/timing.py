import time

from tina4_python.core.router import get, cached


# Documented order: @cached ABOVE @get (docs/python/11-caching.md:235,
# docs/python/index.md:554).
@cached(max_age=120)
@get("/docs-order")
async def docs_order(request, response):
    return response({"t": time.time()})


# Reversed order, for comparison.
@get("/reversed-order")
@cached(max_age=120)
async def reversed_order(request, response):
    return response({"t": time.time()})


# The form that works today, as a control.
@get("/middleware-form", middleware=["ResponseCache:120"])
async def middleware_form(request, response):
    return response({"t": time.time()})


# No caching asked for.
@get("/undecorated")
async def undecorated(request, response):
    return response({"t": time.time()})
