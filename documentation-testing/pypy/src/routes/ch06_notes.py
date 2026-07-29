# ch06 section 4 — "CRUD Operations" (route handlers)
# VERBATIM handler bodies from the chapter: save/create_note (276-285),
# find_by_id/get_note (314-321), delete/delete_note (361-370),
# list_notes (376-388). The per-snippet import lines shown across S4
# (`post, put` / `get` / `delete as delete_route`) are combined here.
from tina4_python.core.router import post, put, get
from tina4_python.core.router import delete as delete_route
from src.orm.note import Note


@post("/api/notes")
async def create_note(request, response):
    note = Note()
    note.title = request.body["title"]
    note.content = request.body.get("content", "")
    note.category = request.body.get("category", "general")
    note.pinned = request.body.get("pinned", False)
    note.save()

    return response({"message": "Note created", "note": note.to_dict()}, 201)


@get("/api/notes/{id:int}")
async def get_note(id, request, response):
    note = Note.find_by_id(id)

    if note is None:
        return response({"error": "Note not found"}, 404)

    return response(note.to_dict())


@delete_route("/api/notes/{id:int}")
async def delete_note(id, request, response):
    note = Note.find_by_id(id)

    if note is None:
        return response({"error": "Note not found"}, 404)

    note.delete()

    return response(None, 204)


@get("/api/notes")
async def list_notes(request, response):
    category = request.params.get("category")

    if category:
        notes = Note.where("category = ?", [category])
    else:
        notes = Note.all()

    return response({
        "notes": [note.to_dict() for note in notes],
        "count": len(notes)
    })
