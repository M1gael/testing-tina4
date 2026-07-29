# Probe — covers BH-46 (issue #46). Adversarial sentinel for the drafted fix patches.
# Adversarial tests for the DRAFTED issue #46 patches at
# `bug-hunting/fix-issue-46-patches/`. The drafted fix had three
# patches:
#   (1) postgres.py:148-152 — wrap count probe in SAVEPOINT, log
#       Log.error with original cause on failure.
#   (2) connection.py:412-414 — Log.error on Database.execute() failure.
#   (3) model.py:336/364/384/405 — Log.error on ORM save/delete/
#       force_delete/restore failure paths.
#
# IMPORTANT: maintainer SHIPPED a DIFFERENT fix shape in v3.13.6 +
# v3.13.8 (see bug-hunting/issue-46-pg-silent-abort.md):
#   - Count probe: full self._conn.rollback() instead of SAVEPOINT
#   - Log routing: through new _exec_with_handling wrapper, fires on
#     paginated query path, not count-probe path
#   - ORM-layer Log.error (drafted patch 3): NOT shipped — ORM still
#     swallows silently
#   - Inside-explicit-txn auto-rollback: DEFERS by design
#
# So 4 of the 10 assertions below check patch-specific shapes that
# maintainer chose not to ship. Those are marked xfail with a pointer
# to `test_issue_46_matrix_probe.py` which captures the canonical
# post-fix behaviour empirically.
#
# Each remaining test runs against the LIVE PostgreSQL fixture
# (tina4_bug46) so the assertions exercise real psycopg2 semantics,
# not a mock. Skipped automatically when psycopg2 / PG is unavailable.

import os
import sys
import pytest

psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2-binary not installed")
import psycopg2.errors


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


from tina4_python.database import Database
# 3.13.30 renamed orm_bind -> bind_database; alias keeps call sites stable.
from tina4_python.orm import bind_database as orm_bind

PG_URL = "postgresql://postgres:tina4test@localhost:5432/tina4_bug46"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from orm.GiftCard import GiftCard


@pytest.fixture(autouse=True)
def _bind_pg():
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
        orm_module._database = prior_global
        GiftCard._db = prior_giftcard_db


# ── ATTACK 1: connection survives across multiple poisoned queries ──

def test_attack_repeated_failures_dont_compound(_bind_pg):
    """Hostile pattern: caller hammers the same broken filter
    repeatedly. Pre-fix this would leave the conn permanently
    aborted. Post-fix every failure must recover cleanly — the
    SAVEPOINT path must not leak state across calls."""
    for i in range(5):
        try:
            GiftCard.where("is_deleted = 0", [])  # BOOLEAN = integer
        except psycopg2.errors.UndefinedFunction:
            pass  # expected

    # After 5 poisoned attempts a VALID query must still succeed.
    cards = GiftCard.where("NOT is_deleted", [])
    assert len(cards) >= 1, (
        "After repeated failures the connection should still be "
        "usable. If not, the SAVEPOINT recovery is leaking aborted "
        "state across fetch() calls."
    )


# ── ATTACK 2: failure interleaved with successful queries ──────────

def test_attack_alternating_pass_fail(_bind_pg):
    """Even nastier shape — successful query, failed query, successful
    query. The fix must not corrupt the state of the conn between
    calls."""
    ok1 = GiftCard.where("NOT is_deleted", [])
    assert len(ok1) >= 1

    try:
        GiftCard.where("is_deleted = 0", [])
    except psycopg2.errors.UndefinedFunction:
        pass

    ok2 = GiftCard.where("NOT is_deleted", [])
    assert len(ok2) == len(ok1), (
        "Result set changed between two identical valid queries "
        "across a failed one — connection state was corrupted by "
        "the SAVEPOINT path."
    )


# ── ATTACK 3: failure inside an explicit user transaction ──────────

