require "tina4"

Tina4.get "/where" do |request, response|
  response.call(Tina4::Session.instance_method(:save).source_location.first, Tina4::HTTP_OK)
end
Tina4.get "/plain" do |request, response|   # never touches the session
  response.call("plain", Tina4::HTTP_OK)
end
Tina4.get "/read" do |request, response|
  response.call("user=#{request.session.get('user') || '-'}", Tina4::HTTP_OK)
end
Tina4.get "/write" do |request, response|
  request.session.set("user", "alice")
  response.call("wrote", Tina4::HTTP_OK)
end
Tina4.get "/login" do |request, response|   # regenerate, then set
  request.session.regenerate
  request.session.set("user", "alice")
  response.call("logged in", Tina4::HTTP_OK)
end
Tina4.get "/flash-set" do |request, response|
  request.session.flash("notice", "saved")
  response.call("flashed", Tina4::HTTP_OK)
end
Tina4.get "/flash-get" do |request, response|
  response.call("flash=#{request.session.get_flash('notice') || '-'}", Tina4::HTTP_OK)
end

Tina4.run!(__dir__, port: Integer(ENV.fetch("PORT")), host: "127.0.0.1", no_browser: true)
