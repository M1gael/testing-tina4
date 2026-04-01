
 # testing template rendering and variables - ch04 section 2

Tina4::Router.get("/welcome") do |request, response|
  response.render("welcome.html", { name: "Alice" })
end

Tina4::Router.get("/profile") do |request, response|
  data = {
    user: {
      name: "Alice",
      email: "alice@example.com",
      address: {
        city: "Cape Town",
        country: "South Africa"
      }
    }
  }
  response.render("profile.html", data)
end

Tina4::Router.get("/expressions") do |request, response|
  response.render("expressions.html", { 
    price: 100, 
    quantity: 5, 
    first_name: "John", 
    last_name: "Doe" 
  })
end

Tina4::Router.get("/about") do |request, response|
  response.render("about.twig", {
    founded_year: 2020,
    team_size: 12,
    office_count: 3
  })
end

Tina4::Router.get("/products/list") do |request, response|
  products = [
    { name: "Screwdriver", price: 15.99, in_stock: true, featured: true },
    { name: "Hammer", price: 29.99, in_stock: true, featured: false },
    { name: "Drill", price: 89.99, in_stock: false, featured: true }
  ]
  response.render("product_list.twig", { products: products })
end

Tina4::Router.get("/v6_demo") do |request, response|
  products = [
    { name: "Screwdriver", price: 15.99, in_stock: true, featured: true },
    { name: "Hammer", price: 29.99, in_stock: true, featured: false },
    { name: "Drill", price: 89.99, in_stock: false, featured: true }
  ]
  response.render("v6_demo.twig", { 
    products: products, 
    user_role: "editor",
    user_name: "Alice" 
  })
end

Tina4::Router.get("/v7_filters") do |request, response|
  metadata = {
    "version" => "1.0.0",
    "status" => "active"
  }
  response.render("v7_filters.twig", { 
    metadata: metadata
  })
end

Tina4::Router.get("/macros") do |request, response|
  response.render("test_macros.twig")
end
