# ch06 section 9 — "Auto-CRUD" / Manual Registration + custom prefix.
# VERBATIM snippets (06-orm.md:867-873, 888-890). Registers Note's auto-CRUD
# routes under /api/v2 — an unshadowed path (the custom /api/notes routes in
# ch06_notes.py take precedence on the default prefix, per S9).
from tina4_python.crud import AutoCrud
from src.orm.note import Note

AutoCrud.register(Note, prefix="/api/v2")
# Routes: /api/v2/notes, /api/v2/notes/{id}, etc.
