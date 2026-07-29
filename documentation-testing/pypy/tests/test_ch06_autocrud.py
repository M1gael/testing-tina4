# Verbatim-impl test — Chapter 6 ORM, S9 "Auto-CRUD".
#   - Task has `auto_crud = True` (src/orm/task.py) -> generated /api/tasks routes.
#   - Note is registered under /api/v2 via AutoCrud.register (src/routes/ch06_autocrud.py).
# Drives the generated routes through the documented Test client + introspection.
# (The documented "custom routes take precedence over auto-CRUD" claim is FALSE
# on 3.13.30 — auto-CRUD shadows custom; logged as PY-06-18, evidence captured
# under `tina4 serve`. Not re-asserted here, since a persistent sentinel would
# require permanently shadowing the S4/S6 custom /api/notes routes.)
import json
import os

import psycopg2
import pytest

from tina4_python.test import Test, assert_equal, assert_true
from tina4_python.crud import AutoCrud

from src.orm.task import Task
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
    _drop("tasks", "notes")
    Task.create_table()
    Note.create_table()
    yield


@pytest.fixture(autouse=True)
def _clean():
    for t in Task.with_trashed():
        t.force_delete()
    for n in Note.all():
        n.delete()
    yield


# AutoCrud.models() introspection (06-orm.md:949-952) — Task registered via flag
def test_autocrud_models_introspection():
    assert "tasks" in AutoCrud.models()


class AutoCrudTaskTest(Test):

    # GET /api/tasks — paginated payload (06-orm.md:909-923)
    def test_list_paginated_shape(self):
        resp = self.get("/api/tasks")
        assert_equal(resp.status, 200, "auto-crud list should 200")
        body = json.loads(resp.body)
        assert_true("data" in body, "paginated payload has 'data'")
        assert_true("total" in body, "paginated payload has 'total'")

    # GET /api/tasks — payload reflects actual rows (06-orm.md:909-923), not just key-presence
    def test_list_reflects_rows(self):
        self.post("/api/tasks", json={"title": "L1"})
        self.post("/api/tasks", json={"title": "L2"})
        body = json.loads(self.get("/api/tasks").body)
        assert_equal(body["total"], 2, "total reflects row count")
        assert_equal(len(body["data"]), 2, "data carries the rows")

    # POST /api/tasks — create (06-orm.md:925-931)
    def test_create(self):
        resp = self.post("/api/tasks", json={"title": "Auto Task"})
        assert_equal(resp.status, 201, "auto-crud create should 201")
        assert_equal(len(Task.all()), 1, "create persisted a row")

    # GET /api/tasks/{id} — get one by PK (documented route table 06-orm.md:878-884)
    def test_get_one_by_id(self):
        self.post("/api/tasks", json={"title": "Fetch Me"})
        t = Task.all()[0]
        resp = self.get(f"/api/tasks/{t.id}")
        assert_equal(resp.status, 200, "auto-crud get-one should 200")
        assert_true("Fetch Me" in json.dumps(json.loads(resp.body)),
                    "get-one returns the record")

    # PUT /api/tasks/{id} — update (documented route table 06-orm.md:878-884)
    def test_update_by_id(self):
        self.post("/api/tasks", json={"title": "Before"})
        t = Task.all()[0]
        resp = self.put(f"/api/tasks/{t.id}", json={"title": "After"})
        assert_true(resp.status in (200, 201), "auto-crud update should 200/201")
        assert_equal(Task.find_by_id(t.id).title, "After", "update persisted")

    # POST validation failure -> 400 (06-orm.md:933-937)
    def test_create_validation_400(self):
        resp = self.post("/api/tasks", json={})
        assert_equal(resp.status, 400, "missing required title should 400")

    # DELETE respects soft delete (06-orm.md:939) — Task has soft_delete=True
    def test_delete_respects_soft_delete(self):
        self.post("/api/tasks", json={"title": "to-delete"})
        t = Task.all()[0]
        resp = self.delete(f"/api/tasks/{t.id}")
        assert_true(resp.status in (200, 204), "auto-crud delete should 200/204")
        assert_equal(Task.find_by_id(t.id), None, "soft-deleted -> hidden from queries")
        assert_equal(len(Task.with_trashed()), 1, "row remains in DB (soft)")


class AutoCrudRegisterPrefixTest(Test):

    # AutoCrud.register(Note, prefix="/api/v2") (06-orm.md:888-890)
    def test_v2_list_paginated(self):
        resp = self.get("/api/v2/notes")
        assert_equal(resp.status, 200, "registered-prefix list should 200")
        assert_true("data" in json.loads(resp.body), "paginated payload")

    def test_v2_create(self):
        resp = self.post("/api/v2/notes", json={"title": "V2 Note"})
        assert_equal(resp.status, 201, "registered-prefix create should 201")
