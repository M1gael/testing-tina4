 # testing basic request object properties - ch03 section 1 and section 2

 # section 1: basic echo of method, path and ip
Tina4::Router.get("/echo") do |request, response|
  response.json({
    method: request.method,
    path: request.path,
    your_ip: request.ip
  })
end

 # section 2: full request debug dump (method, path, params, body, headers, ip, cookies)
Tina4::Router.post("/debug/request") do |request, response|
  response.json({
    method: request.method,
    path: request.path,
    params: request.params,
    query: request.params,
    body: request.body,
    headers: request.headers,
    ip: request.ip,
    cookies: request.cookies
  })
end
