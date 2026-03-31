 # testing file downloads via response.file - ch03 section 8

 # serve a report file from data/reports by filename path param
Tina4::Router.get("/api/reports/{filename}") do |request, response|
  filename = request.params["filename"]
  filepath = File.join(__dir__, "../../data/reports", filename)

  unless File.exist?(filepath)
    return response.json({ error: "Report not found" }, 404)
  end

  response.file(filepath)
end

 # serve with a forced download filename
Tina4::Router.get("/api/reports/{filename}/download") do |request, response|
  filename = request.params["filename"]
  filepath = File.join(__dir__, "../../data/reports", filename)

  unless File.exist?(filepath)
    return response.json({ error: "Report not found" }, 404)
  end

  response.file(filepath, "Q1-2026-Sales-Report.pdf")
end
