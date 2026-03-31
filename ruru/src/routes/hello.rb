# testing simple route
Tina4::Router.get("/hello") do |request, response|
  response.json({ message: "Hello, World!" })
end
