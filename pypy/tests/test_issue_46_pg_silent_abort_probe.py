# Probe for tina4stack/tina4-python issue #46
# https://github.com/tina4stack/tina4-python/issues/46
#
# Source-read confirmation of the fix at postgres.py:148-152.
# Stubs psycopg2 with a cursor that mimics real psycopg2 SAVEPOINT
# semantics (a failed statement poisons the transaction until either
# ROLLBACK or ROLLBACK TO SAVEPOINT lands), then exercises the real
# `PostgreSQLAdapter.fetch()` code path unchanged.
#
# Companion to test_issue_46_live_repro.py, which runs against a live
# PostgreSQL 18 instance. This file proves the code-path shape
# without needing the live infrastructure — useful for CI / fresh
# clones.
#
# Probe assertions are FIX-DIRECTION:
#   (a) the count-probe failure does NOT propagate — the bare except
#       still recovers and falls back to total=0.
#   (b) the fix wraps the probe in SAVEPOINT / ROLLBACK TO SAVEPOINT
#       so the connection's aborted state is cleared.
#   (c) Log.error is invoked on the swallow path with the original
#       cause in the structured payload — the visibility gap is
#       closed.
#   (d) The paginated query AFTER the count-probe recovery runs
#       cleanly (no InFailedSqlTransaction cascade).
#
# If the upstream fix is reverted, all four FLIP to failure.

import sys
import types
import pytest

from tina4_python.database.postgres import PostgreSQLAdapter


# ---- Fake psycopg2 surface ----------------------------------------

class _FakeInFailedSqlTransaction(Exception):
    """Stand-in for psycopg2.errors.InFailedSqlTransaction."""
    pass


class _FakeOperatorError(Exception):
    """Stand-in for psycopg2.errors.UndefinedFunction — the kind of
    error PG raises on `is_deleted = 0` against a BOOLEAN column."""
    pass


class _FakeCursor:
    """Models the relevant slice of psycopg2 behaviour:
      - Failing a statement flips the connection into `_aborted`.
      - While aborted, every statement raises InFailedSqlTransaction,
        EXCEPT `ROLLBACK [TO SAVEPOINT ...]` which clears the flag
        (just like real psycopg2 — psycopg2 lets you ROLLBACK out of
        an aborted state).
      - SAVEPOINT / RELEASE statements pass through.
      - The first call to the user SQL inside `_count_subquery` is
        the one we choose to fail (mirroring `boolean = integer`).
    """

    def __init__(self, fail_on_count: bool = True):
        self.executed: list[str] = []
        self.fail_on_count = fail_on_count
        self._aborted = False
        self._count_failed_once = False
        self.description = None

    def execute(self, sql, params=None):
        self.executed.append(sql)
        sql_upper = sql.strip().upper()

        # Real psycopg2: ROLLBACK / ROLLBACK TO SAVEPOINT always
        # works (it's the way out of aborted state).
        if sql_upper.startswith("ROLLBACK"):
            self._aborted = False
            return

        # SAVEPOINT / RELEASE pass through cleanly.
        if sql_upper.startswith("SAVEPOINT") or sql_upper.startswith("RELEASE"):
            if self._aborted:
                raise _FakeInFailedSqlTransaction(
                    "current transaction is aborted, commands ignored "
                    "until end of transaction block"
                )
            return

        if self._aborted:
            raise _FakeInFailedSqlTransaction(
                "current transaction is aborted, commands ignored "
                "until end of transaction block"
            )

        # First time we see the count probe → fail it.
        if self.fail_on_count and "_count_subquery" in sql and not self._count_failed_once:
            self._count_failed_once = True
            self._aborted = True
            raise _FakeOperatorError(
                "operator does not exist: boolean = integer"
            )

    def fetchone(self):
        return {"cnt": 0}

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor
        self.rollback_calls = 0
        self.commit_calls = 0
        self.autocommit = False

    def cursor(self, cursor_factory=None):
        return self._cursor

    def rollback(self):
        self.rollback_calls += 1
        self._cursor._aborted = False

    def commit(self):
        self.commit_calls += 1


def _install_fake_psycopg2(monkeypatch):
    fake_psycopg2 = types.ModuleType("psycopg2")
    fake_extras = types.ModuleType("psycopg2.extras")

    class _FakeRealDictCursor:
        pass

    fake_extras.RealDictCursor = _FakeRealDictCursor
    fake_psycopg2.extras = fake_extras
    monkeypatch.setitem(sys.modules, "psycopg2", fake_psycopg2)
    monkeypatch.setitem(sys.modules, "psycopg2.extras", fake_extras)


