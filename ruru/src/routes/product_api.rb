# testing full crud application exercise
# In-memory product store (resets on server restart)
$products_api = [
  { id: 1, name: "Wireless Keyboard", category: "Electronics", price: 79.99, in_stock: true },
  { id: 2, name: "Yoga Mat", category: "Fitness", price: 29.99, in_stock: true },
  { id: 3, name: "Coffee Grinder", category: "Kitchen", price: 49.99, in_stock: false },
  { id: 4, name: "Standing Desk", category: "Office", price: 549.99, in_stock: true },
  { id: 5, name: "Running Shoes", category: "Fitness", price: 119.99, in_stock: true }
]

$next_id_api = 6

# List all products, optionally filter by category
Tina4::Router.get("/api/product_api") do |request, response|
  category = request.params["category"]

  if category
    filtered = $products_api.select { |p| p[:category].downcase == category.downcase }
    response.json({ products: filtered, count: filtered.length })
  else
    response.json({ products: $products_api, count: $products_api.length })
  end
end

# Get a single product by ID
Tina4::Router.get("/api/product_api/{id:int}") do |request, response|
  id = request.params[:id]

  product = $products_api.find { |p| p[:id] == id }

  if product
    response.json(product)
  else
    response.json({ error: "Product not found", id: id }, 404)
  end
end

# Create a new product
Tina4::Router.post("/api/product_api") do |request, response|
  body = request.body

  if body["name"].nil? || body["name"].empty?
    return response.json({ error: "Name is required" }, 400)
  end

  product = {
    id: $next_id_api,
    name: body["name"],
    category: body["category"] || "Uncategorized",
    price: (body["price"] || 0).to_f,
    in_stock: body["in_stock"] != false
  }

  $next_id_api += 1
  $products_api << product

  response.json(product, 201)
end

# Replace a product
Tina4::Router.put("/api/product_api/{id:int}") do |request, response|
  id = request.params[:id]
  body = request.body

  index = $products_api.index { |p| p[:id] == id }

  if index.nil?
    response.json({ error: "Product not found", id: id }, 404)
  else
    $products_api[index] = {
      id: id,
      name: body["name"] || $products_api[index][:name],
      category: body["category"] || $products_api[index][:category],
      price: (body["price"] || $products_api[index][:price]).to_f,
      in_stock: body.key?("in_stock") ? body["in_stock"] : $products_api[index][:in_stock]
    }
    response.json($products_api[index])
  end
end

# Delete a product
Tina4::Router.delete("/api/product_api/{id:int}") do |request, response|
  id = request.params[:id]

  index = $products_api.index { |p| p[:id] == id }

  if index.nil?
    response.json({ error: "Product not found", id: id }, 404)
  else
    $products_api.delete_at(index)
    response.json(nil, 204)
  end
end
