Tina4::Router.get("/v-frond") do |request, response|
  response.render("v_frond.twig", { 
    myboolean: true,
    myarray: ["apple", "banana"], 
    mytext: "hello" 
  })
end
