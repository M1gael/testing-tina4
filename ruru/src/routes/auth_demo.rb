 # auth verification routes - ch08
def auth_middleware(request, response, next_handler)
  auth_header = request.headers["authorization"] || ""

  if auth_header.empty? || !auth_header.start_with?("Bearer ")
    response.json({ error: "Authorization required. Send: Authorization: Bearer <token>" }, 401)
  else
    token = auth_header.sub("Bearer ", "")
    if !Tina4::Auth.valid_token(token)
      response.json({ error: "Invalid or expired token. Please login again." }, 401)
    else
      request.user = Tina4::Auth.get_payload(token)
      next_handler.call(request, response)
    end
  end
end

# register
Tina4::Router.post("/api/register") do |request, response|
  body = request.body_parsed
  db = Tina4.database

  hash = Tina4::Auth.hash_password(body["password"])

  begin
    db.execute(
      "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
      [body["name"], body["email"], hash]
    )
    user = db.fetch_one("SELECT id, name, email, role, created_at FROM users WHERE id = last_insert_rowid()")
    response.json({ message: "Registration successful", user: user }, 201)
  rescue => e
    response.json({ error: e.message }, 400)
  end
end.no_auth

# login
Tina4::Router.post("/api/login") do |request, response|
  body = request.body_parsed
  db = Tina4.database

  user = db.fetch_one(
    "SELECT id, name, email, password_hash, role FROM users WHERE email = ?",
    [body["email"]]
  )
  puts "LOGIN DEBUG: body keys: #{body.keys}"
  puts "LOGIN DEBUG: email: #{body["email"]}"
  puts "LOGIN DEBUG: user keys: #{user&.keys}"

  if user.nil? || !Tina4::Auth.check_password(body["password"], user["password_hash"] || user[:password_hash])
    response.json({ error: "Invalid email or password" }, 401)
  else
    token = Tina4::Auth.get_token({
      "user_id" => user[:id] || user["id"],
      "email" => user[:email] || user["email"],
      "name" => user[:name] || user["name"],
      "role" => user[:role] || user["role"]
    })

    response.json({
      message: "Login successful",
      token: token,
      user: {
        id: user[:id] || user["id"],
        name: user[:name] || user["name"],
        email: user[:email] || user["email"],
        role: user[:role] || user["role"]
      }
    })
  end
end.no_auth

# profile
Tina4::Router.get("/api/profile", middleware: "auth_middleware") do |request, response|
  if request.user.nil?
    response.json({ error: "User data missing from request" }, 500)
  else
    response.json({
      user_id: request.user["user_id"],
      email: request.user["email"],
      name: request.user["name"]
    })
  end
end
