# Verbatim-impl test — Chapter 6 ORM, S2 (model) / S3 (create_table) /
# S4 (CRUD) / S5 (serialisation), Note model. Exercises the documented
# model API exactly as the chapter shows, as a reader implementing it would.
# DB bound by conftest (.env -> tina4testingdb).
import json
import os

import psycopg2
import pytest

from src.orm.note import Note


def _drop(*tables):
    conn = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    for t in tables:
        cur.execute(f'DROP TABLE IF EXISTS {t} CASCADE')
    cur.close()
    conn.close()


@pytest.fixture(autouse=True, scope="module")
def _schema():
    _drop("notes")
    Note.create_table()        # S3 — schema from the model
    yield
    # No teardown drop — leave tables + rows visible after the run. Re-runs stay
    # idempotent via the setup _drop above + per-test row cleanup.


@pytest.fixture(autouse=True)
def _clean():
    for n in Note.all():
        n.delete()
    yield


# --- S4 save -- Create or Update ---
def test_save_insert_sets_pk():
    note = Note()
    note.title = "Shopping List"
    note.content = "Milk, eggs"
    note.category = "personal"
    note.pinned = False
    result = note.save()
    assert result is note  # doc (06-orm.md:288): save() returns self on success
    assert note.id is not None


def test_save_update():
    note = Note.create(title="Original")
    note.title = "Updated"
    note.save()
    again = Note.find_by_id(note.id)
    assert again.title == "Updated"


# --- S4 create -- dict and kwargs ---
def test_create_dict():
    note = Note.create({
        "title": "Quick Note",
        "content": "Created in one step",
        "category": "general",
    })
    assert note.id is not None
    assert (note.title, note.content, note.category) == \
        ("Quick Note", "Created in one step", "general")  # values round-trip


def test_create_kwargs():
    note = Note.create(title="Quick Note", content="One step", category="general")
    assert note.id is not None
    assert (note.title, note.content, note.category) == \
        ("Quick Note", "One step", "general")


# --- S4 find_by_id ---
def test_find_by_id_hit():
    n = Note.create(title="A")
    got = Note.find_by_id(n.id)
    assert got is not None
    assert got.title == "A"


def test_find_by_id_miss_returns_none():
    assert Note.find_by_id(999999) is None


# --- S4 find_or_fail ---
def test_find_or_fail_hit():
    n = Note.create(title="X")
    assert Note.find_or_fail(n.id).id == n.id


def test_find_or_fail_miss_raises():
    with pytest.raises(ValueError):
        Note.find_or_fail(999999)


# --- S4 find -- query by filter dict ---
def test_find_filter_dict():
    Note.create(title="w1", category="work")
    Note.create(title="p1", category="personal")
    work = Note.find({"category": "work"})
    assert len(work) == 1
    assert work[0].category == "work"


def test_find_pagination_and_order():
    # explicit out-of-order created_at so DESC ordering is actually provable —
    # a len-only check would pass even if order_by were silently ignored.
    for i, ts in enumerate(["2026-01-01 00:00:00",
                            "2026-01-03 00:00:00",
                            "2026-01-02 00:00:00"]):
        Note.create(title=f"t{i}", pinned=True, created_at=ts)
    recent = Note.find({"pinned": True}, limit=10, order_by="created_at DESC")
    assert len(recent) == 3
    stamps = [str(n.created_at) for n in recent]
    assert stamps == sorted(stamps, reverse=True)        # genuinely DESC
    assert stamps[0].startswith("2026-01-03")            # newest first
    assert stamps[-1].startswith("2026-01-01")           # oldest last


def test_find_no_filter_returns_all():
    Note.create(title="a")
    Note.create(title="b")
    assert len(Note.find()) == 2


# --- S4 where ---
def test_where_basic():
    Note.create(title="w", category="work")
    notes = Note.where("category = ?", ["work"])
    assert len(notes) == 1


def test_where_pagination():
    for i in range(5):
        Note.create(title=f"w{i}", category="work")
    notes = Note.where("category = ?", ["work"], limit=20, offset=0)
    assert len(notes) == 5


# --- S4 all + pagination ---
def test_all_pagination():
    for i in range(3):
        Note.create(title=f"a{i}")
    assert len(Note.all(limit=20, offset=0)) == 3


# --- S4 select -- SQL-first ---
def test_select_sql_first_verbatim_known_broken_on_pg():
    # Verbatim chapter line (06-orm.md:401-404) passes [1] for the boolean
    # `pinned` column. On the bound PostgreSQL, BooleanField is a real BOOLEAN,
    # so `pinned = 1` raises `operator does not exist: boolean = integer`
    # (known PG boolean hazard). Recorded verbatim.
    Note.create(title="s", pinned=True)
    with pytest.raises(Exception):
        Note.select(
            "SELECT * FROM notes WHERE pinned = ? ORDER BY created_at DESC",
            [1], limit=20, offset=0,
        )


def test_select_sql_first_boolean_param_works():
    # Same method, passing a real boolean — confirms select() itself works.
    Note.create(title="s2", pinned=True)
    notes = Note.select(
        "SELECT * FROM notes WHERE pinned = ? ORDER BY created_at DESC",
        [True], limit=20, offset=0,
    )
    assert len(notes) >= 1


# --- S4 select_one ---
def test_select_one_works():
    Note.create(title="One", category="solo")
    note = Note.select_one("SELECT * FROM notes WHERE category = ?", ["solo"])
    assert note is not None
    assert note.title == "One"


def test_select_one_slug_verbatim_known_broken():
    # Verbatim chapter line (06-orm.md:412). Note has no `slug` column
    # (PY-06-04, known) -> raises on the bound DB.
    with pytest.raises(Exception):
        Note.select_one("SELECT * FROM notes WHERE slug = ?", ["my-note"])


# --- S4 load ---
def test_load_by_pk():
    n = Note.create(title="L")
    note = Note()
    note.id = n.id
    assert note.load() is True
    assert note.title == "L"


def test_load_slug_verbatim_known_broken():
    # Verbatim chapter line (06-orm.md:428). `slug` column does not exist
    # (PY-06-04, known).
    note = Note()
    with pytest.raises(Exception):
        note.load("slug = ?", ["my-note"])


# --- S4 count ---
def test_count():
    Note.create(title="a")
    Note.create(title="b", category="work")
    assert Note.count() == 2
    assert Note.count("category = ?", ["work"]) == 1


# --- S4 delete ---
def test_delete():
    n = Note.create(title="d")
    n.delete()
    assert Note.find_by_id(n.id) is None


# --- S5 serialisation ---
def test_to_dict():
    n = Note.create(title="Shopping List", content="Milk, eggs", category="personal")
    d = n.to_dict()
    assert d["title"] == "Shopping List"
    assert "id" in d


def test_to_json():
    n = Note.create(title="J")
    s = n.to_json()
    assert isinstance(s, str)
    assert json.loads(s)["title"] == "J"


def test_to_assoc_and_to_object_alias_to_dict():
    n = Note.create(title="Z")
    assert n.to_assoc() == n.to_dict()
    assert n.to_object() == n.to_dict()


def test_to_array_and_to_list():
    n = Note.create(title="Arr")
    arr = n.to_array()
    assert isinstance(arr, list)
    assert n.to_list() == arr
