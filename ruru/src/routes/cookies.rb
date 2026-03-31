 # testing cookies (set, read, delete) - ch03 section 6

 # set a cookie with full options
Tina4::Router.post("/login") do |request, response|
  response
    .cookie("session_id", "abc123xyz", {
      http_only: true,
      secure: true,
      same_site: "Strict",
      max_age: 3600,
      path: "/"
    })
    .json({ message: "Logged in" })
end

 # read a cookie from the incoming request
Tina4::Router.get("/profile") do |request, response|
  session_id = request.cookies["session_id"]

  if session_id.nil?
    return response.json({ error: "Not logged in" }, 401)
  end

  response.json({ session: session_id })
end

 # delete a cookie by setting max_age to 0
Tina4::Router.post("/logout") do |request, response|
  response
    .cookie("session_id", "", { max_age: 0, path: "/" })
    .json({ message: "Logged out" })
end
