 # database check route
Tina4::Router.get("/api/check-users") do |request, response|
  db = Tina4.database
  begin
    tables = db.tables
    columns = db.columns("users") rescue "N/A"
    migrations = db.fetch("SELECT * FROM tina4_migration") rescue "N/A"
    response.json({
      tables: tables,
      users_columns: columns,
      migrations: migrations
    })
  rescue => e
    response.json({ error: e.message }, 500)
  end
end
