require "tina4"
REPORT = ENV.fetch("REPORT")
Tina4::Router.get("/ping") { |req, res| res.json({ pong: true }) }
# ch03 ruby doc, verbatim call shape: response.file(path, "custom-name.pdf")
Tina4::Router.get("/doc") { |request, response| response.file(REPORT, "monthly-report-march-2026.pdf") }
# control: the real signature (keyword args)
Tina4::Router.get("/ok") { |request, response| response.file(REPORT, download: true) }
Tina4.run!(port: ENV.fetch("PORT").to_i, no_browser: true)
