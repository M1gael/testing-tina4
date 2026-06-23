# Verbatim-impl test — Chapter 6 route handlers driven through the documented
# tina4_python.test client (the Ch18 route-testing approach). Turns the one-off
# `tina4 serve` + curl checks into persistent sentinels.
#
# Sentinels:
#   PY-06-06 — path-param handlers (get_note/get_author/get_post) raise TypeError
#              when driven by the Test client (flat handler(request, response) call).
#   PY-06-07 — write routes (create_note POST) are Bearer-gated by default -> 401
#              over `tina4 serve` (real HTTP).
#   PY-06-13 — the Test client does NOT enforce that gate: the same POST returns
#              201 here. Serve-vs-client auth-dispatch divergence.
import json
import os

import psycopg2
import pytest

from tina4_python.test import Test, assert_equal, assert_true

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
    Note.create_table()
    yield
    # No teardown drop — leave rows visible (see other ch06 tests).


class Ch06NotesRouteTest(Test):

    # list_notes (GET, no path param, read) — should serve cleanly.
    def test_list_notes_ok(self):
        resp = self.get("/api/notes")
        assert_equal(resp.status, 200, "list_notes should return 200")
        body = json.loads(resp.body)
        assert_true("notes" in body and "count" in body, "shape: notes + count")

    # PY-06-06 — get_note path-param handler via the Test client.
    def test_get_note_path_param_py_06_06(self):
        with pytest.raises(TypeError):
            self.get("/api/notes/1")

    # PY-06-06 — get_author / get_post carry the identical positional signature
    # (id, request, response); the same flat client dispatch raises TypeError.
    # (The header named all three as victims; now demonstrated, not just claimed.)
    def test_get_author_path_param_py_06_06(self):
        with pytest.raises(TypeError):
            self.get("/api/authors/1")

    def test_get_post_path_param_py_06_06(self):
        with pytest.raises(TypeError):
            self.get("/api/posts/1")

    # PY-06-13 — the Test client bypasses the Bearer gate that `tina4 serve`
    # enforces: same POST is 401 over HTTP (PY-06-07) but 201 here. Asserting the
    # Test-client reality — a sentinel that flips if the client is ever aligned
    # to the server's auth dispatch.
    def test_create_note_post_via_test_client_py_06_13(self):
        resp = self.post("/api/notes", json={"title": "X", "content": "c", "category": "work"})
        assert_equal(resp.status, 201, "Test client bypasses the auth gate -> 201 (serve: 401)")
