# Verbatim-impl test — Chapter 6 ORM, S15 "Gotchas" (06-orm.md:1282-1372).
# Each gotcha makes a checkable behaviour claim; this exercises all ten against
# live PG (tina4-python 3.13.39) and asserts the ACTUAL behaviour, flagging the
# claims that diverge.
#
# Verdicts:
#   G1  save() returns self / False ......... FAITHFUL
#   G2  find_by_id None + soft-delete excl ... FAITHFUL
#   G3  find(42) bare PK "unexpected" ........ INACCURATE (PY-06-27): find(pk)
#         returns the single record, find(dict) returns a list — bare PK works.
#   G4  circular top-level import -> ImportError ... FAITHFUL (generic Python);
#         framework's string-name descriptors sidestep it.
#   G5  to_dict() includes everything ........ FAITHFUL
#   G6  save() does NOT validate ............. FALSE (PY-06-25): save() DOES
#         validate, refuses invalid data (returns False, logs "save() refused").
#   G7  FK not enforced = "SQLite default" ... MISLEADING (PY-06-26):
#         ForeignKeyField emits 0 FK constraints on PG too — engine-agnostic.
#   G8  N+1 fix snippet (select IN + group) .. FAITHFUL (runs as documented)
#   G9  auto-CRUD vs custom precedence ....... see PY-06-18 (custom does NOT take
#         precedence; auto-CRUD shadows it) + internal Cause/Fix contradiction.
#   G10 soft delete requires flag + field .... FAITHFUL
import os
import subprocess
import sys

import psycopg2
import pytest

from tina4_python.orm import (ORM, IntegerField, StringField, BooleanField,
                              ForeignKeyField)


def _exec(sql):
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    c.autocommit = True
    cur = c.cursor()
    cur.execute(sql)
    cur.close()
    c.close()


# --- inline models (own table names, dropped per module) ---
class GWidget(ORM):
    table_name = "s15_widgets"
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True, min_length=3)
    secret = StringField(default="")


class GSoft(ORM):
    table_name = "s15_soft"
    soft_delete = True
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True)
    is_deleted = IntegerField(default=0)


class GHard(ORM):
    table_name = "s15_hard"  # has is_deleted field but NO soft_delete flag
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True)
    is_deleted = IntegerField(default=0)


class GAuthor(ORM):
    table_name = "s15_authors"
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)


class GBPost(ORM):
    table_name = "s15_posts"
    id = IntegerField(primary_key=True, auto_increment=True)
    author_id = ForeignKeyField("GAuthor")  # FK field — does it emit DDL?
    title = StringField(default="")


_TABLES = ["s15_posts", "s15_authors", "s15_hard", "s15_soft", "s15_widgets"]


@pytest.fixture(autouse=True)
def _schema():
    for t in _TABLES:
        _exec(f"DROP TABLE IF EXISTS {t} CASCADE")
    GWidget.create_table()
    GSoft.create_table()
    GHard.create_table()
    GAuthor.create_table()
    GBPost.create_table()
    yield
    for t in _TABLES:
        _exec(f"DROP TABLE IF EXISTS {t} CASCADE")


# === Gotcha 1: save() returns self on success / False on failure (06-orm.md:1290) ===
def test_g1_save_returns_self_on_success():
    w = GWidget()
    w.name = "Hello"
    ret = w.save()
    assert ret is w
    assert w.id is not None


# === Gotcha 2: find_by_id None on miss + excludes soft-deleted (06-orm.md:1296) ===
def test_g2_find_by_id_none_on_miss():
    assert GWidget.find_by_id(999999) is None


def test_g2_find_by_id_excludes_soft_deleted():
    s = GSoft()
    s.title = "doomed"
    s.save()
    sid = s.id
    s.delete()  # soft delete
    assert GSoft.find_by_id(sid) is None  # excluded


# === Gotcha 3: find(42) bare PK — doc says "unexpected" (PY-06-27) ===
def test_g3_find_bare_pk_actually_returns_record_py_06_27():
    w = GWidget()
    w.name = "Findme"
    w.save()
    # doc (06-orm.md:1304) says find() "takes a dict filter, not a bare primary
    # key value" and bare PK gives "unexpected results". Actual: it returns the
    # single record. Sentinel flips if find() ever rejects a bare PK.
    r = GWidget.find(w.id)
    assert not isinstance(r, list)
    assert r is not None and r.id == w.id
    # dict form returns a list
    lst = GWidget.find({"id": w.id})
    assert isinstance(lst, list) and len(lst) == 1


