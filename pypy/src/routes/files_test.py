from tina4_python.core.router import post, noauth

@post("/test/files")
@noauth()
async def test_files(request, response):
    return response.json({
        "files_keys": list(request.files.keys()),
        "body_keys": list(request.body.keys()) if isinstance(request.body, dict) else "not a dict"
    })
