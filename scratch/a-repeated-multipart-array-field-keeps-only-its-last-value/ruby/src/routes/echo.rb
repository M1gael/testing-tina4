Tina4::Router.post("/echo") { |request, response| response.json({ body: request.body }) }.no_auth
Tina4::Router.get("/q") { |request, response| response.json({ query: request.query }) }.no_auth
