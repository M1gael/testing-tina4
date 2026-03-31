 # testing status code chaining - ch03 section 4

 # chained .status before .json, equivalent to passing status as second arg
Tina4::Router.post("/demo/status") do |request, response|
  response.status(201).json({ id: 7, created: true })
end
