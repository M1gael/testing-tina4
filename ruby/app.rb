require "tina4"

Tina4.get "/" do |request, response|
  response.html "<h1>Welcome to ruby!</h1><p>Powered by Tina4 Ruby</p>"
end

Tina4.get "/api/hello" do |request, response|
  response.json({ message: "Hello from Tina4!", timestamp: Time.now.iso8601 })
end
