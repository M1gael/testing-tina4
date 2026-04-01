
 # database testing raw queries and schema inspection - ch05

Tina4::Router.get("/api/test-db") do |request, response|
  db = Tina4.database
  begin
    result = db.fetch("SELECT 1 + 1 AS answer")
    response.json(result)
  rescue => e
    response.json({ error: e.message }, 500)
  end
end

Tina4::Router.get("/api/schema") do |request, response|
  db = Tina4.database
  begin
    tables = db.tables
    schema = {}
    tables.each do |table|
      schema[table] = db.columns(table)
    end
    response.json({ tables: schema })
  rescue => e
    response.json({ error: e.message }, 500)
  end
end

Tina4::Router.get("/api/test-paginate") do |request, response|
  db = Tina4.database
  begin
    result = db.fetch("SELECT * FROM notes")
    response.json(result.to_paginate)
  rescue => e
    response.json({ error: e.message }, 500)
  end
end

Tina4::Router.get("/api/test-column-info") do |request, response|
  db = Tina4.database
  begin
    result = db.fetch("SELECT * FROM notes")
    response.json(result.column_info)
  rescue => e
    response.json({ error: e.message }, 500)
  end
end

Tina4::Router.get("/api/test-seed") do |request, response|
  begin
    require "tina4/seeder"
    Tina4.seed(seed_folder: "seeds")
    response.json({ status: "success" })
  rescue => e
    response.json({ error: e.message }, 500)
  end
end
 Tina4::Router.get("/api/test-fake") do |request, response|
  begin
    fake = Tina4::FakeData.new
    response.json({
      name: fake.name,
      email: fake.email
    })
  rescue => e
    response.json({ error: e.message }, 500)
  end
end
