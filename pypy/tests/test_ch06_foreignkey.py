# Verbatim-impl test — Chapter 6 ORM, S6 "ForeignKeyField — Auto-Wired
# Relationships" (06-orm.md:499-528). A single ForeignKeyField declaration
# wires both sides: post.author (belongs_to) and author.posts (has_many via
# related_name).
#
# The Author/BlogPost here are the verbatim FK-example classes, distinct from
# the S6 has_many models in src/orm/. This module owns `authors` + `posts`
# (FK-example schema) for the duration of its run (PY-06-05 — "posts" is shared
# across several Chapter-6 model definitions).
import os

import psycopg2
import pytest

from tina4_python.orm import ORM, IntegerField, StringField, ForeignKeyField


class Author(ORM):
    table_name = "authors"
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)


class BlogPost(ORM):
    table_name = "posts"
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True)
    author_id = ForeignKeyField(to=Author, related_name="posts")


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
    # No teardown drop — leave tables + rows visible after the run.


@pytest.fixture(autouse=True)
def _clean():
    for p in BlogPost.all():
        p.delete()
    for a in Author.all():
        a.delete()
    yield


# --- belongs_to accessor: post.author ---
def test_belongs_to_accessor():
    a = Author.create(name="Alice")
    p = BlogPost.create(title="Getting Started with Tina4", author_id=a.id)
    assert p.author is not None
    assert p.author.name == "Alice"


# --- has_many accessor (related_name="posts"): author.posts ---
def test_has_many_accessor():
    a = Author.create(name="Alice")
    BlogPost.create(title="Post 1", author_id=a.id)
    BlogPost.create(title="Post 2", author_id=a.id)
    titles = [p.title for p in a.posts]
    assert len(titles) == 2
    assert set(titles) == {"Post 1", "Post 2"}
