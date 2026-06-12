# Issue #46 — No database error visibility

**Upstream:** https://github.com/tina4stack/tina4-python/issues/46
**Reporter:** SchalkAB13711
**Reported against:** tina4-python 3.13.4
**Fix shipped:** v3.13.6 (2026-06-09, commit `3188176`) + follow-on v3.13.8 (2026-06-10, commit `42685a1`)
**Upstream status:** CLOSED 2026-06-09T15:03:10Z
**Local verification version:** tina4-python **3.13.8**
**Local verdict:** **Partial fix** — reporter's exact call shape works; two residual paths still cascade and hide the original cause.

---

## Reporter's symptom (pre-fix, 3.13.4)

First ORM call `GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])` returned:

```
current transaction is aborted, commands ignored until end of transaction block
```

No log entry shows what actually failed first.

## Pre-fix root cause (3.13.4)

`PostgreSQLAdapter.fetch()` ran a `COUNT(*)` probe with a bare-except swallow before the paginated query. When the count probe raised on PG (e.g. `is_deleted = 0` against a `BOOLEAN` column → `operator does not exist: boolean = integer`), the except clause swallowed the error and the connection was left in aborted state. The paginated query then raised `InFailedSqlTransaction` with the cascade message — that's what surfaced.

## Maintainer's fix (v3.13.6 + v3.13.8)

Different shape from the SAVEPOINT pattern suggested in the original report. Three code-level changes:

1. **`postgres.py:264-302` — `fetch()` count probe now ROLLBACKs on failure** (not SAVEPOINT-scoped):
   ```python
   try:
       self._safe_execute(cursor, count_sql, params)
       total = cursor.fetchone()["cnt"]
   except Exception:
       total = 0
       if not self._in_transaction and self._conn is not None:
           try:
               self._conn.rollback()
           except Exception:
               pass
   ```

2. **`postgres.py:106-167` — new `_exec_with_handling` wrapper around `_safe_execute`** routes failures through `_on_query_error` which:
   - Logs via `Log.error` with sql + params context
   - Stores `self.last_error = str(exc)` (on the adapter, not on the Database wrapper)
   - Auto-rollbacks if not in explicit transaction
   - Re-raises so callers still see the failure

3. **`postgres.py:52-104` — new `_heal_aborted_txn()` pre-flight check** (v3.13.8) inspects `psycopg2 transaction_status` and ROLLBACKs if the connection arrived poisoned from elsewhere (boot-time query, untracked failure, etc.). Defers to explicit transactions by design.

The maintainer's stated reasoning (`postgres.py:127-130`): *"Inside an explicit transaction we do NOT auto-rollback — the user owns that transaction (could be running a SAVEPOINT/retry pattern)."* The heal step defers for the same reason.

## Empirical verification matrix (3.13.8 against live PG 18)

Three test files, **22 assertions, all passing**:

| File | Tests | What it covers |
|---|---|---|
| `pypy/tests/test_issue_46_pg_silent_abort_probe.py` | 4 | Mocked psycopg2 — fix-direction code-path shape, no live infra needed |
| `pypy/tests/test_issue_46_live_repro.py` | 5 | Live PG 18 — reporter's exact ORM call, log capture, last_error |
| `pypy/tests/test_issue_46_matrix_probe.py` | 13 | Live PG 18 — full `{fetch,execute} × {outside-txn, inside-txn} × {fresh, post-failure, pre-poisoned}` matrix |

### Result matrix per scenario

| Scenario | Cascade gone? | Original cause visible? | Log emitted? | `db.last_error`? | Raises? |
|---|---|---|---|---|---|
| `fetch()` outside explicit txn | ✅ | ✅ exception + log | ✅ sql+params | ❌ None (asymmetry) | ✅ |
| `fetch()` inside explicit txn | ❌ **cascade** | ❌ **lost** | logs cascade only | shows cascade msg | ✅ |
| `execute()` outside explicit txn | ✅ | ✅ exception + log | ✅ sql+params | ✅ original cause | ✅ (catches → False) |
| `execute()` inside explicit txn | ❌ **cascade** | ❌ **lost** | logs cascade only | shows cascade msg | ❌ **silent False** |
| `fetch()` on pre-poisoned conn | ✅ heal fires | ✅ | warning + then normal | — | ✅ |
| `execute()` on pre-poisoned conn | ✅ heal fires | ✅ | warning + then normal | ✅ | ✅ |

