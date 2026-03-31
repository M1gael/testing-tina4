# exercise solution b store route with product listing
Tina4::Router.get("/store") do |request, response|
  products = [
    { name: "Espresso Machine", category: "Kitchen", price: 299.99, featured: true },
    { name: "Yoga Mat", category: "Fitness", price: 29.99, featured: false },
    { name: "Standing Desk", category: "Office", price: 549.99, featured: true },
    { name: "Noise-Canceling Headphones", category: "Electronics", price: 199.99, featured: true },
    { name: "Water Bottle", category: "Fitness", price: 24.99, featured: false }
  ]

  featured_count = products.count { |p| p[:featured] }

  response.render("store.html", {
    products: products,
    featured_count: featured_count
  })
end
