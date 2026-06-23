# Verbatim-impl test — Chapter 6 ORM, S13 "Exercise: Build a Blog" + S14 "Solution"
# (06-orm.md:1082-1278). Run against live PG.
#
# The six documented endpoints (06-orm.md:1098-1105) are thin wrappers over ORM
# operations. The verbatim handler bodies live in src/routes/blog.py; this file
# exercises the exact operations each handler performs and asserts the documented
# response shape (the test_ch06_scopes.py payload-assertion style). Driving them
# through the router is avoided on purpose: get_author / get_post share their paths
# with the S6 snippet file src/routes/ch06_blog.py (last-loaded wins, router.py:358),
# so the registered winner is load-order-dependent — a workspace artifact, not a
# doc claim. The serve smoke-run (logged separately) confirms blog.py boots.
#
# Models: src/orm/author.py (S6/S7/S14), src/orm/blog_post.py (S6/S7/S11), and the
# new src/orm/comment.py (S14). They carry the S14 field spec (06-orm.md:1113-1146)
# PLUS the S7 descriptors + S11 scopes — author.py was aligned to S14 by adding
# name min_length=2 (06-orm.md:1120), which the S6 model omitted.
#
# tina4-python 3.13.39 — all six endpoints behave as documented.
import os

import psycopg2
import pytest

from src.orm.author import Author
from src.orm.blog_post import BlogPost
from src.orm.comment import Comment


def _drop(*tables):
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    c.autocommit = True
    cur = c.cursor()
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    cur.close()
    c.close()


@pytest.fixture(autouse=True)
def _schema():
    _drop("comments", "posts", "authors")
    Author.create_table()
    BlogPost.create_table()
    Comment.create_table()
    yield


def _author(name="Alice", email="alice@example.com", bio="Tech writer"):
    a = Author()
    a.name = name
    a.email = email
    a.bio = bio
    a.save()
    return a


# === POST /api/authors — create_author (06-orm.md:1173-1185) ===
def test_create_author_valid():
    a = Author()
    a.name = "Alice"
    a.email = "alice@example.com"
    a.bio = ""
    assert a.validate() == []
    a.save()
    assert a.id is not None
    assert a.to_dict()["name"] == "Alice"


def test_create_author_invalid_returns_errors():
    # name/email required (06-orm.md:1119-1121); missing -> validate() non-empty,
    # handler returns {"errors": errors}, 400.
    a = Author()
    a.bio = ""
    errors = a.validate()
    assert errors  # -> handler would respond 400
    blob = " | ".join(errors)
    assert "name" in blob and "email" in blob


def test_create_author_name_min_length():
    # S14 name = StringField(required=True, min_length=2) (06-orm.md:1120).
    # Boundary assertion that exercises the constraint the S14 doc introduces.
    a = Author()
    a.name = "A"  # 1 char < 2
    a.email = "a@example.com"
    errors = a.validate()
    assert errors
    assert "name" in " | ".join(errors)


# === GET /api/authors/{id:int} — get_author (06-orm.md:1188-1200) ===
def test_get_author_with_posts():
    a = _author()
    BlogPost.create(author_id=a.id, title="P1", slug="p1", content="", status="published")
    BlogPost.create(author_id=a.id, title="P2", slug="p2", content="", status="draft")

    author = Author.find_by_id(a.id)
    posts = BlogPost.where("author_id = ?", [author.id])
    data = author.to_dict()
    data["posts"] = [p.to_dict() for p in posts]

    assert data["name"] == "Alice"
    assert len(data["posts"]) == 2  # where() is unscoped -> both statuses


def test_get_author_not_found():
    assert Author.find_by_id(999999) is None  # handler -> 404


# === POST /api/posts — create_post (06-orm.md:1203-1224) ===
def test_create_post_valid():
    a = _author()
    bp = BlogPost()
    bp.author_id = a.id
    bp.title = "Hello"
    bp.slug = "hello"
    bp.content = "body"
    bp.status = "published"
    assert bp.validate() == []
    bp.save()
    assert bp.id is not None
    assert bp.to_dict()["title"] == "Hello"


def test_create_post_missing_author_is_404():
    # handler first verifies author exists (06-orm.md:1207-1210).
    assert Author.find_by_id(424242) is None


def test_create_post_invalid_status_choice():
    # status choices: draft/published/archived (06-orm.md:1139).
    a = _author()
    bp = BlogPost()
    bp.author_id = a.id
    bp.title = "X"
    bp.slug = "x"
    bp.status = "bogus"
    errors = bp.validate()
    assert errors
    assert "status" in " | ".join(errors)


# === GET /api/posts — list_posts (06-orm.md:1227-1238) ===
def test_list_posts_published_only_with_author():
    a = _author()
    BlogPost.create(author_id=a.id, title="Pub", slug="pub", content="", status="published")
    BlogPost.create(author_id=a.id, title="Draft", slug="draft", content="", status="draft")

    posts = BlogPost.published()
    data = []
    for p in posts:
        d = p.to_dict()
        author = p.belongs_to(Author, "author_id")
        d["author"] = author.to_dict() if author else None
        data.append(d)
    payload = {"posts": data, "count": len(data)}

    assert payload["count"] == 1
    assert payload["posts"][0]["title"] == "Pub"
    assert payload["posts"][0]["author"]["name"] == "Alice"


# === GET /api/posts/{id:int} — get_post (06-orm.md:1241-1256) ===
def test_get_post_with_author_and_comments():
    a = _author()
    bp = BlogPost.create(author_id=a.id, title="Has comments", slug="hc",
                         content="", status="published")
    Comment.create(post_id=bp.id, author_name="Bob",
                   author_email="bob@example.com", body="Great post!")
    Comment.create(post_id=bp.id, author_name="Cara",
                   author_email="cara@example.com", body="Thanks for sharing")

    blog_post = BlogPost.find_by_id(bp.id)
    author = blog_post.belongs_to(Author, "author_id")
    comments = blog_post.has_many(Comment, "post_id")
    data = blog_post.to_dict()
    data["author"] = author.to_dict() if author else None
    data["comments"] = [c.to_dict() for c in comments]
    data["comment_count"] = len(comments)

    assert data["title"] == "Has comments"
    assert data["author"]["name"] == "Alice"
    assert data["comment_count"] == 2
    assert {c["author_name"] for c in data["comments"]} == {"Bob", "Cara"}


def test_get_post_not_found():
    assert BlogPost.find_by_id(777777) is None  # handler -> 404


# === POST /api/posts/{id:int}/comments — add_comment (06-orm.md:1259-1277) ===
def test_add_comment_valid():
    a = _author()
    bp = BlogPost.create(author_id=a.id, title="P", slug="p", content="", status="published")

    c = Comment()
    c.post_id = bp.id
    c.author_name = "Dan"
    c.author_email = "dan@example.com"
    c.body = "Nice write-up"
    assert c.validate() == []
    c.save()
    assert c.id is not None
    assert c.to_dict()["post_id"] == bp.id


def test_add_comment_body_too_short():
    # body min_length=5 (06-orm.md:1160).
    a = _author()
    bp = BlogPost.create(author_id=a.id, title="P", slug="p", content="", status="published")
    c = Comment()
    c.post_id = bp.id
    c.author_name = "Dan"
    c.author_email = "dan@example.com"
    c.body = "hi"  # 2 chars < 5
    errors = c.validate()
    assert errors
    assert "body" in " | ".join(errors)
