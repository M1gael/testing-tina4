# Verbatim-impl test — Chapter 6 ORM, S7 "Eager Loading".
# Uses the canonical src/orm models, which now carry the S7 descriptors
# (Author.posts, BlogPost.author, BlogPost.comments). No inline duplicate
# classes — a duplicate same-named class collides with the global descriptor
# name registry and makes `posts.comments` resolve the wrong class.
#
# PY-06-12 is a doc-ORDERING finding: S7 references a `Comment` model it never
# defines — the model first appears in S14 (06-orm.md:1150). A strictly
# sequential reader AT S7 (no Comment yet) hits `ValueError: Related model
# 'Comment' not found` on every comments path (the `comments` descriptor,
# include=["comments"], nested posts.comments, to_dict-with-comments). That
# S7-state block is preserved here as an isolated subprocess sentinel
# (test_comments_blocked_without_comment_model_py_06_12).
#
# Once the chapter is fully implemented (S14 defines src/orm/comment.py), the
# `Comment` model resolves and the S7 comments eager-loading works exactly as
# S7 documents — asserted by the three test_*_comments tests below. PY-06-12
# stays open as the doc-ordering defect; the runtime no longer blocks once the
# reader reaches S14.
import os
import subprocess
import sys

import psycopg2
import pytest

from src.orm.author import Author
from src.orm.blog_post import BlogPost
from src.orm.comment import Comment

PYPY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    _drop("comments", "posts", "authors")
    Author.create_table()
    BlogPost.create_table()
    Comment.create_table()
    yield
    # No teardown drop — leave tables + rows visible after the run.


@pytest.fixture(autouse=True)
def _clean():
    for c in Comment.all():
        c.delete()
    for p in BlogPost.all():
        p.delete()
    for a in Author.all():
        a.delete()
    yield


def _seed():
    a = Author.create(name="Alice", email="alice@example.com", bio="Tech writer")
    p1 = BlogPost.create(author_id=a.id, title="Getting Started with Tina4",
                         slug="getting-started", content="...", status="published")
    p2 = BlogPost.create(author_id=a.id, title="Advanced Routing",
                         slug="advanced-routing", content="...", status="draft")
    return a, p1, p2


# --- Declarative descriptors: lazy access (06-orm.md:703-708) ---
def test_lazy_has_many_posts():
    a, _, _ = _seed()
    fetched = Author.find_by_id(a.id)
    titles = [post.title for post in fetched.posts]
    assert set(titles) == {"Getting Started with Tina4", "Advanced Routing"}


def test_lazy_belongs_to_author():
    _, p1, _ = _seed()
    post = BlogPost.find_by_id(p1.id)
    assert post.author.name == "Alice"


# --- Eager loading via include (06-orm.md:714-715) ---
def test_eager_all_include_posts():
    _seed()
    authors = Author.all(include=["posts"])
    assert len(authors) == 1
    data = authors[0].to_dict(include=["posts"])
    assert len(data["posts"]) == 2


# include=["author"] half of 06-orm.md:718 — the "author" relationship resolves
# (the "comments" half is blocked by PY-06-12, asserted below).
def test_eager_find_by_id_include_author():
    _, p1, _ = _seed()
    post = BlogPost.find_by_id(p1.id, include=["author"])
    data = post.to_dict(include=["author"])
    assert data["author"]["name"] == "Alice"


# --- S7 comments paths — resolve once S14 defines Comment (PY-06-12 ordering) ---
def _seed_comment(post_id):
    return Comment.create(post_id=post_id, author_name="Bob",
                          author_email="bob@example.com", body="Great post!")


def test_lazy_comments_resolves_after_s14():
    # S7 lazy descriptor (06-orm.md:697). Blocked at S7 (PY-06-12); works once
    # src/orm/comment.py (S14) exists.
    _, p1, _ = _seed()
    _seed_comment(p1.id)
    post = BlogPost.find_by_id(p1.id)
    comments = post.comments
    assert len(comments) == 1
    assert comments[0].author_name == "Bob"


def test_include_comments_resolves_after_s14():
    # Verbatim S7 lines 718 / 737-738: include=["author", "comments"].
    _, p1, _ = _seed()
    _seed_comment(p1.id)
    post = BlogPost.find_by_id(p1.id, include=["author", "comments"])
    data = post.to_dict(include=["author", "comments"])
    assert data["author"]["name"] == "Alice"
    assert len(data["comments"]) == 1


def test_nested_posts_comments_resolves_after_s14():
    # Verbatim S7 nested example (06-orm.md:727): include=["posts", "posts.comments"].
    a, p1, _ = _seed()
    _seed_comment(p1.id)
    authors = Author.all(include=["posts", "posts.comments"])
    data = authors[0].to_dict(include=["posts", "posts.comments"])
    by_id = {p["id"]: p for p in data["posts"]}
    assert len(by_id[p1.id]["comments"]) == 1


# --- PY-06-12 evidence preserved: the S7-reader state (Comment undefined). ---
# Isolated subprocess imports only author + blog_post (NOT comment), so the
# `comments` descriptor cannot resolve "Comment" from ORM.__subclasses__()
# (fields.py:271-289) and raises exactly the error a sequential S7 reader hits.
def test_comments_blocked_without_comment_model_py_06_12():
    snippet = (
        "from src.orm.blog_post import BlogPost\n"
        "bp = BlogPost()\n"
        "bp.id = 1\n"
        "try:\n"
        "    _ = bp.comments\n"
        "    print('RESOLVED')\n"
        "except ValueError as e:\n"
        "    print('BLOCKED:' + str(e))\n"
        "except Exception as e:\n"
        "    print('OTHER:' + type(e).__name__)\n"
    )
    out = subprocess.run([sys.executable, "-c", snippet], cwd=PYPY,
                         capture_output=True, text=True)
    assert "BLOCKED:Related model 'Comment' not found" in out.stdout, out.stdout + out.stderr
