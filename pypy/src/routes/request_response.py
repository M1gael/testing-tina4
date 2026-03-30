from tina4_python.core.router import get, post, put, delete
import os

# chapter 3: request and response
# testing core request and response features from documentation

# 1. the request object

# testing request.method
@get("/chapter3/check")
async def check_method(request, response):
    # returns the uppercase http method
    return response.json({
        "method": request.method,
        "response_methods": dir(response),
        "request_methods": dir(request)
    })

# testing request.path
@get("/chapter3/info")
async def info(request, response):
    # returns the url path without query strings
    return response.json({"path": request.path})

# testing path parameters as function arguments
@get("/chapter3/users/{id:int}/posts/{slug}")
async def user_post(id, slug, request, response):
    # path parameters must match function arguments
    return response.json({
        "user_id": id,
        "slug": slug
    })

# testing request.params (query string parameters)
@get("/chapter3/search")
async def search(request, response):
    # request.params is a dictionary of query parameters
    return response.json({
        "q": request.params.get("q", ""),
        "page": int(request.params.get("page", 1)),
        "sort": request.params.get("sort", "relevance")
    })

# testing request.body (parsed request body)
@post("/chapter3/feedback")
async def feedback(request, response):
    # request.body handles json and form data
    name = request.body.get("name", "anonymous")
    message = request.body.get("message", "")
    rating = request.body.get("rating", 0)

    return response.json({
        "received": {
            "name": name,
            "message": message,
            "rating": rating
        }
    }, 201)

# testing request.headers (case-insensitive dictionary)
@get("/chapter3/headers")
async def show_headers(request, response):
    # headers can be accessed with any case
    return response.json({
        "content_type": request.headers.get("content-type", "not set"),
        "user_agent": request.headers.get("user-agent", "not set"),
        "custom": request.headers.get("x-custom-header", "not set")
    })

# testing request.ip
@get("/chapter3/whoami")
async def whoami(request, response):
    # client's ip address
    return response.json({"ip": request.ip})

# testing request.cookies
@get("/chapter3/cookies")
async def show_cookies(request, response):
    # dictionary of cookies sent by the client
    return response.json({
        "cookies": request.cookies,
        "session_id": request.cookies.get("session_id", "none")
    })

# testing request.files (multipart file uploads)
@post("/chapter3/upload")
async def upload(request, response):
    # discrepancy: request.files is empty, multipart data is in request.body
    files_data = request.body if isinstance(request.body, dict) else {}
    if "document" not in files_data:
        return response.json({"error": "no file uploaded"}, 400)

    # discrepancy: metadata uses 'file_name' not 'filename'
    file = files_data["document"]

    return response.json({
        "filename": file.get("file_name", "unknown"),
        "size": file.get("size", 0)
    })

# testing request.files save to disk
@post("/chapter3/upload/save")
async def upload_and_save(request, response):
    # checking if request.body files can be saved correctly
    files_data = request.body if isinstance(request.body, dict) else {}
    if "photo" not in files_data:
        return response.json({"error": "no photo uploaded"}, 400)

    file = files_data["photo"]
    filename = file.get("file_name", "unknown")

    # ensure save directory exists
    save_dir = os.path.join("public", "images")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_path = os.path.join(save_dir, filename)
    
    # discrepancy: content is base64 encoded string
    import base64
    try:
        content = base64.b64decode(file["content"])
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
         return response.json({"error": f"save failed: {e}"}, 500)

    return response.json({
        "message": "photo uploaded",
        "url": f"/images/{filename}"
    }, 201)

# 2. the response object

# testing response.json with status codes
@get("/chapter3/status-test/{code:int}")
async def status_test(code, request, response):
    # optional second argument to json() sets the status code
    return response.json({"status": code}, code)

# testing response.html
@get("/chapter3/welcome-html")
async def welcome(request, response):
    # returns raw html
    return response.html("""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>welcome to my store</h1>
            <p>testing html response</p>
        </body>
        </html>
    """)

# testing response.text
@get("/chapter3/robots-test.txt")
async def robots(request, response):
    # returns plain text
    return response.text("user-agent: *\nallow: /")

# testing response.redirect
@get("/chapter3/old-url")
async def old_page(request, response):
    # redirects to new url with default 302
    return response.redirect("/chapter3/info")

# testing response.render
@get("/chapter3/dashboard")
async def dashboard(request, response):
    # rendering a template from src/templates
    return response.render("chapter3_test.html", {
        "user_name": "Sarah",
        "notifications": 7
    })

# testing response.file and force download
@get("/chapter3/download/test")
async def download_test(request, response):
    # create a dummy file for testing using absolute path
    dummy_path = os.path.abspath("data/test-report.txt")
    if not os.path.exists("data"):
        os.makedirs("data")
    
    with open(dummy_path, "w") as f:
        f.write("this is a test report")

    # testing Force Download with download_name
    return response.file(dummy_path, download_name="my-report.txt")

# testing response.header (chaining)
@get("/chapter3/headers-chain")
async def data_with_headers(request, response):
    # header methods are chainable
    return response.header("x-custom-header", "my-value") \
                   .header("x-request-id", "abc-123") \
                   .json({"data": "headers were set"})

# testing response.cookie (chaining)
@post("/chapter3/session-test")
async def session_test(request, response):
    # cookie methods are chainable
    return response.cookie("session_id", "abc123",
        path="/",
        max_age=3600,
        http_only=True,
        secure=False,
        same_site="Lax"
    ).json({"message": "cookie set"})
