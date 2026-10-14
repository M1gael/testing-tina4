# Stock tina4-ruby v3: AutoCrud + Crud.to_crud over a 3-row sqlite table.
$LOAD_PATH.unshift(File.join(ENV.fetch("TINA4_RB_TREE"), "lib"))
require "tina4"
Tina4.initialize!(__dir__)

db_path = File.join(__dir__, "people.db")
File.delete(db_path) if File.exist?(db_path)
db = Tina4::Database.new("sqlite:///#{db_path}")
Tina4.bind_database(db)
db.execute("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)")
[["Ann", 30], ["O'Brien", 40], ["Zed", 25]].each { |n, a| db.execute("INSERT INTO people (name, age) VALUES (?, ?)", [n, a]) }
db.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY, token TEXT)")
db.execute("INSERT INTO secrets (id, token) VALUES (1, 'TOPSECRET')")
db.commit rescue nil

class Person < Tina4::ORM
  table_name "people"
  integer_field :id, primary_key: true, auto_increment: true
  string_field :name
  integer_field :age
end

Tina4::AutoCrud.register(Person, public: true)
Tina4::AutoCrud.generate_routes(prefix: "/api")

Tina4.get("/grid", auth: false) { |req, res| res.html(Tina4::Crud.to_crud(req, { model: Person })) }
Tina4.get("/gridsql", auth: false) { |req, res| res.html(Tina4::Crud.to_crud(req, { model: Person, sql: "SELECT id, name, age FROM people" })) }

app = Tina4::RackApp.new(root_dir: __dir__)
Tina4::WebServer.new(app, host: "127.0.0.1", port: (ENV["PORT"] || 7463).to_i).start
