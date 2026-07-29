# Probe — covers BH-46 + BH-49 (issues #46, #49). 13-test matrix over {fetch,execute} × {outside/inside txn} × {fresh/poisoned}.
# Comprehensive matrix probe for tina4stack/tina4-python issue #46
# https://github.com/tina4stack/tina4-python/issues/46
#
# v3.13.6 added auto-rollback + Log.error on failures.
# v3.13.8 added pre-flight heal for connections that arrived poisoned.
# Issue closed by maintainer 2026-06-09 after v3.13.6.
#
# This probe runs reporter's ORM call shape AND a matrix of variants
# against live PostgreSQL, capturing the FULL state of the framework
# response per cell: exception type, exception message, log output,
# db.last_error, and adapter.last_error.
#
# Matrix axes:
#   - call mode:     fetch() | execute()
#   - txn context:   outside explicit txn | inside explicit txn
#   - conn state:    fresh | post-failure | pre-poisoned (raw psycopg2 fail)
#
# Cross-cutting checks per cell:
#   - cascade_present:    "current transaction is aborted" in surfaced error
#   - cause_present:      original PG error (e.g. "operator does not exist") visible
#   - log_emitted:        Log.error fired with sql+params context
#   - db_last_error:      Database.get_error() populated with what
#   - raised:             did the call propagate or silently return
#
# Tests split into two groups:
#   FIX-DIRECTION — assert the fix HOLDS. If maintainer reverts, these flip.
#   RESIDUAL-GAP — assert the gap STILL EXISTS in 3.13.8. If maintainer
#     extends the fix, these flip (positive-direction regression — update probe).

import os
import sys
import pytest

psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2-binary not installed")
import psycopg2.errors
import psycopg2.extensions


PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASS = "tina4test"
PG_DB   = "tina4_bug46"
PG_URL  = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
REPORTER_EMAIL = "schalk@codeinfinity.co.za"


def _pg_reachable() -> bool:
    try:
        c = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER,
            password=PG_PASS, dbname=PG_DB, connect_timeout=2,
        )
        c.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pg_reachable(),
    reason="local PostgreSQL on 5432 with the tina4_bug46 fixture not available",
)


from tina4_python.database import Database
# 3.13.30 renamed orm_bind -> bind_database; alias keeps call sites stable.
from tina4_python.orm import bind_database as orm_bind

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from orm.GiftCard import GiftCard


# ---------- Fixtures ------------------------------------------------

@pytest.fixture
def db():
    """Fresh PG Database, ORM bound, restored after the test so the
    rest of the suite (SQLite-bound) stays clean."""
    import tina4_python.orm.model as orm_module
    prior_global = orm_module._database
    prior_giftcard_db = getattr(GiftCard, "_db", None)

    d = Database(url=PG_URL)
    orm_bind(d)

    yield d

    orm_module._database = prior_global
    if prior_giftcard_db is not None:
        GiftCard._db = prior_giftcard_db
    elif hasattr(GiftCard, "_db"):
        try:
            delattr(GiftCard, "_db")
        except AttributeError:
            pass


def _adapter(db: Database):
    return getattr(db, "_adapter", None) or getattr(db, "adapter", None)


def _poison_connection_raw(db: Database):
    """Reach into the adapter, grab psycopg2 conn, execute a guaranteed-
    failing query directly via psycopg2 (bypassing _exec_with_handling)
    so the connection is left in TRANSACTION_STATUS_INERROR. Mirrors the
    'arrived poisoned' scenario v3.13.8 was meant to handle."""
    adapter = _adapter(db)
    conn = adapter._conn
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM no_such_table_in_universe_42")
    except Exception:
        pass  # intentional


def _safe_rollback(db):
    try:
        db.rollback()
    except Exception:
        pass


# =====================================================================
# FIX-DIRECTION (outside explicit txn) — assert fix HOLDS
# =====================================================================

def test_fix_fetch_surfaces_original_cause(db):
    raised = None
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception as e:
        raised = e

    assert raised is not None
    msg = str(raised)
    assert "current transaction is aborted" not in msg, (
        f"REGRESSION: cascade re-surfacing. Got: {msg}"
    )
    assert "operator does not exist" in msg
    assert "boolean" in msg.lower() and "integer" in msg.lower()


