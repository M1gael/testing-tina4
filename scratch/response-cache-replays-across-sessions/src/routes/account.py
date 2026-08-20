from tina4_python.core.router import get

USER_DATA = {
    "alice_session_token": {
        "user": "Alice Smith",
        "account_number": "ACC-9921",
        "balance": "$84,250.00",
    },
    "bob_session_token": {
        "user": "Bob Jones",
        "account_number": "ACC-1044",
        "balance": "$12.50",
    },
}


@get("/account/balance", middleware=["ResponseCache:300"])
async def account_balance(request, response):
    session = request.cookies.get("session", "anonymous")
    data = USER_DATA.get(
        session,
        {"user": "Anonymous", "account_number": "ACC-0000", "balance": "$0.00"},
    )
    return response(data)


@get("/account/no-store", middleware=["ResponseCache:300"])
async def account_no_store(request, response):
    session = request.cookies.get("session", "anonymous")
    data = USER_DATA.get(
        session,
        {"user": "Anonymous", "account_number": "ACC-0000", "balance": "$0.00"},
    )
    response.header("Cache-Control", "no-store")
    return response(data)


@get("/public/catalog", middleware=["ResponseCache:300"])
async def public_catalog(request, response):
    response.header("Cache-Control", "public, max-age=300")
    return response({"catalog": "standard-products", "items_count": 42})


@get("/public/anon", middleware=["ResponseCache:300"])
async def public_anon(request, response):
    return response({"service": "public-status", "status": "operational"})
