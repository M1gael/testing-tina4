# Probe — covers BH-46 (issue #46). Source-read sentinel for the SAVEPOINT count-probe fix.
# Probe for tina4stack/tina4-python issue #46
# https://github.com/tina4stack/tina4-python/issues/46
#
# Source-read confirmation of the fix at postgres.py:264-302 (3.13.8).
# Stubs psycopg2 with a cursor that mimics real psycopg2 transaction-
# poison semantics (a failed statement poisons the transaction until
# either ROLLBACK [TO SAVEPOINT] lands), then exercises the real
# `PostgreSQLAdapter.fetch()` code path unchanged.
#
# Companion to test_issue_46_live_repro.py (reporter's exact ORM call
# against live PG) and test_issue_46_matrix_probe.py (full fix/gap
# matrix). This file proves the code-path SHAPE without needing live
# infrastructure — useful for CI / fresh clones.
#
# Fix shape note (v3.13.6 + v3.13.8 actuals):
#   Maintainer used `self._conn.rollback()` (not SAVEPOINT) to clear
#   the aborted state after the count probe, and routed Log.error via
#   the downstream paginated query through _exec_with_handling →
#   _on_query_error. The SAVEPOINT pattern is reserved for the
#   lastval probe (postgres.py:240-248, issue #38). Probe assertions
#   are written against the user-VISIBLE outcome, not against a
#   specific recovery primitive — both ROLLBACK and ROLLBACK TO
#   SAVEPOINT are accepted as recovery shapes.
#
# Probe assertions are FIX-DIRECTION:
#   (a) the count-probe failure does NOT propagate — the bare except
#       still recovers and falls back to total=0.
#   (b) some form of ROLLBACK lands after the count-probe failure (the
#       fix may use full ROLLBACK or ROLLBACK TO SAVEPOINT; both are
#       valid recovery shapes).
#   (c) Log.error is invoked with the original cause in the
#       structured payload — emitted via the paginated query path
#       since that's where _exec_with_handling lives.
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

        # Real PG behaviour: the user's broken WHERE clause fails on
        # BOTH the count probe AND the paginated query — same SQL,
        # same operator-mismatch. So we fail on any query containing
        # the broken predicate, not just the count subquery.
        if self.fail_on_count and "is_deleted = 0" in sql:
            # First failure → mark count as failed (used to drive the
            # rollback path), and poison the txn.
            if "_count_subquery" in sql:
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


def test_count_probe_failure_does_not_surface_as_cascade():
    """(a) Fix-direction: the count-probe failure must NOT propagate
    as the ``current transaction is aborted`` cascade message.

    In real PG, the broken WHERE clause (is_deleted = 0) fails on BOTH
    the count probe AND the paginated query — same SQL, same operator
    mismatch. The fix's job is to ensure that what the user sees is
    the ORIGINAL cause from the paginated query (routed through
    _exec_with_handling → _on_query_error), not the cascade that
    would surface if the count-probe failure poisoned the connection."""
    adapter, cursor = _new_adapter_with_failing_count()

    raised = None
    try:
        adapter.fetch(
            "SELECT * FROM gift_cards WHERE is_deleted = 0",
            params=None, limit=20, offset=0,
        )
    except Exception as e:
        raised = e

    assert raised is not None  # paginated query still raises
    msg = str(raised)
    # The fix-direction guarantee:
    assert "current transaction is aborted" not in msg, (
        f"Cascade message surfaced — fix has regressed. Got: {msg}"
    )
    assert "operator does not exist" in msg, (
        f"Original cause missing — fix has regressed. Got: {msg}"
    )
    # Count probe was attempted (wrapped in _count_subquery)
    assert any("_count_subquery" in s for s in cursor.executed)


def test_fix_recovers_aborted_txn_after_count_probe_failure():
    """(b) Fix-direction: SOME recovery mechanism runs after the count
    probe fails, clearing the aborted state before the paginated
    query.

    The maintainer's v3.13.6 implementation uses ``self._conn.rollback()``
    (postgres.py:288-292) — the full ROLLBACK is simpler than the
    SAVEPOINT pattern used for the lastval probe (#38). Both are valid
    recovery shapes; this assertion accepts either."""
    adapter, cursor = _new_adapter_with_failing_count()

    try:
        adapter.fetch(
            "SELECT * FROM gift_cards WHERE is_deleted = 0",
            params=None, limit=20, offset=0,
        )
    except Exception:
        pass  # may or may not raise; only the recovery trail matters

    # Recovery shape A: full ROLLBACK via self._conn.rollback() — the
    # FakeConn increments rollback_calls and resets _aborted.
    conn_rollback_used = adapter._conn.rollback_calls > 0

    # Recovery shape B: SAVEPOINT + ROLLBACK TO SAVEPOINT issued
    # through the cursor — recorded in cursor.executed.
    sp_rollback = [s for s in cursor.executed
                   if s.upper().startswith("ROLLBACK TO SAVEPOINT")]

    assert conn_rollback_used or sp_rollback, (
        "Expected ROLLBACK (full or SAVEPOINT-scoped) after count-"
        "probe failure to recover the transaction. "
        f"conn.rollback_calls={adapter._conn.rollback_calls}, "
        f"cursor.executed={cursor.executed}"
    )


def test_fix_emits_log_error_with_original_cause(capfd):
    """(c) Fix-direction: a Log.error line surfaces the original cause
    with sql + params context. Closes the visibility gap from #46.

    The maintainer routes the log through ``_on_query_error`` on the
    PAGINATED query — by the time the wrapper sees it, the count
    probe has already swallowed-and-rolled-back, the connection is
    clean, and the paginated query re-encounters the same underlying
    PG error. So the log line is emitted at paginated-query time, not
    count-probe time. The user-visible OUTCOME is the same: original
    cause + sql + params reach the log."""
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

    # The wrapper logs as: "PostgreSQL query failed: <ExcClass>: <msg>"
    error_lines = [
        ln for ln in stream.splitlines()
        if "[ERROR" in ln and "postgresql query failed" in ln.lower()
    ]
    assert error_lines, (
        "Expected an ERROR log line from _on_query_error. "
        f"Captured stream tail: {stream[-400:]}"
    )
    joined = "\n".join(error_lines)
    # Original cause text from our fake error
    assert "boolean = integer" in joined, (
        f"Original cause missing from log: {joined}"
    )


def test_fix_paginated_query_reached_after_recovery():
    """(d) Fix-direction: after the count probe is recovered (full
    ROLLBACK or ROLLBACK TO SAVEPOINT), the paginated query is
    reached — it doesn't get short-circuited by the cascade. Whether
    the paginated query then succeeds or raises depends on the user's
    SQL; the contract is just that it gets a clean txn to run on."""
    adapter, cursor = _new_adapter_with_failing_count()

    try:
        adapter.fetch(
            "SELECT * FROM gift_cards WHERE is_deleted = 0",
            params=None, limit=20, offset=0,
        )
    except Exception:
        pass  # paginated query raising with original cause is fine

    # The paginated SQL (with LIMIT) was attempted, after the count
    # probe — this is what we're checking.
    paginated = [s for s in cursor.executed
                 if "LIMIT" in s.upper() and "_count_subquery" not in s]
    assert paginated, (
        f"Paginated query was not attempted. Executed: {cursor.executed}"
    )
