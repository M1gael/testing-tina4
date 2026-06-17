# Verbatim-impl test — Chapter 6 ORM, S6 "Relationships" (imperative style).
# Exercises has_many / belongs_to / has_one on the documented Author + BlogPost
# models (src/orm/author.py, src/orm/blog_post.py) the way the S6 route
# handlers (src/routes/ch06_blog.py) call them.
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
    _drop("posts", "authors")
    Author.create_table()
    BlogPost.create_table()
    yield
    _drop("posts", "authors")


@pytest.fixture(autouse=True)
def _clean():
    for p in BlogPost.all():
        p.delete()
    for a in Author.all():
        a.delete()
    yield


def _author(name="Alice", email="alice@example.com"):
    return Author.create(name=name, email=email, bio="Tech writer")


def _post(author_id, title, slug, status="published"):
    return BlogPost.create(
        author_id=author_id, title=title, slug=slug,
        content="...", status=status,
    )


# --- has_many ---
def test_has_many_returns_authors_posts():
    a = _author()
    _post(a.id, "Getting Started with Tina4", "getting-started")
    _post(a.id, "Advanced Routing", "advanced-routing", status="draft")
    posts = a.has_many(BlogPost, "author_id")
    assert len(posts) == 2
    assert {p.title for p in posts} == {"Getting Started with Tina4", "Advanced Routing"}


def test_has_many_empty():
    a = _author(name="Loner", email="loner@example.com")
    assert a.has_many(BlogPost, "author_id") == []


# --- belongs_to ---
def test_belongs_to_returns_parent_author():
    a = _author()
    p = _post(a.id, "Post One", "post-one")
    author = p.belongs_to(Author, "author_id")
    assert author is not None
    assert author.id == a.id
    assert author.name == "Alice"


# --- has_one ---
def test_has_one_returns_single_or_none():
    a = _author(name="Solo", email="solo@example.com")
    _post(a.id, "Only Post", "only-post")
    one = a.has_one(BlogPost, "author_id")
    assert one is not None
    assert one.title == "Only Post"

    b = _author(name="None", email="none@example.com")
    assert b.has_one(BlogPost, "author_id") is None
