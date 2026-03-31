# exercise solution a for greeting api with time of day
Tina4::Router.get("/api/greet") do |request, response|
  name = request.params["name"] || "Stranger"
  hour = Time.now.hour

  time_of_day = if hour >= 5 && hour < 12
                  "morning"
                elsif hour >= 12 && hour < 17
                  "afternoon"
                elsif hour >= 17 && hour < 21
                  "evening"
                else
                  "night"
                end

  response.json({
    greeting: "Welcome, #{name}!",
    time_of_day: time_of_day
  })
end
