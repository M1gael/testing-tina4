# chapter 2: route chaining secure and cache
from tina4_python.core.router import get, Router

@get("/api/account")
async def get_account_chain(request, response):
    return response.json({"account": getattr(request, "user", "guest")})

get_account_chain.secure()


async def list_catalog(request, response):
    return response.json({"catalog": ["Item 1", "Item 2"]})

Router.get("/api/catalog", list_catalog).cache()


async def chain_handler(request, response):
    return response.json({"data": "chained"})

Router.get("/api/data-chained", chain_handler).secure().cache()
