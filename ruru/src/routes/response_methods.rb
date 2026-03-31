 # testing response methods - ch03 section 3

 # json with a status code as second argument
Tina4::Router.get("/demo/json") do |request, response|
  response.json({ id: 7, name: "Widget" }, 201)
end

 # html response
Tina4::Router.get("/demo/html") do |request, response|
  response.html("<h1>Hello</h1><p>This is HTML.</p>")
end

 # plain text response
Tina4::Router.get("/demo/text") do |request, response|
  response.text("Just a plain string.")
end

 # xml response
Tina4::Router.get("/api/feed") do |request, response|
  response.xml("<feed><entry><title>Hello</title></entry></feed>")
end

 # structured error envelope
Tina4::Router.post("/api/things") do |request, response|
  response.error("VALIDATION_FAILED", "Name is required", 400)
end

 # redirect to another path (302 by default)
Tina4::Router.get("/demo/redirect") do |request, response|
  response.redirect("/echo")
end

 # redirect with a 301 permanent status
Tina4::Router.get("/demo/redirect-permanent") do |request, response|
  response.redirect("/echo", 301)
end
