# Verbatim-impl test — Chapter 6 ORM, S8 "Soft Delete".
# Exercises the documented soft-delete behaviour on the verbatim Task model
# (src/orm/task.py) exactly as S8 describes it. DB bound by conftest.
import os

import psycopg2
import pytest

from src.orm.task import Task


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
    _drop("tasks")
    Task.create_table()
    yield
    # No teardown drop — rows stay visible after the run.


@pytest.fixture(autouse=True)
def _clean():
    for t in Task.with_trashed():
        t.force_delete()
    yield


# delete() -> soft delete: is_deleted=1, row stays, hidden from standard queries
def test_delete_is_soft():
    t = Task.create(title="A")
    t.delete()
    assert Task.find_by_id(t.id) is None              # hidden
    assert len(Task.with_trashed()) == 1              # row still there


# all() / where() / find_by_id() filter out soft-deleted records
def test_standard_queries_exclude_deleted():
    keep = Task.create(title="keep")
    gone = Task.create(title="gone")
    gone.delete()
    assert len(Task.all()) == 1
    assert Task.all()[0].id == keep.id
    assert len(Task.where("title = ?", ["gone"])) == 0
    assert Task.find_by_id(gone.id) is None


# restore() -> is_deleted=0, visible again
def test_restore():
    t = Task.create(title="R")
    t.delete()
    assert Task.find_by_id(t.id) is None
    t.restore()
    assert Task.find_by_id(t.id) is not None


# force_delete() -> row permanently removed
def test_force_delete():
    t = Task.create(title="F")
    t.force_delete()
    assert Task.find_by_id(t.id) is None
    assert len(Task.with_trashed()) == 0              # gone for good


# with_trashed() includes soft-deleted records
def test_with_trashed_includes_deleted():
    a = Task.create(title="active")
    d = Task.create(title="deleted")
    d.delete()
    assert len(Task.with_trashed()) == 2


# with_trashed(filter) -- verbatim chapter line passes [1] for the boolean
# `completed` column (06-orm.md:809). On PG `completed` is BOOLEAN, so
# `completed = 1` raises `operator does not exist: boolean = integer`
# (PY-06-14, same hazard family as PY-06-08). Recorded verbatim.
def test_with_trashed_filter_verbatim_known_broken_on_pg():
    t = Task.create(title="done")
    t.completed = True
    t.save()
    t.delete()
    with pytest.raises(Exception):
        Task.with_trashed("completed = ?", [1])


def test_with_trashed_filter_works_with_boolean():
    # Same method, real boolean param -> confirms with_trashed(filter) works.
    t = Task.create(title="done2")
    t.completed = True
    t.save()
    t.delete()
    assert len(Task.with_trashed("completed = ?", [True])) >= 1


# count() respects soft delete -- only counts active records
def test_count_respects_soft_delete():
    Task.create(title="a")
    b = Task.create(title="b")
    b.delete()
    assert Task.count() == 1


# count(filter) -- verbatim chapter line filters on `category` (06-orm.md:820),
# a column the Task model never defines -> UndefinedColumn (PY-06-15, family of
# PY-06-04). Recorded verbatim.
def test_count_category_verbatim_known_broken():
    Task.create(title="x")
    with pytest.raises(Exception):
        Task.count("category = ?", ["work"])
