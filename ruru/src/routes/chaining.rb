# testing route chaining
Tina4::Router.get("/api/account") do |request, response|
  response.json({ account: request.user })
end.secure

Tina4::Router.get("/api/catalog") do |request, response|
  # Expensive database query
  response.json({ products: [] })
end.cache

Tina4::Router.get("/api/data_chained") do |request, response|
  response.json({ data: "cached secure data" })
end.secure.cache
