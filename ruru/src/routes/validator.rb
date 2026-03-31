 # testing the Tina4::Validator class - ch03 section 10

Tina4::Router.post("/api/users") do |request, response|
  v = Tina4::Validator.new(request.body)
  v.required("name").required("email").email("email").min_length("name", 2)

  unless v.valid?
    return response.error("VALIDATION_FAILED", v.errors.first[:message], 400)
  end

  response.json({ message: "User created", name: request.body["name"] }, 201)
end