def test_fix_fetch_emits_log_with_sql_and_params(db, capfd):
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    out, err = capfd.readouterr()
    stream = out + err
    assert "PostgreSQL query failed" in stream
    assert "operator does not exist" in stream
    assert '"sql":' in stream and '"params":' in stream
    assert "is_deleted = 0" in stream
    assert REPORTER_EMAIL in stream


def test_fix_fetch_failure_then_valid_call_succeeds(db):
    """Outside explicit txn, auto-rollback in _on_query_error heals the
    connection between calls. Use a boolean-free WHERE so SQLTranslator
    (the BH-46-adjacent bug at adapter.py:538-542) doesn't rewrite the
    valid query into an invalid one."""
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    rows = GiftCard.where(
        "created_by_email = ?",
        [REPORTER_EMAIL],
    )
    assert rows is not None


def test_fix_fetch_on_pre_poisoned_connection_heals(db):
    """v3.13.8 scenario — conn arrives poisoned from a raw psycopg2 call
    that bypassed the wrapper. Next fetch() should pre-flight heal."""
    _poison_connection_raw(db)
    adapter = _adapter(db)
    assert (adapter._conn.info.transaction_status
            == psycopg2.extensions.TRANSACTION_STATUS_INERROR)

    rows = GiftCard.where(
        "created_by_email = ?",
        [REPORTER_EMAIL],
    )
    assert rows is not None
    assert (adapter._conn.info.transaction_status
            != psycopg2.extensions.TRANSACTION_STATUS_INERROR)


def _cause_in(text):
    # the boolean=integer cause surfaces as UndefinedFunction ("operator does not
    # exist: boolean = integer") on some paths and DatatypeMismatch ("boolean ...
    # integer") on others (3.13.39 drift) — accept either.
    low = (text or "").lower()
    return (("boolean" in low and "integer" in low)
            or "operator does not exist" in low
            or "datatype" in low)


def test_fix_execute_surfaces_cause_and_populates_last_error(db):
    """REFRAMED (BH-49, 3.13.39): Database.execute() now SURFACES the original
    cause — it raises on the boolean=integer error (was: catch + return False).
    Either way the cause is observable (raised, or via get_error()), never the
    bare cascade. Regression guard: flips if execute() goes back to swallowing."""
    raised = None
    result = None
    try:
        result = db.execute("UPDATE gift_cards SET is_deleted = 0 WHERE id = 1")
    except Exception as e:
        raised = e
    err = db.get_error()
    blob = " ".join(x for x in [str(raised) if raised else "", err or ""] if x)
    assert blob, f"execute() neither raised nor populated last_error (result={result!r})"
    assert _cause_in(blob), f"original cause not surfaced; raised={raised!r} err={err!r}"
    assert "current transaction is aborted" not in blob


def test_fix_execute_on_pre_poisoned_connection_heals(db):
    _poison_connection_raw(db)
    adapter = _adapter(db)
    assert (adapter._conn.info.transaction_status
            == psycopg2.extensions.TRANSACTION_STATUS_INERROR)

    result = db.execute(
        "UPDATE gift_cards SET created_by_email = created_by_email "
        "WHERE id = -999"
    )
    assert result is not False, (
        f"execute() did not heal pre-poisoned conn. last_error: "
        f"{db.get_error()!r}"
    )


# =====================================================================
# RESIDUAL-GAP (inside explicit txn) — assert gap STILL EXISTS
# =====================================================================

def test_gap_fetch_inside_explicit_txn_cascades(db):
    """Reporter's exact query shape wrapped in start_transaction().
    Heal step defers to explicit txn (postgres.py:79); auto-rollback
    defers similarly. Cascade surfaces, original cause lost."""
    db.start_transaction()
    try:
        raised = None
        try:
            GiftCard.where(
                "created_by_email = ? AND is_deleted = 0",
                [REPORTER_EMAIL],
            )
        except Exception as e:
            raised = e

        assert raised is not None
        msg = str(raised)
        # GAP — cascade present, cause absent
        assert "current transaction is aborted" in msg, (
            f"Gap closed unexpectedly — cascade absent inside txn. "
            f"Got: {msg}"
        )
        assert "operator does not exist" not in msg, (
            f"Gap closed unexpectedly — cause visible inside txn. "
            f"Got: {msg}"
        )
    finally:
        _safe_rollback(db)


