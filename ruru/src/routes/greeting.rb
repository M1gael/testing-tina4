# testing your first route and adding more http methods
Tina4::Router.get("/api/greeting/{name}") do |request, response|
  name = request.params["name"]
  response.json({
    message: "Hello, #{name}!",
    timestamp: Time.now.iso8601
  })
end

Tina4::Router.post("/api/greeting") do |request, response|
  name = request.body["name"] || "World"
  language = request.body["language"] || "en"

  greetings = {
    "en" => "Hello",
    "es" => "Hola",
    "fr" => "Bonjour",
    "de" => "Hallo",
    "ja" => "Konnichiwa"
  }

  greeting = greetings[language] || greetings["en"]

  response.json({
    message: "#{greeting}, #{name}!",
    language: language
  }, 201)
end
