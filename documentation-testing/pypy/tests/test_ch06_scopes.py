# Verbatim-impl test — Chapter 6 ORM, S11 "Scopes" (06-orm.md:976-1027).
# Implemented exactly as the section shows, run against live PG.
#
# S11 redefines `BlogPost` (table_name="posts") with a different schema than S6's
# src/orm/blog_post.py (PY-06-05 collision). To avoid clobbering the S6 model the
# S11 class is reproduced inline here, verbatim from the chapter.
#
# Snippets exercised, with what live PG showed (tina4-python 3.13.30):
#   (1) classmethod scopes
#         published() / drafts()  -> work; return list[BlogPost] filtered by status.
#         recent(days=7)          -> BROKEN on PostgreSQL (PY-06-23). The scope uses
#                                    SQLite-only `datetime('now', ?)`; PG raises
#                                    UndefinedFunction: function datetime(...) does not exist.
#   (2) routes that call the scopes (handler payload exercised directly).
#   (3) dynamic registration  BlogPost.scope("active", "status != ?", ["archived"])
#                             -> BlogPost.active()  -> works as documented.
#
# test_recent_scope asserts the ACTUAL (failing) PG behaviour so it stays green as a
# sentinel; it flips red if the framework/doc stops emitting SQLite datetime() on PG.
import os

import psycopg2
import pytest

from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField


# --- verbatim S11 model (06-orm.md:980-1003) ---
class BlogPost(ORM):
    table_name = "posts"

    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True)
    status = StringField(default="draft")
    created_at = DateTimeField()

    @classmethod
    def published(cls):
        return cls.where("status = ?", ["published"])

    @classmethod
    def drafts(cls):
        return cls.where("status = ?", ["draft"])

    @classmethod
    def recent(cls, days=7):
        return cls.where(
            "created_at > datetime('now', ?)",
            [f"-{days} days"]
        )


def _conn():
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    c.autocommit = True
    return c


def _exec(sql):
    c = _conn()
    cur = c.cursor()
    cur.execute(sql)
    cur.close()
    c.close()


@pytest.fixture(autouse=True)
def _schema():
    _exec("DROP TABLE IF EXISTS posts CASCADE")
    BlogPost.create_table()
    _exec(
        "INSERT INTO posts (title, status, created_at) VALUES "
        "('Pub recent', 'published', NOW()), "
        "('Pub old',    'published', NOW() - INTERVAL '30 days'), "
        "('A draft',    'draft',     NOW()), "
        "('Archived',   'archived',  NOW())"
    )
    yield


# (1) published() scope — 06-orm.md:989-991
def test_published_scope():
    posts = BlogPost.published()
    assert len(posts) == 2
    assert all(p.status == "published" for p in posts)


# (1) drafts() scope — 06-orm.md:993-995
def test_drafts_scope():
    posts = BlogPost.drafts()
    assert len(posts) == 1
    assert posts[0].status == "draft"


# (1) recent() scope — 06-orm.md:997-1002 — PY-06-23: datetime('now', ?) is SQLite
# syntax; on PostgreSQL it raises UndefinedFunction. Sentinel asserts the failure.
def test_recent_scope_breaks_on_postgres():
    with pytest.raises(psycopg2.errors.UndefinedFunction):
        BlogPost.recent()


# (2) route payload — 06-orm.md:1008-1011: {"posts": [p.to_dict() for p in BlogPost.published()]}
def test_published_route_payload():
    payload = {"posts": [p.to_dict() for p in BlogPost.published()]}
    assert len(payload["posts"]) == 2
    assert all(p["status"] == "published" for p in payload["posts"])


# (3) dynamic scope registration — 06-orm.md:1022-1026
def test_dynamic_scope_active():
    BlogPost.scope("active", "status != ?", ["archived"])
    posts = BlogPost.active()
    assert len(posts) == 3  # published x2 + draft x1, archived excluded
    assert all(p.status != "archived" for p in posts)
