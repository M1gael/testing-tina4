# Issue #46 — No database error visibility

**Upstream:** https://github.com/tina4stack/tina4-python/issues/46
**Reporter:** SchalkAB13711
**Framework version under test:** tina4-python 3.13.4 (`pypy/.venv`)
**Status:** root cause confirmed, probe passes (`pypy/tests/test_issue_46_pg_silent_abort_probe.py`)

---

## Reporter's symptom

The first ORM call (`GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])`)
returns the error string

```
current transaction is aborted, commands ignored until end of transaction block
```

No log entry shows what actually failed first.

## Root cause

`PostgreSQLAdapter.fetch()` (`tina4_python/database/postgres.py:138-160`)
runs a `COUNT(*)` probe before the paginated query:

```python
# postgres.py:138-160 (verbatim)
def fetch(self, sql: str, params: list = None,
          limit: int = 100, offset: int = 0) -> DatabaseResult:
    import psycopg2.extras

    sql = self._translate_sql(sql)

    cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Count total rows
    count_sql = f"SELECT COUNT(*) AS cnt FROM ({sql}) AS _count_subquery"
    try:
        self._safe_execute(cursor, count_sql, params)
        total = cursor.fetchone()["cnt"]
    except Exception:                  # <-- L151
        total = 0                       # <-- L152: bare swallow, no rollback, no log

    # Apply pagination
    paginated_sql = f"{sql} LIMIT %s OFFSET %s"
    paginated_params = (params or []) + [limit, offset]
    self._safe_execute(cursor, paginated_sql, paginated_params)
    rows = [self._decode_blobs(dict(row)) for row in cursor.fetchall()]

    return DatabaseResult(...)
```

When `count_sql` raises on PostgreSQL — e.g. the reporter's
`is_deleted = 0` is a type mismatch on a `BOOLEAN` column, raising
`operator does not exist: boolean = integer` — the `except Exception`
on line 151 swallows the error. The connection (opened with
`self._conn.autocommit = False` at `postgres.py:70`) is now in
*aborted* state per psycopg2 semantics.

The very next line then runs the paginated SQL on the same cursor.
psycopg2 raises `InFailedSqlTransaction` with the message *"current
transaction is aborted, commands ignored until end of transaction
block"*. That exception propagates up — `Database.fetch()`
(`connection.py:422-439`) does not wrap it, `Model.where()`
(`orm/model.py:599-635`) does not wrap it, so it surfaces to the
reporter's `try/except Exception as e` and reaches the log as the
cascade message. The original `boolean = integer` cause is gone.

## Adjacent context — the framework already knows about this pattern

The lastval probe a few lines up (`postgres.py:99-122`) explicitly
guards against the same cascade with a SAVEPOINT:

```python
# postgres.py:108-122 (verbatim, abbreviated)
# Fix: wrap the probe in a SAVEPOINT. If ``lastval()`` raises, we
# ROLLBACK TO SAVEPOINT and the outer transaction stays usable;
# ``last_id`` just stays ``None`` (same as before for non-INSERT
# statements). On success we RELEASE SAVEPOINT.
sql_upper = sql.strip().upper()
if sql_upper.startswith("INSERT"):
    cursor.execute("SAVEPOINT _t4_lastval_probe")
    try:
        cursor.execute("SELECT lastval()")
        ...
        cursor.execute("RELEASE SAVEPOINT _t4_lastval_probe")
    except Exception:
        cursor.execute("ROLLBACK TO SAVEPOINT _t4_lastval_probe")
```

This patch landed for upstream issue #38. The same fix shape — and
the same rationale — is needed at lines 148-152 for the count probe.
It has not been applied there.

## Adjacent leaks (same class of defect)

| File:Line | Symptom |
|---|---|
| `connection.py:412-414` | `Database.execute()` catches all `Exception`, stores `str(e)` in `last_error`, returns `False`. No `self.rollback()` call. On PG, every write that fails leaves the connection in aborted state. |
| `orm/model.py:336-338` | `ORM.save()` catches all `Exception`, calls `db.rollback()`, returns `False`. Recovers the transaction but emits no log — caller cannot tell *what* failed, only that `save()` returned `False`. |

