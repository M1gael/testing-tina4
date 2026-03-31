# testing chapter 5 database integration (partially untestable via http due to sqlite lock bugs)
from tina4_python.core.router import get, post, put, delete
from tina4_python.database.connection import Database


@get("/api/notes")
async def list_notes(request, response):
    db = Database()
    category = request.params.get("category")
    pinned = request.params.get("pinned")

    sql = "SELECT * FROM notes"
    params = []
    conditions = []

    if category:
        conditions.append("category = ?")
        params.append(category)

    if pinned == "true":
        conditions.append("pinned = 1")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY pinned DESC, created_at DESC"

    notes = db.fetch(sql, params)

    return response.json({"notes": notes, "count": len(notes)})


@get("/api/notes/categories")
async def list_categories(request, response):
    db = Database()
    categories = db.fetch(
        "SELECT category, COUNT(*) as count FROM notes GROUP BY category ORDER BY count DESC"
    )
    return response.json({"categories": categories})


@get("/api/notes/{id:int}")
async def get_note(request, response):
    db = Database()
    note = db.fetch_one(
        "SELECT * FROM notes WHERE id = ?",
        [request.params["id"]]
    )

    if note is None:
        return response.json({"error": "Note not found"}, 404)

    return response.json(note)


@post("/api/notes")
async def create_note(request, response):
    db = Database()
    body = request.body

    if not body.get("title"):
        return response.json({"error": "Title is required"}, 400)

    result = db.execute(
        "INSERT INTO notes (title, content, category, pinned) VALUES (?, ?, ?, ?)",
        [body["title"], body.get("content", ""), body.get("category", "general"), 1 if body.get("pinned") else 0]
    )

    note = db.fetch_one("SELECT * FROM notes WHERE id = ?", [result.last_id])
    db.cache_clear()

    return response.json({"message": "Note created", "note": note}, 201)


@put("/api/notes/{id:int}")
async def update_note(request, response):
    db = Database()
    note_id = request.params["id"]
    body = request.body

    existing = db.fetch_one("SELECT * FROM notes WHERE id = ?", [note_id])
    if existing is None:
        return response.json({"error": "Note not found"}, 404)

    db.execute(
        """UPDATE notes
           SET title = ?, content = ?, category = ?,
               pinned = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        [
            body.get("title", existing["title"]),
            body.get("content", existing["content"]),
            body.get("category", existing["category"]),
            1 if body.get("pinned", existing["pinned"]) else 0,
            note_id
        ]
    )

    updated = db.fetch_one("SELECT * FROM notes WHERE id = ?", [note_id])
    db.cache_clear()

    return response.json({"message": "Note updated", "note": updated})


@delete("/api/notes/{id:int}")
async def delete_note(request, response):
    db = Database()
    note_id = request.params["id"]

    existing = db.fetch_one("SELECT * FROM notes WHERE id = ?", [note_id])
    if existing is None:
        return response.json({"error": "Note not found"}, 404)

    db.execute("DELETE FROM notes WHERE id = ?", [note_id])
    db.cache_clear()

    return response.json(None, 204)
