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
#   - PY-06-22 (framework defect, verified + reframed 2026-06-18): at the documented
#     API level, Note.clear_cache() does NOT make a subsequent cached() reflect changed
#     data — contradicting S10. Accurate root cause (adversarial pass): there are TWO
#     cache layers. clear_cache() DOES clear the module-level ORM cache
#     (_query_cache.clear_tag, orm/model.py:882-884). But cached() reads through
#     cls.select() -> Database.fetch(), which has its OWN request-scoped cache
#     (db._query_cache, default-on, mode='request', ttl=5s, database/connection.py:521-548)
#     that clear_cache() never touches. Proof: clearing BOTH clear_cache()+db.cache_clear()
#     -> fresh; clear_cache() alone -> stale; cached() serves rows even after DROP TABLE.
#     Explains PY-06-21: insert/update/delete call db._cache_invalidate(), so .save()
#     refreshes — a different path. Severity nuance: under `tina4 serve` the DB cache is
#     cleared per-request (cache_new_request), so staleness is bounded to within one
#     handler + the 5s TTL; a reader calling clear_cache() then cached() in the same
#     handler still gets stale data. These tests run in a single sync process (no request
#     boundary), so the 5s TTL holds for the sub-second test window.
#
# The two divergent tests below assert the ACTUAL (buggy) behaviour so they stay
# green as sentinels; they flip red when the framework starts honouring clear_cache().
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


# PY-06-22: clear_cache() does not refresh cached(). Doc (06-orm.md:968-971) says it
# clears "when data changes"; cached() still returns stale because it depends on the
# DB-layer cache (db._query_cache) that clear_cache() does not invalidate. Sentinel
# asserts the buggy behaviour so it flips red when the framework starts honouring it.
def test_clear_cache_does_not_refresh_cached():
    assert len(Note.cached(SQL, [True], ttl=60, limit=20)) == 2
    _exec("INSERT INTO notes (title, pinned, content, category) VALUES ('D', true, '', 'g')")
    Note.clear_cache()
    after = Note.cached(SQL, [True], ttl=60, limit=20)
    assert len(after) == 2                          # BUG: still stale; doc claims fresh (3)


# Strongest proof clear_cache() never re-hits the DB: drop the table after
# clear_cache() and cached() STILL returns the cached rows instead of erroring.
def test_clear_cache_does_not_rehit_db():
    assert len(Note.cached(SQL, [True], ttl=60, limit=20)) == 2
    Note.clear_cache()
    _exec("DROP TABLE notes CASCADE")
    served = Note.cached(SQL, [True], ttl=60, limit=20)
    assert len(served) == 2                          # served from cache; no DB error -> clear_cache no-op