A grep for `Log\.` (the framework's own logger, `tina4_python.debug.Log`)
across `tina4_python/database/` and `tina4_python/orm/` returns **zero
matches**. The entire DB + ORM layer has no structured logging on
the swallow paths. This is the visibility half of the issue.

## Empirical confirmation

Two layers of evidence: a mock-cursor probe that proves the
framework's code path independent of any live driver, and a live
PostgreSQL reproduction that confirms the actual psycopg2 error
the framework hides.

### Live reproduction (PostgreSQL 18 + psycopg2-binary 2.9.12)

`pypy/tests/test_issue_46_live_repro.py` against a real PostgreSQL
instance (DB `tina4_bug46`, table `gift_cards` with `is_deleted
BOOLEAN`, seeded with the reporter's email). Four assertions, all
passing — exact `-s` capture:

```
test_baseline_sanity_psycopg2_direct                                 PASSED
test_raw_psycopg2_is_deleted_eq_zero_raises_operator_error
[psycopg2 raw error] operator does not exist: boolean = integer
LINE 1: ...ed_by_email = 'schalk@codeinfinity.co.za' AND is_deleted = 0
                                                                    ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
                                                                     PASSED
test_orm_where_with_is_deleted_eq_zero_surfaces_cascade_only
[framework-surfaced error] InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block
                                                                     PASSED
test_db_last_error_does_not_capture_the_original_cause
[db.last_error after where()] None                                   PASSED
```

Three layers, three different messages:

| Layer | Message |
|---|---|
| Raw psycopg2 cursor | `operator does not exist: boolean = integer` — with line/column pointer at `is_deleted = 0` |
| ORM `where()` surfaces to caller | `InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block` — **byte-identical to the reporter's log** |
| `Database.get_error()` after the call | `None` — even the framework's own `last_error` channel preserves nothing |

The trigger hypothesis is now confirmed: when the reporter's
`is_deleted = 0` filter hits a `BOOLEAN` column, psycopg2 raises
`UndefinedFunction`. The framework's count-probe swallow at
`postgres.py:148-152` discards that error, the aborted-transaction
cascade fires on the next line, and that cascade message is the
only thing that reaches the application.

### Source-read confirmation (no live driver needed)

`pypy/tests/test_issue_46_pg_silent_abort_probe.py` stubs
psycopg2 with a cursor that flips to aborted state after the first
error (matching real psycopg2 semantics) and exercises the real
`PostgreSQLAdapter.fetch()` code path unchanged. Four assertions,
all passing today:

1. `test_count_probe_failure_is_swallowed_silently` — the count-probe
   exception does not propagate. The next line's
   `InFailedSqlTransaction` does. The swallow only hides the first
   failure, not the cascade.
2. `test_no_rollback_between_count_probe_and_pagination` —
   `conn.rollback()` is called zero times between the swallow and
   the cascade. Bug-direction assertion (`rollback_calls == 0`) is
   the regression sentinel; when the SAVEPOINT fix lands it will
   flip to `>= 1`.
3. `test_no_log_emitted_on_count_probe_swallow` — pytest's `caplog`
   captures no `ERROR`/`WARNING` log records mentioning the
   swallowed cause or the transaction. Bug-direction assertion is
   the empty-list check.
4. `test_user_visible_message_hides_original_cause` — what reaches
   the caller contains *"current transaction is aborted"* but not
   *"boolean = integer"*. The original cause is gone.

Run:

```
uv run python -m pytest tests/test_issue_46_pg_silent_abort_probe.py -v
```

Today: `4 passed`.

## Recommended fix (suggestion, not implemented here)

Two coupled changes at the framework, mirroring the issue-#38 fix:

1. **`postgres.py:148-152` — guard the count probe with a SAVEPOINT**
   so a failure there does not poison the outer transaction:

   ```python
   cursor.execute("SAVEPOINT _t4_count_probe")
   try:
       self._safe_execute(cursor, count_sql, params)
       total = cursor.fetchone()["cnt"]
       cursor.execute("RELEASE SAVEPOINT _t4_count_probe")
   except Exception as e:
       cursor.execute("ROLLBACK TO SAVEPOINT _t4_count_probe")
       total = 0
       from tina4_python.debug import Log
       Log.error("count-probe failed; falling back to total=0",
                 error=str(e), sql=sql)
   ```

2. **`connection.py:412-414` — log + rollback in `Database.execute()`**
   so subsequent calls on the same connection are not silently
   poisoned, and the caller has a trace:

   ```python
   except Exception as e:
       self.last_error = str(e)
       from tina4_python.debug import Log
       Log.error("Database.execute() failed",
                 error=str(e), sql=sql)
       try:
           self._get_adapter().rollback()
       except Exception:
           pass  # rollback on already-closed conn is fine
       return False
   ```

The same logging shape (`Log.error(...) → return False`) should also
be applied at `model.py:336-338`, `model.py:364-366`,
`model.py:384-386`, `model.py:405-407` so every silent failure on
the ORM path leaves a trace.

## Draft upstream comment (paste into issue #46)

> Reproduced live against PostgreSQL 18 + psycopg2-binary 2.9.12.
>
> **Root cause:** `PostgreSQLAdapter.fetch()`
> (`tina4_python/database/postgres.py:148-152`) wraps a `COUNT(*)`
> probe in `try: ... except Exception: total = 0`. On PostgreSQL the
> connection is opened with `autocommit = False`
> (`postgres.py:70`), so the moment the count probe raises (e.g.
> `is_deleted = 0` against a `BOOLEAN` column → `operator does not
> exist: boolean = integer`) the transaction enters aborted state.
> The probe's bare-except swallows the original error and does not
> roll back or release a savepoint. The next line then runs the
> paginated query, which immediately raises `InFailedSqlTransaction`
> with the *"current transaction is aborted"* message — and that is
> the only thing the caller ever sees.
>
> The framework already knows about this exact failure mode: lines
> 99-122 in the same file guard the `lastval()` probe with a
> `SAVEPOINT` for upstream issue #38. The same shape is needed at
> the count probe.
>
> Visibility half: `grep -rn "Log\." tina4_python/database/
> tina4_python/orm/` returns zero matches. The DB + ORM layers have
> no structured logging on any of their swallow paths
> (`connection.py:412-414`, `model.py:336-338`, etc.) — that is why
> "there are no logs after that point" in the report.
>
> Adversarial verification before posting:
> - Looked for a rollback path inside `Database.execute()`'s except
>   block — none.
> - Looked for `Log.*` calls in `tina4_python/database/` and
>   `tina4_python/orm/` — none.
> - Checked whether `TINA4_AUTOCOMMIT=true` escapes the cascade —
>   no, the env var only flips the adapter's `_autocommit` python
>   flag (`adapter.py:307`); `_conn.autocommit` is hardcoded `False`
>   at `postgres.py:70` so PG is still inside an implicit txn.
> - Re-read `postgres.py:148-152` for any SAVEPOINT/rollback —
>   none, only at `postgres.py:99-122` for the lastval probe.
>
> Two repro tests are included as regression sentinels:
> - [`test_issue_46_live_repro.py`](LINK) — live PG, mirrors the
>   reporter's filter verbatim. Captures the raw psycopg2 cause
>   (`operator does not exist: boolean = integer`) and proves the
>   ORM swallows it and surfaces only the cascade message.
> - [`test_issue_46_pg_silent_abort_probe.py`](LINK) — mocks
>   psycopg2 so the framework code path can be exercised without a
>   live PG. Four assertions about swallow / no-rollback / no-log /
>   cause-discarded.
>
> Both probe sets PASS today; they will FAIL once the SAVEPOINT +
> `Log.error` fix lands, so they double as regression sentinels.
>
> Suggested fix shape: SAVEPOINT around the count probe (mirroring
> lines 108-122), plus `Log.error(...)` at every swallow point on
> the DB+ORM layer so the original cause is preserved before the
> bare-except path discards it.