### Adversarial disproof outcomes (pre-conclusion pass)

| Tried to break | Result |
|---|---|
| "Maybe the fix doesn't survive a second call." | Outside txn: second valid call works (heal between calls). Inside txn: second call cascades — but that's a separate gap, not regression. |
| "Maybe the fix only works for `boolean = integer`." | Tested `DatatypeMismatch` on UPDATE (boolean column vs int literal) and `UndefinedTable` (raw psycopg2 SELECT from nonexistent table). Both fix and gap behave identically. |
| "Maybe `db.last_error` IS populated, just on a different field." | Probed `db.get_error()`, `db.last_error`, `adapter.last_error`. Adapter has it; Database wrapper doesn't propagate on the `fetch()` path. |
| "Maybe the `start_transaction` → fail scenario is actually fixed and I just hit a stale conn." | Tested with a brand-new `Database()` instance, fresh connection, no prior pollution. First call inside txn still cascades. Gap is design choice, not bug. |
| "Maybe `execute()` inside txn DOES raise — the swallow only happens at `Database` wrapper level." | Confirmed via direct script: `db.execute(...)` returns `False` silently, no exception propagates to caller. Adapter raises; `Database.execute()` (connection.py:412-414) catches → stores `last_error` → returns `False`. Caller has no signal without polling `db.get_error()`. |

## Residual gaps (filed for follow-up)

Three paths where 3.13.8 still reproduces the original BH-46 symptom (cascade hides cause):

### Gap 1 — `fetch()` inside explicit transaction
Reporter's exact query shape wrapped in `db.start_transaction()` still cascades. The user-visible exception is `InFailedSqlTransaction: current transaction is aborted...` with no trace of the underlying `UndefinedFunction: operator does not exist`. `Log.error` fires but logs only the cascade. Probe: `test_gap_fetch_inside_explicit_txn_cascades`.

### Gap 2 — `execute()` inside explicit transaction (worse — silent failure)
`Database.execute()` (connection.py:412-414) catches all exceptions and returns `False`. Inside a txn, a second `execute()` on a poisoned connection returns `False` too — caller cannot distinguish "real error" from "cascade" without parsing `db.last_error`. Probes: `test_gap_execute_inside_explicit_txn_swallows_second_call`, `test_gap_second_call_inside_txn_still_cascades`.

### Gap 3 — `db.last_error` asymmetry on `fetch()` failures
`Database.fetch()` (connection.py:438-439) routes straight to `adapter.fetch()` with no `last_error` capture. `Database.execute()` (connection.py:412-414) does capture. After a `fetch()` failure, `db.get_error()` returns `None` even though `adapter.last_error` has the original cause. Trivial one-line fix on the maintainer side. Probes: `test_gap_fetch_failure_does_not_populate_db_last_error`, `test_data_exists_on_adapter_last_error_not_db_last_error`.

## Notes on the chosen fix shape vs original suggestion

Original suggestion (BH-46 patches at `bug-hunting/fix-issue-46-patches/`) proposed:
- SAVEPOINT `_t4_count_probe` around the count probe — mirroring lastval probe at `postgres.py:240-248`
- `Log.error` emitted from inside the count-probe except block

Maintainer's actual fix:
- Full `self._conn.rollback()` outside explicit txn — simpler, single-statement
- `Log.error` emitted from `_on_query_error` on the paginated query (since the same SQL fails there too)
- Plus `_heal_aborted_txn()` pre-flight in v3.13.8 — broader coverage than the original suggestion

Both shapes fix the reporter's symptom. Maintainer's is simpler at the count-probe site but pushes recovery semantics into a wider helper (`_exec_with_handling`) — which also enabled the v3.13.8 heal extension cleanly.

## Source-read of the actual fix

