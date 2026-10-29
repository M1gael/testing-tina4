require "tina4"
Tina4::Router.get("/ping") { |req, res| res.json({ pong: true }) }
# a logged-in browser: identity token held in the session, no Bearer
Tina4::Router.get("/login") { |req, res| req.session.set("token", Tina4::Auth.get_token({ "user_id" => 1 })); res.json({ logged_in: true }) }
Tina4::Router.get("/profile") { |req, res| res.render("profile.twig", {}) }
Tina4::Router.post("/api/profile") { |req, res| res.json({ saved: true }) } # default write route: auth required
Tina4::Router.post("/api/open") { |req, res| res.json({ saved: true }) }.no_auth # ch10 exercise shape
Tina4.run!(port: ENV.fetch("PORT").to_i, no_browser: true)
