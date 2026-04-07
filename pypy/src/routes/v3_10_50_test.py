from tina4_python import get, noauth
import requests

@get("/wild/{*path}")
@noauth()
async def test_wildcard(request, response):
    return response.json({
        "params": request.params,
        "is_star_set": "*" in request.params,
        "is_wildcard_set": "wildcard" in request.params
    })

# testing @group decorator
try:
    from tina4_python import group
    print("Export group: OK")
except ImportError:
    print("Export group: FAILED")
