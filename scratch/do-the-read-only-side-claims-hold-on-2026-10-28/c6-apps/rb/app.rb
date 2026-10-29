require "tina4"
Tina4::Router.get("/ping") { |req, res| res.json({ pong: true }) }
Tina4::Router.get("/login") { |req, res| req.session.set("token", Tina4::Auth.get_token({ "user_id" => 1 })); res.json({ logged_in: true }) }
Tina4::Router.post("/api/save") { |req, res| res.json({ saved: true }) }
Tina4::Router.post("/api/open") { |req, res| res.json({ saved: true }) }.no_auth
Tina4.run!(port: ENV.fetch("PORT").to_i, no_browser: true)