@pytest.mark.xfail(
    reason="Maintainer's v3.13.6+v3.13.8 fix defers inside explicit txn by "
           "design (postgres.py:127-130). Drafted patch behaviour not shipped. "
           "See test_gap_fetch_inside_explicit_txn_cascades in matrix probe.",
    strict=False,
)
def test_attack_failure_inside_user_transaction(_bind_pg):
    """Caller has called db.start_transaction() before the failing
    fetch. The SAVEPOINT must NEST inside the user txn, not commit
    or rollback the outer txn implicitly. After recovery, the user
    must still be able to commit or rollback their own txn."""
    db = _bind_pg
    db.start_transaction()
    try:
        try:
            GiftCard.where("is_deleted = 0", [])
        except psycopg2.errors.UndefinedFunction:
            pass  # expected — the outer txn should still be alive

        # Run an INSERT inside the still-alive outer txn. If the
        # SAVEPOINT path had implicitly rolled back the user txn,
        # this would either fail or be in autocommit-shape.
        # NB: write `FALSE::boolean` so the framework's
        # `boolean_to_int` SQL translator can rewrite FALSE→0 and
        # the resulting `0::boolean` is still valid PG (adjacent
        # translator finding; doesn't change the assertion shape).
        row = db.fetch_one(
            "INSERT INTO gift_cards (created_by_email, amount, is_deleted) "
            "VALUES ('adv-test@example.com', 1.00, FALSE::boolean) RETURNING id"
        )
        assert row is not None and row.get("id") is not None
        new_id = row["id"]

        # Now the user explicitly rolls back. The INSERT must be undone.
        db.rollback()

        # Verify the insert was undone (proves the outer txn was real).
        check = db.fetch_one(
            "SELECT id FROM gift_cards WHERE id = %s", [new_id]
        )
        assert check is None, (
            "User-driven transaction was not honoured — the INSERT "
            "survived a rollback(), meaning the SAVEPOINT fix broke "
            "outer-transaction semantics."
        )
    except Exception:
        # If anything else went wrong, attempt to rollback to keep
        # the connection clean for later tests in this module.
        try:
            db.rollback()
        except Exception:
            pass
        raise


# ── ATTACK 4: SAVEPOINT name collision ──────────────────────────────

@pytest.mark.xfail(
    reason="Maintainer chose full conn.rollback() instead of SAVEPOINT for "
           "count probe (postgres.py:288-292), so no savepoint name to "
           "clash with at the count-probe site. Lastval probe still uses "
           "fixed name _t4_lastval_probe (postgres.py:240-248).",
    strict=False,
)
def test_attack_savepoint_name_does_not_clash_with_user_savepoint(_bind_pg):
    """If the user has their own SAVEPOINT named `_t4_count_probe`,
    the framework's SAVEPOINT must not stomp on it. Probe via raw
    SQL since the framework doesn't expose savepoints."""
    db = _bind_pg
    db.start_transaction()
    try:
        # User establishes their own savepoint with the SAME name
        # to maximise collision risk.
        db.adapter._conn.cursor().execute("SAVEPOINT _t4_count_probe")

        try:
            GiftCard.where("is_deleted = 0", [])
        except psycopg2.errors.UndefinedFunction:
            pass

        # The user can still rollback to their own savepoint —
        # which would fail if the framework had RELEASEd it.
        cur = db.adapter._conn.cursor()
        try:
            cur.execute("ROLLBACK TO SAVEPOINT _t4_count_probe")
            user_sp_alive = True
        except psycopg2.errors.InvalidSavepointSpecification:
            user_sp_alive = False

        # This is informational — the current fix DOES use the same
        # name so a collision is expected to break the user's SP. We
        # record the finding rather than asserting strict isolation.
        # (The upstream fix could use a unique-per-call name to
        # eliminate this — left as a suggestion in the patch notes.)
        print(f"\n[savepoint collision] user SP after framework SP: "
              f"{'alive' if user_sp_alive else 'released by framework'}")
    finally:
        try:
            db.rollback()
        except Exception:
            pass


# ── ATTACK 5: Log payload doesn't leak credentials ──────────────────

def test_attack_log_does_not_leak_credentials(_bind_pg, capfd):
    """The Log.error call serialises the `sql` parameter. If the SQL
    string ever contained credentials (it shouldn't — params are
    bound separately on psycopg2), the log would leak. Verify the
    log line for the standard failure path doesn't contain the
    password."""
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            ["schalk@codeinfinity.co.za"],
        )
    except Exception:
        pass

    out, err = capfd.readouterr()
    stream = out + err

    # The PG_URL contains the password. The Log payload must not.
    assert "tina4test" not in stream, (
        "Credentials leaked into the log payload! This is the "
        "exact PII risk that motivated the careful Log payload "
        f"design. Stream:\n{stream}"
    )


# ── ATTACK 6: Long SQL doesn't break the log payload ────────────────

@pytest.mark.xfail(
    reason="Drafted patch logged full SQL; maintainer's _on_query_error "
           "truncates to first line, 200 chars (postgres.py:145). Test "
           "asserts against drafted-patch log content shape.",
    strict=False,
)
def test_attack_long_sql_does_not_crash_log(_bind_pg, capfd):
    """A failing query with a huge IN-list or repeated clauses must
    still produce a parseable log line — Log shouldn't truncate or
    crash on long payloads."""
    big_filter = " OR ".join(["is_deleted = 0"] * 50)
    try:
        GiftCard.where(big_filter, [])
    except Exception:
        pass

    out, err = capfd.readouterr()
    stream = out + err
    assert "[ERROR" in stream
    assert "count probe" in stream.lower()
    # Log line should NOT contain any traceback (Log.error is a
    # plain log call, not exception_info).
    assert "Traceback" not in stream, (
        "Log.error should not emit a stack trace — just the message "
        "+ structured payload."
    )


