
 # debug frond template engine - isolating bugs found in Ch04

Tina4::Router.get("/frond-debug") do |request, response|
  response.render("frond_debug.twig", {
    items: [1, 2, 3],
    name: "Alice"
  })
end
