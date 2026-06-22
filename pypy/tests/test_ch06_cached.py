# Verbatim-impl test — Chapter 6 ORM, S10 "Cached Queries" (06-orm.md:956-972).
#   popular = Note.cached(SQL, [True], ttl=60, limit=20)   -> list[Note], in-memory TTL cache
#   Note.clear_cache()                                      -> (doc) "Clear the cache when data changes"
#
# Found on tina4-python 3.13.30. Behaviour observed implementing the section verbatim:
#   - cached() works: returns list[Note], honours the filter/limit, and genuinely
#     serves STALE rows within the TTL window for out-of-band writes (raw SQL /
#     another process) — proven by raw INSERT between two calls.
#   - `pinned = ?` with [True] binds as a real PG boolean (parameterised, so it
#     side-steps the `= 1` boolean-literal hazard from earlier sections).
#   - PY-06-21 (minor, doc-completeness): ORM writes (.save()) auto-invalidate the
#     query cache. The chapter never mentions this — it frames clear_cache() as the
#     handler for "when data changes".
#   - PY-06-22 (framework defect, found 3.13.30; FIXED in 3.13.39, verified 2026-06-22):
#     On 3.13.30, at the documented API level Note.clear_cache() did NOT make a subsequent
#     cached() reflect changed data — contradicting S10. Root cause then: TWO cache layers.
#     clear_cache() cleared the module-level ORM cache (_query_cache.clear_tag,
#     orm/model.py) but cached() reads through cls.select() -> Database.fetch(), which has
#     its OWN request-scoped cache (db._query_cache, default-on, mode='request', ttl=5s)
#     that clear_cache() never touched. On 3.13.39 clear_cache() now invalidates the
#     DB-layer cache too: after an out-of-band insert + clear_cache(), cached() returns the
#     fresh row count, and after clear_cache() + DROP TABLE, cached() re-hits the DB and
#     raises UndefinedTable (it no longer serves stale rows). The two tests below now
#     assert that corrected behaviour; they were the red sentinels that flagged the fix.
#   - PY-06-21 (still observed 3.13.39): ORM writes (.save()) auto-invalidate the cache —
#     undocumented; insert/update/delete call db._cache_invalidate().
import os

import psycopg2
import pytest

from src.orm.note import Note

SQL = "SELECT * FROM notes WHERE pinned = ? ORDER BY id"


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
    _exec("DROP TABLE IF EXISTS notes CASCADE")
    Note.create_table()
    Note.clear_cache()  # belt-and-braces; cache is class-level
    # seed: two pinned, one not
    _exec(
        "INSERT INTO notes (title, pinned, content, category) "
        "VALUES ('A', true, '', 'g'), ('B', true, '', 'g'), ('C', false, '', 'g')"
    )
    yield


# Verbatim S10 snippet (06-orm.md:961-965)
def test_cached_returns_note_list():
    popular = Note.cached(
        "SELECT * FROM notes WHERE pinned = ? ORDER BY created_at DESC",
        [True], ttl=60, limit=20
    )
    assert isinstance(popular, list)
    assert len(popular) == 2                        # only the two pinned rows
    assert all(isinstance(n, Note) for n in popular)
    assert {n.title for n in popular} == {"A", "B"}


# TTL cache serves stale results for out-of-band writes within the window
def test_cached_serves_stale_within_ttl():
    first = Note.cached(SQL, [True], ttl=60, limit=20)
    assert len(first) == 2

    # mutate behind the ORM's back — no .save(), so no auto-invalidation
    _exec("INSERT INTO notes (title, pinned, content, category) VALUES ('D', true, '', 'g')")

    second = Note.cached(SQL, [True], ttl=60, limit=20)
    assert len(second) == 2                         # stale -> cache hit, not the new row
    assert second is first                          # same cached object handed back


# PY-06-21: ORM writes auto-invalidate the cache (undocumented but it DOES refresh)
def test_orm_save_auto_invalidates_cache():
    assert len(Note.cached(SQL, [True], ttl=60, limit=20)) == 2
    Note(title="E", pinned=True).save()             # ORM write
    assert len(Note.cached(SQL, [True], ttl=60, limit=20)) == 3   # auto-dropped by .save()


# PY-06-22 (FIXED 3.13.39): clear_cache() now refreshes cached(), honouring the doc
# (06-orm.md:968-971) "clear the cache when data changes". After an out-of-band insert
# and clear_cache(), cached() reflects the new row. (On 3.13.30 this returned the stale 2.)
def test_clear_cache_refreshes_cached():
    assert len(Note.cached(SQL, [True], ttl=60, limit=20)) == 2
    _exec("INSERT INTO notes (title, pinned, content, category) VALUES ('D', true, '', 'g')")
    Note.clear_cache()
    after = Note.cached(SQL, [True], ttl=60, limit=20)
    assert len(after) == 3                          # FIXED: fresh; clear_cache invalidated the DB-layer cache


# Strongest proof clear_cache() now re-hits the DB: drop the table after clear_cache()
# and cached() raises instead of serving stale rows. (On 3.13.30 it returned the cached
# rows with no DB error, proving clear_cache() was a no-op for cached().)
def test_clear_cache_rehits_db():
    assert len(Note.cached(SQL, [True], ttl=60, limit=20)) == 2
    Note.clear_cache()
    _exec("DROP TABLE notes CASCADE")
    with pytest.raises(psycopg2.errors.UndefinedTable):
        Note.cached(SQL, [True], ttl=60, limit=20)   # FIXED: re-hits DB -> UndefinedTable
