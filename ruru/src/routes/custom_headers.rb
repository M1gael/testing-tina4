 # testing custom headers and cors headers - ch03 section 5

 # chained custom headers before the json response
Tina4::Router.get("/api/data") do |request, response|
  response
    .header("X-Request-Id", SecureRandom.hex(8))
    .header("X-Rate-Limit-Remaining", "57")
    .header("Cache-Control", "no-cache")
    .json({ data: [1, 2, 3] })
end

 # manual cors header override
Tina4::Router.get("/demo/cors") do |request, response|
  response
    .header("Access-Control-Allow-Origin", "https://myapp.com")
    .header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
    .header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    .json({ data: "value" })
end
