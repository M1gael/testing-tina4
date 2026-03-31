# testing wildcard and catch-all
Tina4::Router.get("/docs/*") do |request, response|
  path = request.params["*"] || ""
  response.json({
    section: "docs",
    path: path
  })
end

Tina4::Router.get("/*") do |request, response|
  response.json({
    error: "Page not found",
    path: request.path
  }, 404)
end