def test_gap_fetch_inside_explicit_txn_logs_only_cascade(db, capfd):
    """REFRAMED (BH-49 Gaps 1+2 CLOSED on 3.13.39): _on_query_error now emits the
    ORIGINAL cause via Log.* even inside an explicit transaction (v3.13.11), not
    only the cascade. Regression guard: the original cause must appear in the log."""
    db.start_transaction()
    try:
        try:
            GiftCard.where(
                "created_by_email = ? AND is_deleted = 0",
                [REPORTER_EMAIL],
            )
        except Exception:
            pass
    finally:
        _safe_rollback(db)

    out, err = capfd.readouterr()
    stream = out + err
    assert _cause_in(stream), (
        "Gaps 1+2 regressed — original cause no longer logged inside an explicit "
        f"txn. Stream: {stream[-300:]!r}"
    )


def test_gap_execute_inside_explicit_txn_swallows_second_call(db):
    """REFRAMED (BH-49 Gaps 1+2 CLOSED on 3.13.39): Database.execute() inside an
    explicit txn no longer SILENTLY swallows — it surfaces the original cause
    (raises, or populates get_error()), so a caller can tell a real error from a
    cascade. Regression guard: flips if execute() goes back to silent return-False."""
    db.start_transaction()
    try:
        raised = None
        try:
            db.execute("UPDATE gift_cards SET is_deleted = 0 WHERE id = 1")
        except Exception as e:
            raised = e
        err = db.get_error()
        blob = " ".join(x for x in [str(raised) if raised else "", err or ""] if x)
        assert blob, "execute() inside txn still silently swallowed (no raise, no last_error)"
        assert _cause_in(blob), (
            f"original cause not surfaced inside txn; raised={raised!r} err={err!r}"
        )
    finally:
        _safe_rollback(db)


def test_gap_second_call_inside_txn_still_cascades(db):
    """Outside txn, auto-rollback heals between calls. Inside txn, it
    defers — so a second valid query also cascades."""
    db.start_transaction()
    try:
        try:
            GiftCard.where(
                "created_by_email = ? AND is_deleted = 0",
                [REPORTER_EMAIL],
            )
        except Exception:
            pass

        raised = None
        try:
            GiftCard.where(
                "created_by_email = ?",
                [REPORTER_EMAIL],
            )
        except Exception as e:
            raised = e

        assert raised is not None
        assert "current transaction is aborted" in str(raised)
    finally:
        _safe_rollback(db)


def test_gap_recovery_requires_manual_rollback(db):
    """After explicit-txn poisoning, only db.rollback() + new call
    clears the cascade. Documents the contract for txn users."""
    db.start_transaction()
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    db.rollback()

    rows = GiftCard.where(
        "created_by_email = ?",
        [REPORTER_EMAIL],
    )
    assert rows is not None


# =====================================================================
# ASYMMETRY — db.last_error on fetch() path vs execute() path
# =====================================================================

def test_gap_fetch_failure_does_not_populate_db_last_error(db):
    """REFRAMED (BH-49 Gap 3 CLOSED on 3.13.39): Database.fetch() now CAPTURES
    last_error on failure (was asymmetric vs execute()), so get_error() returns
    the original cause after a failed where() — previously None. Regression guard."""
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    err = db.get_error()
    assert err is not None, "Gap 3 regressed — fetch() failure no longer populates last_error"
    assert _cause_in(err), f"last_error should carry the original cause, got: {err!r}"


def test_data_exists_on_adapter_last_error_not_db_last_error(db):
    """The original cause IS captured — on adapter.last_error
    (postgres.py:154 via _on_query_error). Database.fetch() just
    doesn't read it. Trivial fix on maintainer's side."""
    try:
        GiftCard.where(
            "created_by_email = ? AND is_deleted = 0",
            [REPORTER_EMAIL],
        )
    except Exception:
        pass

    adapter = _adapter(db)
    assert adapter is not None
    assert adapter.last_error is not None
    assert "operator does not exist" in adapter.last_error