# ---- Probe ---------------------------------------------------------

def _new_adapter_with_failing_count():
    adapter = PostgreSQLAdapter()
    cursor = _FakeCursor(fail_on_count=True)
    adapter._conn = _FakeConn(cursor)
    return adapter, cursor


@pytest.fixture(autouse=True)
def _patch_psycopg2(monkeypatch):
    _install_fake_psycopg2(monkeypatch)
    yield


def test_count_probe_failure_does_not_propagate():
    """(a) Fix-direction: the count-probe failure must not crash
    `fetch()`. Falls back to total=0 internally; the paginated query
    that follows must run cleanly because the SAVEPOINT cleared the
    aborted state."""
    adapter, cursor = _new_adapter_with_failing_count()

    # Should NOT raise — the fix recovers the transaction and the
    # paginated query proceeds.
    result = adapter.fetch(
        "SELECT * FROM gift_cards WHERE is_deleted = 0",
        params=None, limit=20, offset=0,
    )

    # count fell back to 0 (the bare-except path)
    assert result.count == 0, (
        f"Expected total=0 fallback after count-probe failure; got {result.count}"
    )
    # The count probe WAS attempted (look for the wrapped SQL)
    assert any("_count_subquery" in s for s in cursor.executed)


def test_fix_uses_savepoint_for_recovery():
    """(b) Fix-direction: the SAVEPOINT / ROLLBACK TO pattern is used
    to recover from a count-probe failure (mirroring the lastval
    probe fix at postgres.py:108-122 for issue #38)."""
    adapter, cursor = _new_adapter_with_failing_count()

    try:
        adapter.fetch(
            "SELECT * FROM gift_cards WHERE is_deleted = 0",
            params=None, limit=20, offset=0,
        )
    except Exception:
        pass  # we may or may not raise; only the SAVEPOINT trail matters

    sp_create = [s for s in cursor.executed if s.upper().startswith("SAVEPOINT")]
    sp_rollback = [s for s in cursor.executed
                   if s.upper().startswith("ROLLBACK TO SAVEPOINT")]

    assert sp_create, (
        "Expected at least one SAVEPOINT to be created around the "
        "count probe (mirroring the lastval-probe fix). Executed SQL "
        f"so far: {cursor.executed}"
    )
    assert sp_rollback, (
        "Expected a ROLLBACK TO SAVEPOINT after the count-probe "
        "failure to recover the transaction. Executed: "
        f"{cursor.executed}"
    )


def test_fix_emits_log_error_with_original_cause(capfd):
    """(c) Fix-direction: the count-probe failure must emit
    `Log.error` with the original cause in the structured payload.
    Closes the visibility gap from issue #46."""
    adapter, _ = _new_adapter_with_failing_count()

    try:
        adapter.fetch(
            "SELECT * FROM gift_cards WHERE is_deleted = 0",
            params=None, limit=20, offset=0,
        )
    except Exception:
        pass

    out, err = capfd.readouterr()
    stream = out + err

    error_lines = [
        ln for ln in stream.splitlines()
        if "[ERROR" in ln and "count probe" in ln.lower()
    ]
    assert error_lines, (
        "Expected an ERROR log line mentioning the count probe. "
        f"Captured stream tail: {stream[-400:]}"
    )
    joined = "\n".join(error_lines)
    assert "boolean = integer" in joined, (
        f"Original cause missing from log: {joined}"
    )


def test_fix_paginated_query_succeeds_after_savepoint_rollback():
    """(d) Fix-direction: after the SAVEPOINT recovers the aborted
    state, the paginated query that follows the count probe must
    run cleanly — no InFailedSqlTransaction cascade."""
    adapter, cursor = _new_adapter_with_failing_count()

    # No exception — paginated query reaches and completes.
    result = adapter.fetch(
        "SELECT * FROM gift_cards WHERE is_deleted = 0",
        params=None, limit=20, offset=0,
    )
    assert result is not None
    # The paginated SQL (with LIMIT) was reached.
    assert any("LIMIT" in s.upper() and "_count_subquery" not in s
               for s in cursor.executed), (
        f"Paginated query was not attempted. Executed: {cursor.executed}"
    )
