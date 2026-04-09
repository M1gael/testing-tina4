 # orm verification routes - ch06
Tina4::Router.get("/api/orm-test") do |request, response|
  begin
    # 1. Setup tables (workaround for buggy create_table)
    db = Tina4.database
    db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, tag TEXT, pinned INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, bio TEXT, created_at TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, author_id INTEGER, title TEXT, slug TEXT, content TEXT, status TEXT, created_at TEXT, updated_at TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")

    # 2. CRUD: Create
    note = Note.create({
      title: "ORM Test Note",
      content: "Testing the 3.10.x ORM",
      category: "testing"
    })

    # 3. Relationship: Create Author and Post
    author = Author.create({
      name: "John Doe",
      email: "john@example.com"
    })

    post = BlogPost.create({
      author_id: author.id,
      title: "First Post",
      slug: "first-post",
      status: "published"
    })

    # 4. Fetch with Eager Loading
    authors = Author.all(include: ["posts"])

    response.json({
      note: note.to_h,
      authors: authors.map { |a| a.to_h(include: ["posts"]) }
    })
  rescue => e
    response.json({ error: e.message, backtrace: e.backtrace.first(5) }, 500)
  end
end
