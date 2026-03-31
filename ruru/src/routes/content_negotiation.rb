 # testing content negotiation via accept header - ch03 section 9

Tina4::Router.get("/api/products/{id:int}") do |request, response|
  id = request.params["id"]
  product = {
    id: id,
    name: "Wireless Keyboard",
    price: 79.99
  }

  accept = request.headers["Accept"] || "application/json"

  if accept.include?("text/html")
    response.render("product-detail.html", { product: product })
  elsif accept.include?("text/plain")
    text = "Product ##{id}: #{product[:name]} - $#{product[:price]}"
    response.text(text)
  else
    response.json(product)
  end
end
