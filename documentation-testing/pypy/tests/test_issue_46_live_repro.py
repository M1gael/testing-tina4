# Probe — covers BH-46 (issue #46). Live PG reproduction of reporter's exact call shape.
# Live reproduction for tina4stack/tina4-python issue #46
# https://github.com/tina4stack/tina4-python/issues/46
#
# Goal: run the reporter's EXACT code path
#
#     GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])
#
# against a real PostgreSQL instance, capture the actual psycopg2
# error before the framework discards it, and confirm whether the
# user-visible "current transaction is aborted" message is what the
# bare-except in `PostgreSQLAdapter.fetch()` (postgres.py:148-152)
# turned the original cause into.
#
# Prerequisites (set up out-of-band, not in this file):
#   - PostgreSQL 18 running on localhost:5432
#   - User: postgres / Password: tina4test
#   - DB: tina4_bug46 (created)
#   - Table: gift_cards with is_deleted BOOLEAN NOT NULL — seeded
#   - psycopg2-binary installed in pypy/.venv
#
# Run:
#   uv run python -m pytest tests/test_issue_46_live_repro.py -v -s

import os
import sys
import pytest

# Skip cleanly if psycopg2 is not installed on this machine — the file
# is committed to the bug-hunting branch but should not break the
# normal pypy test suite on machines that don't have the live PG
# infrastructure.
psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2-binary not installed")
import psycopg2.errors

# Same skip-guard for the live PG connection itself.
def _pg_reachable() -> bool:
    try:
        c = psycopg2.connect(
            host="localhost", port=5432, user="postgres",
            password="tina4test", dbname="tina4_bug46",
            connect_timeout=2,
        )
        c.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pg_reachable(),
    reason="local PostgreSQL on 5432 with the tina4_bug46 fixture is not available",
)


# Import the model + framework WITHOUT touching TINA4_DATABASE_URL —
# polluting that env var leaks into the rest of the pypy test suite
# (other tests' `os.environ.setdefault(...)` becomes a no-op and they
# end up pointed at this PG fixture instead of SQLite).
from tina4_python.database import Database
# 3.13.30 renamed orm_bind -> bind_database; alias keeps call sites stable.
from tina4_python.orm import bind_database as orm_bind

PG_URL = "postgresql://postgres:tina4test@localhost:5432/tina4_bug46"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from orm.GiftCard import GiftCard


@pytest.fixture(autouse=True)
def _bind_pg():
    """Bind ORM models to a fresh PG Database for one test, then
    restore the previous global binding so the rest of the suite
    (which uses SQLite via test_*_setup_teardown.py et al.) is not
    polluted. `orm_bind(db)` writes a module-level global in
    tina4_python.orm.model — restore it explicitly in teardown."""
    import tina4_python.orm.model as orm_module

    prior_global = orm_module._database
    prior_giftcard_db = getattr(GiftCard, "_db", None)

    db = Database(url=PG_URL)
    orm_bind(db)
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass
        # Full restore: global default + the per-class override.
        orm_module._database = prior_global
        GiftCard._db = prior_giftcard_db


# ---- Tests ---------------------------------------------------------

REPORTER_EMAIL = "schalk@codeinfinity.co.za"


def test_baseline_sanity_psycopg2_direct():
    """Sanity check: a raw psycopg2 query against the same DB returns
    rows for the reporter's email. Confirms the fixture is intact and
    the email actually has gift cards to find."""
    conn = psycopg2.connect(
        host="localhost", port=5432, user="postgres",
        password="tina4test", dbname="tina4_bug46",
    )
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT count(*) FROM gift_cards WHERE created_by_email = %s AND is_deleted = FALSE",
            [REPORTER_EMAIL],
        )
        n = cur.fetchone()[0]
        assert n == 2, f"fixture expected 2 active cards for reporter, got {n}"
    finally:
        conn.close()


def test_raw_psycopg2_is_deleted_eq_zero_raises_operator_error():
    """The actual psycopg2 error the framework hides. Running the
    reporter's filter (`is_deleted = 0`) on a BOOLEAN column raises
    `UndefinedFunction: operator does not exist: boolean = integer`.

    This is what `PostgreSQLAdapter.fetch()`'s count probe encounters
    and swallows."""
    conn = psycopg2.connect(
        host="localhost", port=5432, user="postgres",
        password="tina4test", dbname="tina4_bug46",
    )
    try:
        cur = conn.cursor()
        with pytest.raises(psycopg2.errors.UndefinedFunction) as exc:
            cur.execute(
                "SELECT count(*) FROM gift_cards "
                "WHERE created_by_email = %s AND is_deleted = 0",
                [REPORTER_EMAIL],
            )
        msg = str(exc.value)
        assert "operator does not exist" in msg
        assert "boolean" in msg.lower() and "integer" in msg.lower(), msg
        print(f"\n[psycopg2 raw error] {msg.strip()}")
    finally:
        conn.close()


