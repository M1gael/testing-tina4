from tina4_python import get, post, noauth

@get("/test-verify/{id:int}")
@noauth()
async def test_v74(id, request, response):
    return response.json({
        "signature_id": id,
        "request_params": request.params,
        "is_id_in_params": "id" in request.params
    })

@post("/test-upload")
@noauth()
async def test_upload(request, response):
    return response.json({
        "files_keys": list(request.files.keys()),
        "body_keys": list(request.body.keys()) if isinstance(request.body, dict) else "not a dict"
    })

@get("/test-wild/{*path}")
@noauth()
async def test_wild(request, response):
    return response.json({
        "params": request.params
    })
