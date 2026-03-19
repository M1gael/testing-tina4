# define route for the custom template
Tina4.get "/mywebsite" do |request, response|
  response.render("mywebsite.twig", { title: "My Tina4 Ruby Site" })
end