def test_orm_where_surfaces_original_cause_not_cascade():
    """Reporter's verbatim code path — `Model.where(...)` against a
    BOOLEAN column with `is_deleted = 0`.

    POST-FIX expectation (this is the regression sentinel):
        The error that surfaces is psycopg2's *original*
        `UndefinedFunction: operator does not exist: boolean =
        integer` — with line/column pointer at the failing filter.
        The user CAN see what actually went wrong.

    PRE-FIX behaviour (kept here as documentation of what the bug
    looked like): the count probe at postgres.py:148-152 swallowed
    the UndefinedFunction, leaving the connection in aborted state;
    the paginated query then raised `InFailedSqlTransaction` with
    *"current transaction is aborted, commands ignored until end of
    transaction block"*, and the original cause was lost.
    """
    raised = None
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception as e:
        raised = e

    assert raised is not None, (
        "Expected the framework to surface an exception (the SQL is "
        "still bad). If this passes silently, something has changed "
        "more than just the count-probe fix."
    )

    msg = str(raised)
    print(f"\n[framework-surfaced error] {type(raised).__name__}: {msg.strip()}")

    # Fix-direction: the original cause now reaches the caller.
    assert "operator does not exist" in msg, (
        "Expected the original psycopg2 UndefinedFunction cause to "
        f"be visible after the fix. Got: {msg}"
    )
    assert "boolean" in msg.lower() and "integer" in msg.lower(), (
        f"Expected `boolean = integer` type-mismatch detail. Got: {msg}"
    )

    # Regression sentinel: the cascade message must NOT be what
    # surfaces. If this assertion fails, the fix has regressed.
    assert "current transaction is aborted" not in msg, (
        "REGRESSION: the cascade message is back — the count-probe "
        "fix at postgres.py:148-152 has been reverted or broken. "
        f"Got: {msg}"
    )


def test_failure_logs_original_cause_with_sql_and_params(capfd):
    """Fix-direction: a Log.error line surfaces the original cause
    with sql + params context. Captures the visibility half of #46.

    Implementation note (v3.13.6 actual): the log fires via
    ``_on_query_error`` on the PAGINATED query, not the count probe.
    By the time the wrapper sees it, the count probe has already
    swallowed-and-rolled-back, the conn is clean, and the paginated
    query re-encounters the same underlying PG error. So the log line
    is emitted at paginated-query time. The user-visible outcome is
    the same: original cause + sql + params reach the log.

    ``tina4_python.debug.Log`` writes via direct ``print()`` to stdout
    (debug/__init__.py:418), not through stdlib ``logging``. So we
    use ``capfd`` (file-descriptor-level capture) rather than ``caplog``.
    """
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    out, err = capfd.readouterr()
    log_stream = out + err

    # Log.error wraps to multiple lines (LINE / HINT / structured
    # payload all follow the [ERROR] header). Check the full stream
    # rather than filtering to header lines only.
    assert "PostgreSQL query failed" in log_stream, (
        f"_on_query_error did not fire. Stream tail:\n{log_stream[-800:]}"
    )
    assert ("boolean = integer" in log_stream
            or "operator does not exist" in log_stream), (
        f"Original cause missing from log. Stream tail:\n{log_stream[-800:]}"
    )
    # sql + params structured payload (debug/__init__.py:400-401)
    assert '"sql":' in log_stream, (
        f"sql key missing from log. Stream tail:\n{log_stream[-800:]}"
    )
    assert REPORTER_EMAIL in log_stream, (
        f"params not in log. Stream tail:\n{log_stream[-800:]}"
    )


def test_db_last_error_does_not_capture_the_original_cause(_bind_pg):
    """`Database.execute()` stores `str(e)` in `self.last_error` on
    failure (connection.py:412-414) — but `Database.fetch()` does NOT.
    So even the framework's own "last_error" channel doesn't preserve
    the original UndefinedFunction. Confirms the visibility gap goes
    beyond `Log.*` calls — the framework simply doesn't have the
    information anywhere by the time the cascade surfaces."""
    # REFRAMED (BH-49 Gap 3 CLOSED on 3.13.39): Database.fetch() now captures
    # last_error, so get_error() returns the ORIGINAL cause after a failing
    # where() — previously None / cascade-only. Regression guard. (Original test
    # name kept for traceability.)
    db = _bind_pg  # the fixture's PG database

    assert db.get_error() is None  # clean to start

    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    err = db.get_error()
    print(f"\n[db.last_error after where()] {err!r}")
    assert err is not None, "Gap 3 regressed — fetch() failure no longer populates last_error"
    low = err.lower()
    assert (("boolean" in low and "integer" in low)
            or "operator does not exist" in low
            or "datatype" in low), f"last_error should carry the original cause, got: {err!r}"
