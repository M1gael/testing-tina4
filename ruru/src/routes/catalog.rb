
 # exercise solution: product catalog template - ch04 sections 11-12

Tina4::Router.get("/catalog") do |request, response|
  all_products = [
    { name: "Espresso Machine", category: "Kitchen", price: 299.99, in_stock: true, featured: true },
    { name: "Yoga Mat", category: "Fitness", price: 29.99, in_stock: true, featured: false },
    { name: "Standing Desk", category: "Office", price: 549.99, in_stock: true, featured: true },
    { name: "Blender", category: "Kitchen", price: 89.99, in_stock: false, featured: false },
    { name: "Running Shoes", category: "Fitness", price: 119.99, in_stock: true, featured: false },
    { name: "Desk Lamp", category: "Office", price: 39.99, in_stock: true, featured: true },
    { name: "Cast Iron Skillet", category: "Kitchen", price: 44.99, in_stock: true, featured: false }
  ]

  # get unique categories
  categories = all_products.map { |p| p[:category] }.uniq.sort

  # filter by category if specified
  active_category = request.params["category"] || ""
  products = if active_category.empty?
               all_products
             else
               all_products.select { |p| p[:category].downcase == active_category.downcase }
             end

  response.render("catalog.twig", {
    products: products,
    categories: categories,
    active_category: active_category
  })
end
