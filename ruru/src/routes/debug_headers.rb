 # testing header access in GET - ch03 debug

Tina4::Router.get("/debug/headers") do |request, response|
  response.json({
    accept: request.headers["Accept"],
    all_headers: request.headers
  })
end