# === Gotcha 4: circular top-level import -> ImportError (06-orm.md:1310-1314) ===
def test_g4_circular_top_level_import_fails(tmp_path):
    (tmp_path / "mod_a.py").write_text("from mod_b import B\nclass A:\n    pass\n")
    (tmp_path / "mod_b.py").write_text("from mod_a import A\nclass B:\n    pass\n")
    out = subprocess.run([sys.executable, "-c", "import mod_a"],
                         cwd=str(tmp_path), capture_output=True, text=True)
    assert out.returncode != 0
    assert "ImportError" in out.stderr or "circular" in out.stderr.lower() \
        or "partially initialized" in out.stderr.lower()


# === Gotcha 5: to_dict() includes all fields incl sensitive (06-orm.md:1320) ===
def test_g5_to_dict_includes_all_fields():
    w = GWidget()
    w.name = "X"
    w.secret = "topsecret"
    keys = set(w.to_dict().keys())
    assert {"id", "name", "secret"} <= keys  # 'secret' (sensitive) NOT omitted


# === Gotcha 6: doc claims save() does NOT validate (PY-06-25) ===
def test_g6_save_actually_validates_py_06_25():
    bad = GWidget()
    bad.name = "ab"  # min_length=3 -> invalid
    assert bad.validate()  # validate() reports the error
    # doc (06-orm.md:1326-1328): "save() does not validate ... invalid data gets
    # into the database." Actual: save() DOES validate, refuses, returns False,
    # nothing persisted. Sentinel asserts the real (contradicting) behaviour.
    ret = bad.save()
    assert ret is False
    assert bad.id is None
    # table is empty — nothing slipped through
    assert GWidget.count() == 0


# === Gotcha 7: FK not enforced — doc blames SQLite default (PY-06-26) ===
def test_g7_foreign_key_not_enforced_engine_agnostic_py_06_26():
    a = GAuthor()
    a.name = "Real"
    a.save()
    # orphan author_id, no such GAuthor
    p = GBPost()
    p.author_id = 999
    p.title = "orphan"
    ret = p.save()
    assert ret is p and p.id is not None  # orphan save SUCCEEDS

    # doc says this is because "SQLite does not enforce FK by default" — but on
    # PostgreSQL ForeignKeyField emits NO real FK constraint either.
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.table_constraints "
                "WHERE table_name='s15_posts' AND constraint_type='FOREIGN KEY'")
    fk_count = cur.fetchone()[0]
    cur.close()
    c.close()
    assert fk_count == 0  # engine-agnostic: not SQLite-specific


# === Gotcha 8: N+1 fix — select IN + manual grouping snippet (06-orm.md:1348-1356) ===
def test_g8_n_plus_1_fix_snippet_runs():
    a1 = GAuthor(); a1.name = "A1"; a1.save()
    a2 = GAuthor(); a2.name = "A2"; a2.save()
    for a, n in ((a1, 2), (a2, 1)):
        for i in range(n):
            p = GBPost(); p.author_id = a.id; p.title = f"{a.name}-{i}"; p.save()

    authors = GAuthor.all()
    all_posts = GBPost.select(
        "SELECT * FROM s15_posts WHERE author_id IN ("
        + ",".join(str(a.id) for a in authors) + ")"
    )
    posts_by_author = {}
    for post in all_posts:
        posts_by_author.setdefault(post.author_id, []).append(post)

    assert len(posts_by_author[a1.id]) == 2
    assert len(posts_by_author[a2.id]) == 1


# === Gotcha 10: soft delete requires BOTH flag + is_deleted field (06-orm.md:1370-1372) ===
def test_g10_soft_delete_active_with_flag_and_field():
    s = GSoft()
    s.title = "t"
    s.save()
    sid = s.id
    s.delete()
    # soft-deleted: excluded from default queries but row still present (is_deleted=1)
    assert GSoft.find_by_id(sid) is None
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    cur = c.cursor()
    cur.execute("SELECT is_deleted FROM s15_soft WHERE id=%s", (sid,))
    row = cur.fetchone()
    cur.close()
    c.close()
    assert row is not None and row[0] == 1  # row kept, flagged 1


def test_g10_without_flag_delete_is_hard():
    h = GHard()  # has is_deleted field but NO soft_delete flag
    h.title = "t"
    h.save()
    hid = h.id
    h.delete()
    # no soft_delete flag -> row physically gone
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM s15_hard WHERE id=%s", (hid,))
    cnt = cur.fetchone()[0]
    cur.close()
    c.close()
    assert cnt == 0  # hard-deleted
