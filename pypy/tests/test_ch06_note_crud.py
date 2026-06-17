# ch06 sections 3 + 4 — create_table + CRUD operations
# Exercises the documented ORM API (S3 create_table, S4 save/create/find_by_id/
# find/where/delete/count).
#
# ┌─ BEFORE RUNNING ANY ORM CHAPTER ─────────────────────────────────────────┐
# │ Ensure a database is connected, or every ORM call raises                  │
# │ "RuntimeError: No database bound".                                         │
# │   1. Start Postgres:  docker compose up -d   (from repo root)              │
# │   2. pypy/.env sets   TINA4_DATABASE_URL=postgresql://postgres:tina4test@  │
# │                       localhost:5432/tina4testingdb                        │
# │   3. pypy/conftest.py loads .env into os.environ before tests; the ORM     │
# │      binds lazily. Chapter tables (notes, …) are auto-created by           │
# │      create_table() at runtime — no manual schema needed.                  │
# └───────────────────────────────────────────────────────────────────────────┘
#
# Binding note [PY-06-01]: Ch06 (the book) shows no DB binding anywhere — no
# TINA4_DATABASE_URL, no Database(), no bind_database(). Binding is established
# only in Ch05, which Ch06 silently assumes with no callout. That gap is the
# finding; the box above is our harness's setup, not the book's.
from tina4_python.test import Test, assert_equal, assert_true, assert_not_none, assert_none
from src.orm.note import Note


class NoteCrudTest(Test):

    def set_up(self):
        # S3 — create the table from the model definition
        Note.create_table()

    # S4 — save (create)
    def test_save_creates_record(self):
        note = Note()
        note.title = "Shopping List"
        note.content = "Milk, eggs"
        note.category = "personal"
        note.pinned = False
        note.save()

        assert_not_none(note.id, "Note should have an ID after save")
        assert_true(note.id > 0, "Note ID should be positive")

    # S4 — create (build and save in one step)
    def test_create_one_step(self):
        note = Note.create({
            "title": "Quick Note",
            "content": "Created in one step",
            "category": "general"
        })
        assert_not_none(note.id, "create() should return a saved instance with an ID")

    # S4 — find_by_id
    def test_find_by_id(self):
        note = Note.create(title="Find Me", content="x", category="work")
        loaded = Note.find_by_id(note.id)
        assert_not_none(loaded, "find_by_id should return the record")
        assert_equal(loaded.title, "Find Me", "Title should match")

    # S4 — find by filter dict
    def test_find_by_filter(self):
        Note.create(title="Work A", category="work")
        work_notes = Note.find({"category": "work"})
        assert_true(len(work_notes) >= 1, "find() should return matching notes")

    # S4 — where with SQL
    def test_where_sql(self):
        Note.create(title="Work B", category="work")
        notes = Note.where("category = ?", ["work"])
        assert_true(len(notes) >= 1, "where() should return matching notes")

    # S4 — count
    def test_count(self):
        Note.create(title="Counted", category="misc")
        total = Note.count()
        assert_true(total >= 1, "count() should return a positive total")

    # S4 — delete
    def test_delete(self):
        note = Note.create(title="Delete Me", category="temp")
        note_id = note.id
        note.delete()
        gone = Note.find_by_id(note_id)
        assert_none(gone, "deleted note should not be loadable")
