# testing http methods
Tina4::Router.get("/products_crud") do |request, response|
  response.json({ action: "list all products" })
end

Tina4::Router.post("/products_crud") do |request, response|
  response.json({ action: "create a product" }, 201)
end

Tina4::Router.put("/products_crud/{id}") do |request, response|
  id = request.params[:id]
  response.json({ action: "replace product #{id}" })
end

Tina4::Router.patch("/products_crud/{id}") do |request, response|
  id = request.params[:id]
  response.json({ action: "update product #{id}" })
end

Tina4::Router.delete("/products_crud/{id}") do |request, response|
  id = request.params[:id]
  response.json({ action: "delete product #{id}" })
end
