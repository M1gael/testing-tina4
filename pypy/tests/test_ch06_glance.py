# Verbatim-impl test — Chapter 6 "ORM at a Glance" (Python).
# Exercises the glance Post model (src/orm/post.py) and the Python column of
# the "Common Query Operations" table (06-orm.md:85-94).
#
# Note: the glance Post and the S6 BlogPost both declare table_name="posts"
# with different schemas (PY-06-05, known). This module owns the `posts` table
# with the glance Post schema for the duration of its run.
import os

import psycopg2
import pytest

from src.orm.post import Post


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
    _drop("posts")
    Post.create_table()
    yield
    # No teardown drop — leave tables + rows visible after the run.


@pytest.fixture(autouse=True)
def _clean():
    for p in Post.all():
        p.delete()
    yield


# --- Build and save: Post.create(title="x") ---
def test_create():
    p = Post.create(title="x")
    assert p.id is not None


# --- Save an instance: post.save() ---
def test_save_instance():
    p = Post()
    p.title = "saved"
    p.save()
    assert p.id is not None


# --- Find by primary key: Post.find_by_id(1) ---
def test_find_by_id():
    p = Post.create(title="byid")
    assert Post.find_by_id(p.id).title == "byid"


# --- Filter by attributes: Post.find({"title": "x"}) ---
def test_find_filter():
    Post.create(title="x")
    Post.create(title="y")
    assert len(Post.find({"title": "x"})) == 1


# --- Raw SQL where clause: Post.where("title = ?", ["x"]) ---
def test_where():
    Post.create(title="x")
    assert len(Post.where("title = ?", ["x"])) == 1


# --- Fetch every row: Post.all() ---
def test_all():
    Post.create(title="a")
    Post.create(title="b")
    assert len(Post.all()) == 2


# --- Count rows: Post.count() ---
def test_count():
    Post.create(title="a")
    Post.create(title="b")
    assert Post.count() == 2


# --- Delete a record: post.delete() ---
def test_delete():
    p = Post.create(title="gone")
    p.delete()
    assert Post.find_by_id(p.id) is None
