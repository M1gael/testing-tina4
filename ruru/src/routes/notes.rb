
 # notes crud api - ch05 exercise

# List all notes with optional filters
Tina4::Router.get("/api/notes") do |request, response|
  db = Tina4.database
  begin
    tag = request.params["tag"] || ""
    search = request.params["search"] || ""

    sql = "SELECT * FROM notes"
    params = []
    conditions = []

    unless tag.empty?
      conditions << "tag = ?"
      params << tag
    end

    unless search.empty?
      conditions << "(title LIKE ? OR content LIKE ?)"
      params << "%#{search}%"
      params << "%#{search}%"
    end

    sql += " WHERE #{conditions.join(' AND ')}" unless conditions.empty?
    sql += " ORDER BY updated_at DESC"

    notes = db.fetch(sql, params)

    response.json({
      notes: notes,
      count: notes.length
    })
  rescue => e
    response.json({ error: e.message }, 500)
  end
end

# Get a single note
Tina4::Router.get("/api/notes/{id:int}") do |request, response|
  db = Tina4.database
  begin
    id = request.params["id"]
    note = db.fetch_one("SELECT * FROM notes WHERE id = ?", [id])

    if note.nil?
      response.json({ error: "Note not found", id: id }, 404)
    else
      response.json(note)
    end
  rescue => e
    response.json({ error: e.message }, 500)
  end
end

# Create a note
Tina4::Router.post("/api/notes") do |request, response|
  db = Tina4.database
  begin
    body = request.body_parsed
    # validate
    errors = []
    errors << "Title is required" if body["title"].nil? || body["title"].empty?
    errors << "Content is required" if body["content"].nil? || body["content"].empty?

    unless errors.empty?
      next response.json({ errors: errors }, 400)
    end

    db.execute(
      "INSERT INTO notes (title, content, tag) VALUES (?, ?, ?)",
      [body["title"], body["content"], body["tag"] || "general"]
    )

    note = db.fetch_one("SELECT * FROM notes WHERE id = last_insert_rowid()")
    response.json(note, 201)
  rescue => e
    response.json({ error: e.message }, 500)
  end
end.no_auth

# Update a note
Tina4::Router.put("/api/notes/{id:int}") do |request, response|
  db = Tina4.database
  begin
    id = request.params["id"]
    body = request.body_parsed

    existing = db.fetch_one("SELECT * FROM notes WHERE id = ?", [id])
    if existing.nil?
      next response.json({ error: "Note not found", id: id }, 404)
    end

    db.execute(
      "UPDATE notes SET title = ?, content = ?, tag = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
      [
        body["title"] || existing["title"],
        body["content"] || existing["content"],
        body["tag"] || existing["tag"],
        id
      ]
    )

    note = db.fetch_one("SELECT * FROM notes WHERE id = ?", [id])
    response.json(note)
  rescue => e
    response.json({ error: e.message }, 500)
  end
end.no_auth

# Delete a note
Tina4::Router.delete("/api/notes/{id:int}") do |request, response|
  db = Tina4.database
  begin
    id = request.params["id"]
    existing = db.fetch_one("SELECT * FROM notes WHERE id = ?", [id])

    if existing.nil?
      next response.json({ error: "Note not found", id: id }, 404)
    end

    db.execute("DELETE FROM notes WHERE id = ?", [id])
    response.json(nil, 204)
  rescue => e
    response.json({ error: e.message }, 500)
  end
end.no_auth
