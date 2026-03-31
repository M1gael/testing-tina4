# testing query parameters
Tina4::Router.get("/search") do |request, response|
  q = request.params["q"] || ""
  page = (request.params["page"] || 1).to_i
  limit = (request.params["limit"] || 10).to_i

  response.json({
    query: q,
    page: page,
    limit: limit,
    offset: (page - 1) * limit
  })
end
