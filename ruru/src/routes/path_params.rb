# testing path parameters
Tina4::Router.get("/users/{id}/posts/{post_id}") do |request, response|
  user_id = request.params[:id]
  post_id = request.params[:post_id]

  response.json({
    user_id: user_id,
    post_id: post_id
  })
end

Tina4::Router.get("/orders/{id:int}") do |request, response|
  id = request.params[:id]
  response.json({
    order_id: id,
    type: id.class.name
  })
end

Tina4::Router.get("/products_item/{id:int}") do |request, response|
  id = request.params[:id]
  response.json({
    product_id: id,
    type: id.class.name
  })
end

Tina4::Router.get("/products_item/{id:int}/price/{price:float}") do |request, response|
  id = request.params[:id]
  price = request.params[:price]
  response.json({
    product_id: id,
    price: price,
    type: price.class.name
  })
end

Tina4::Router.get("/files/{filepath:path}") do |request, response|
  filepath = request.params[:filepath]
  response.json({
    filepath: filepath,
    type: filepath.class.name
  })
end