### `_heal_aborted_txn` — v3.13.8 (postgres.py:52-104)
```python
def _heal_aborted_txn(self):
    if self._in_transaction or self._conn is None:
        return
    try:
        import psycopg2.extensions as _ext
        status = self._conn.info.transaction_status
    except Exception:
        return
    if status != _ext.TRANSACTION_STATUS_INERROR:
        return
    try:
        self._conn.rollback()
    except Exception:
        return
    try:
        from tina4_python.debug import Log
        Log.warning(
            "PostgreSQL connection arrived in aborted-transaction "
            "state — issued pre-flight ROLLBACK so the next query "
            "starts clean. Look back in the log for the original "
            "PostgreSQL query failed entry."
        )
    except Exception:
        pass
```

### `_on_query_error` — v3.13.6 (postgres.py:139-167)
```python
def _on_query_error(self, exc: Exception, sql: str, params=None):
    try:
        from tina4_python.debug import Log
        preview = sql.strip().splitlines()[0][:200] if sql else "<no sql>"
        Log.error(
            f"PostgreSQL query failed: {exc.__class__.__name__}: {exc}",
            sql=preview,
            params=params,
        )
    except Exception:
        pass

    self.last_error = str(exc)

    if not self._in_transaction and self._conn is not None:
        try:
            self._conn.rollback()
        except Exception:
            pass
```

### `fetch()` count probe — v3.13.8 (postgres.py:264-302)
```python
def fetch(self, sql, params=None, limit=100, offset=0):
    import psycopg2.extras
    sql = self._translate_sql(sql)
    self._heal_aborted_txn()
    cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    count_sql = f"SELECT COUNT(*) AS cnt FROM ({sql}) AS _count_subquery"
    try:
        self._safe_execute(cursor, count_sql, params)
        total = cursor.fetchone()["cnt"]
    except Exception:
        total = 0
        if not self._in_transaction and self._conn is not None:
            try:
                self._conn.rollback()
            except Exception:
                pass

    paginated_sql = f"{sql} LIMIT %s OFFSET %s"
    paginated_params = (params or []) + [limit, offset]
    self._exec_with_handling(cursor, paginated_sql, paginated_params)
    rows = [self._decode_blobs(dict(row)) for row in cursor.fetchall()]
    return DatabaseResult(records=rows, count=total, limit=limit, offset=offset, sql=sql, adapter=self)
```

## Live evidence — reporter's exact ORM call, 3.13.8 output

Output from `manual_bh46_verify.py` (temp script, since cleaned):

```
[setup] bound ORM to postgresql://postgres:tina4test@localhost:5432/tina4_bug46

[call] GiftCard.where("created_by_email = ? AND is_deleted = 0", ['schalk@codeinfinity.co.za'])

2026-06-10T12:16:56.709Z [ERROR  ] PostgreSQL query failed: UndefinedFunction: operator does not exist: boolean = integer
LINE 1: ...mail = 'schalk@codeinfinity.co.za' AND is_deleted = 0 LIMIT ...
                                                             ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
 {"sql": "SELECT * FROM gift_cards WHERE created_by_email = %s AND is_deleted = 0 LIMIT %s OFFSET %s", "params": ["schalk@codeinfinity.co.za", 20, 0]}

[result] Exception type: UndefinedFunction
[result] Exception module: psycopg2.errors
[result] Exception str:
         | operator does not exist: boolean = integer
         | LINE 1: ...AND is_deleted = 0 LIMIT ...
         |                              ^
         | HINT:  No operator matches the given name and argument types.

[after] db.last_error: None
```

Compare to reporter's pre-fix error: just `"current transaction is aborted, commands ignored until end of transaction block"`. The fix unambiguously surfaces the original cause for the reporter's specific call shape.

## Run the probes

```
# all 22 BH-46 assertions
uv run python -m pytest tests/test_issue_46_pg_silent_abort_probe.py tests/test_issue_46_live_repro.py tests/test_issue_46_matrix_probe.py -v
```

Today (3.13.8): **22 passed in 1.25s.**

The matrix probe doubles as a positive-direction regression sentinel for the residual gaps: if maintainer later extends auto-rollback or heal to cover explicit transactions, the `test_gap_*` assertions FLIP to failure — that's the signal to update logs and acknowledge upstream.