# ── ATTACK 7: ORM.save() failure logs cause + still returns False ──

@pytest.mark.xfail(
    reason="Drafted patch 3 added Log.error('ORM.save() failed', ...) — not "
           "shipped. ORM layer still swallows silently. Adapter does emit "
           "'PostgreSQL query failed' via _on_query_error, but the test "
           "specifically checks the ORM-layer wording.",
    strict=False,
)
def test_attack_orm_save_logs_violation_and_returns_false(_bind_pg, capfd):
    """save() contract: rollback + return False, never raise. The
    fix added a Log.error before the return — must NOT have
    accidentally promoted to a raise."""
    # Force a NOT NULL violation: amount is NOT NULL on the schema.
    gc = GiftCard()
    gc.created_by_email = "adv-save-test@example.com"
    gc.amount = None  # violates NOT NULL — INSERT will fail

    result = gc.save()

    # Contract: returns False (not raises, not None).
    assert result is False, (
        f"save() must return False on failure (contract). Got: {result!r}"
    )

    out, err = capfd.readouterr()
    assert "ORM.save() failed" in out + err, (
        "save() failure must emit a Log.error mentioning ORM.save."
    )


# ── ATTACK 8: paginated query failure (not count probe) propagates ──

def test_attack_paginated_query_failure_still_propagates(_bind_pg):
    """The fix is targeted at the COUNT PROBE. If the paginated
    query itself fails (count succeeded, then pagination broke
    somehow), the framework must still raise — not silently swallow.
    Trigger: missing column referenced only in the OUTER select,
    so count(*) wrapping doesn't expose it but the paginated
    SELECT * does."""
    # Both queries reference the same SQL, so this is hard to
    # exercise cleanly. Approximation: a syntactically-valid filter
    # that fails on the paginated query specifically would require
    # a different SQL between the two — the framework's fetch
    # doesn't allow that. So we instead confirm a hard error in
    # the SELECT (bad table) still propagates.
    with pytest.raises(psycopg2.errors.UndefinedTable):
        # This bypasses ORM and goes straight through db.fetch
        # via the model — but since we don't have a where() that
        # talks to an arbitrary table, exercise it through raw SQL.
        _bind_pg.fetch("SELECT * FROM table_that_does_not_exist")


# ── ATTACK 9: Log call import-failure must not break data path ──────

def test_attack_log_import_failure_does_not_propagate(_bind_pg, monkeypatch):
    """The fix wraps the `from tina4_python.debug import Log` in a
    try/except. If Log is broken or missing, the data path must
    still work."""
    import tina4_python.debug as debug_mod

    # Sabotage Log.error to raise (simulating a broken/missing Log).
    original_error = debug_mod.Log.error
    def broken_error(*args, **kwargs):
        raise RuntimeError("Log is on fire")
    monkeypatch.setattr(debug_mod.Log, "error", broken_error)

    # The fetch() call should still recover from the count probe
    # — the data path must not blow up because logging blew up.
    try:
        GiftCard.where("created_by_email = ? AND is_deleted = 0",
                       ["schalk@codeinfinity.co.za"])
    except psycopg2.errors.UndefinedFunction:
        pass  # expected — the paginated query still raises the real cause
    except RuntimeError as e:
        if "Log is on fire" in str(e):
            pytest.fail(
                "Logging failure escaped into the data path! The "
                "Log.error call inside the except block must be "
                "wrapped in its own try/except."
            )
        raise

    # Restore so other tests in this session aren't affected
    # (autouse fixture restoration would also do this).
    monkeypatch.setattr(debug_mod.Log, "error", original_error)


# ── ATTACK 10: very large total via the count-probe fallback ──────

def test_attack_count_fallback_total_zero_doesnt_lie_for_normal_queries(_bind_pg):
    """The fix falls back to `total = 0` when the count probe fails.
    Normal (non-failing) queries must still report the correct
    count — the SAVEPOINT shouldn't accidentally trigger the
    fallback when the probe succeeds."""
    cards, total = GiftCard.where("NOT is_deleted", [], with_count=True)
    assert total >= 2, (
        f"Expected real count from successful count probe. Got "
        f"total={total} which suggests the SAVEPOINT path is "
        "always firing the fallback."
    )
    assert total == len(cards) or total >= len(cards), (
        "Pagination total must be >= len(records) on a non-paginated "
        "query."
    )
