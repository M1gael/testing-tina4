# Verbatim-impl test — Chapter 6 ORM, S7 "Eager Loading".
# Uses the canonical src/orm models, which now carry the S7 descriptors
# (Author.posts, BlogPost.author, BlogPost.comments). No inline duplicate
# classes — a duplicate same-named class collides with the global descriptor
# name registry and makes `posts.comments` resolve the wrong class.
#
# S7 references a `Comment` model it never defines (PY-06-12): the `comments`
# descriptor, `include=["comments"]`, nested `posts.comments`, and the
# to_dict-with-comments example all raise `ValueError: Related model 'Comment'
# not found`. Those are asserted as blocked, not scaffolded around.
import os

import psycopg2
import pytest

from src.orm.author import Author
from src.orm.blog_post import BlogPost


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
    yield
    # No teardown drop — leave tables + rows visible after the run.


@pytest.fixture(autouse=True)
def _clean():
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


# --- PY-06-12: comments path blocked (S7 never defines Comment) ---
def test_include_comments_blocked_py_06_12():
    # Verbatim S7 lines 718 / 737-738 reference include=["author", "comments"].
    _, p1, _ = _seed()
    with pytest.raises(ValueError, match="Related model 'Comment' not found"):
        BlogPost.find_by_id(p1.id, include=["author", "comments"])


def test_lazy_comments_blocked_py_06_12():
    _, p1, _ = _seed()
    post = BlogPost.find_by_id(p1.id)
    with pytest.raises(ValueError, match="Related model 'Comment' not found"):
        _ = post.comments


def test_nested_posts_comments_blocked_py_06_12():
    # Verbatim S7 nested example (06-orm.md:727).
    _seed()
    with pytest.raises(ValueError, match="Related model 'Comment' not found"):
        Author.all(include=["posts", "posts.comments"])
