# testing auth and session chapters
from tina4_python.core.router import get, post, put, noauth, middleware, secured
from tina4_python.auth import Auth
from tina4_python.database.connection import Database

# testing Auth setup
async def auth_middleware(request, response, next_handler):
    # testing Section 6: Auth Middleware
    auth_header = request.headers.get("Authorization", "")

    if not auth_header or not auth_header.startswith("Bearer "):
        return response.json({"error": "Authorization required. Send: Authorization: Bearer <token>"}, 401)

    token = auth_header[7:]

    payload = Auth.valid_token(token)
    if payload is None:
        return response.json({"error": "Invalid or expired token. Please login again."}, 401)

    request.user = payload

    return await next_handler(request, response)

@get("/chapter8/init")
@noauth()
async def init_auth(request, response):
    # testing database setup for auth
    db = Database()
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        return response.json({"status": "success", "message": "Users table initialized"})
    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)

@post("/chapter8/register")
@noauth()
async def register(request, response):
    # testing Section 3: Password Hashing & Registration
    body = request.body

    if not body.get("name") or not body.get("email") or not body.get("password"):
        return response.json({"error": "Name, email, and password are required"}, 400)

    db = Database()
    
    # Check if email exists
    existing = db.fetch_one("SELECT id FROM users WHERE email = ?", [body["email"]])
    if existing:
        return response.json({"error": "Email already registered"}, 409)

    password_hash = Auth.hash_password(body["password"])
    
    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        [body["name"], body["email"], password_hash]
    )
    user_id = db.get_last_id()

    user = db.fetch_one("SELECT id, name, email FROM users WHERE id = ?", [user_id])
    return response.json({"message": "Registration successful", "user": user}, 201)

@post("/chapter8/login")
@noauth()
async def login(request, response):
    # testing Section 4: Login Flow
    body = request.body
    if not body.get("email") or not body.get("password"):
        return response.json({"error": "Email and password are required"}, 400)

    db = Database()
    user = db.fetch_one("SELECT id, name, email, password_hash, role FROM users WHERE email = ?", [body["email"]])

    if user is None or not Auth.check_password(body["password"], user["password_hash"]):
        return response.json({"error": "Invalid email or password"}, 401)

    token = Auth.get_token({
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"]
    })

    return response.json({"message": "Login successful", "token": token, "user": user})

@get("/chapter8/profile")
@middleware(auth_middleware)
async def get_profile(request, response):
    # testing Section 6/7: Protected Route (middleware)
    return response.json({"message": "Access granted", "user": request.user})

@get("/chapter8/secured")
@secured()
async def test_secured(request, response):
    # testing Section 7: @secured decorator
    # Note: request.user is automatically populated by @secured if it uses internal auth
    return response.json({"message": "Secured via decorator", "user": getattr(request, "user", None)})

# testing Sessions (Chapter 9)
@get("/chapter9/set-session")
@noauth()
async def set_session(request, response):
    # testing Section 4: Writing to Session
    request.session.set("test_key", "Hello Session")
    request.session.set("user_id", 123)
    return response.json({"message": "Session values set"})

@get("/chapter9/get-session")
@noauth()
async def get_session(request, response):
    # testing Section 4: Reading from Session
    data = {
        "test_key": request.session.get("test_key"),
        "user_id": request.session.get("user_id"),
        "all": request.session.all()
    }
    return response.json(data)

@get("/chapter9/flash-set")
@noauth()
async def flash_set(request, response):
    # testing Section 5: Flash Messages
    request.session.flash("message", "Redirect Success!")
    return response.json({"message": "Flash message set"})

@get("/chapter9/flash-get")
@noauth()
async def flash_get(request, response):
    # testing Section 5: Reading Flash Message (will delete it)
    msg = request.session.flash("message")
    return response.json({"flash": msg})

@get("/chapter9/cookie-set")
@noauth()
async def cookie_set(request, response):
    # testing Section 6: Setting Cookies
    return response.cookie("theme", "dark", {"max_age": 3600}) \
                   .cookie("lang", "en") \
                   .json({"message": "Cookies set"})

@get("/chapter9/cookie-get")
@noauth()
async def cookie_get(request, response):
    # testing Section 6: Reading Cookies
    return response.json({
        "theme": request.cookies.get("theme"),
        "lang": request.cookies.get("lang")
    })
