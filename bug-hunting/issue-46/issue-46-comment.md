# Comment to post on tina4stack/tina4-python#46

Paste the block below into the GitHub issue thread. The patch files
themselves (`bug-hunting/fix-issue-46-patches/01..03.patch`) should
be attached as files or referenced via PR — they're too long for an
inline comment.

---

## Reproduced and root-caused on `tina4-python` 3.13.4 + PostgreSQL 18 + `psycopg2-binary` 2.9.12.

### Root cause — `tina4_python/database/postgres.py:148-152`

The count probe inside `PostgreSQLAdapter.fetch()` swallows every exception with no rollback and no savepoint:

```python
# postgres.py:146-152 (verbatim, 3.13.4)
# Count total rows
count_sql = f"SELECT COUNT(*) AS cnt FROM ({sql}) AS _count_subquery"
try:
    self._safe_execute(cursor, count_sql, params)
    total = cursor.fetchone()["cnt"]
except Exception:
    total = 0
```

The connection is opened with `self._conn.autocommit = False` (`postgres.py:70`), so the moment the count probe raises, psycopg2 marks the transaction as aborted. The bare `except Exception: total = 0` does not roll back or release a savepoint, so the very next line — the paginated query — runs against an already-poisoned connection and raises `InFailedSqlTransaction` with the *"current transaction is aborted, commands ignored until end of transaction block"* message. The original cause is gone by the time the caller sees anything.

The framework already knows about this exact failure shape: the `lastval()` probe a few lines above (`postgres.py:99-122`) guards against it with a `SAVEPOINT` / `ROLLBACK TO SAVEPOINT` block, added for #38. The same shape is needed at the count probe.

### Live reproduction

Schema in the repro (matching the typical PG idiom for a soft-delete flag):

```sql
CREATE TABLE gift_cards (
    id SERIAL PRIMARY KEY,
    created_by_email VARCHAR(200) NOT NULL,
    owned_by_email VARCHAR(200),
    amount NUMERIC(10,2) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Reporter's filter, verbatim:

```python
GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])
```

What `psycopg2` actually raises (captured directly from a raw cursor against the same DB, bypassing the framework):

```
psycopg2.errors.UndefinedFunction: operator does not exist: boolean = integer
LINE 1: ...mail = 'schalk@codeinfinity.co.za' AND is_deleted = 0
                                                              ^
HINT:  No operator matches the given name and argument types.
       You might need to add explicit type casts.
```

What the framework surfaces through `Model.where()` (against the same DB, same SQL):

```
InFailedSqlTransaction: current transaction is aborted,
commands ignored until end of transaction block
```

— byte-identical to the message in the original report. The `UndefinedFunction` cause, line number, column pointer, and `HINT` are all discarded.

The trigger in this reproduction is a `BOOLEAN` column with an integer-literal filter. That is the most likely shape for the reporter's `gift_cards.is_deleted` column given the filter SQL, but the same swallow + cascade pattern would fire for any error inside the count probe (missing column, type cast failure, function-not-found, deadlock victim, etc.) — the column type is the trigger, not the root cause.

### Visibility gap

```
grep -rn "Log\." tina4_python/database/ tina4_python/orm/
# (no matches in 3.13.4)
```

Zero structured-log calls in the entire DB + ORM layer. `tina4_python.debug.Log` is available framework-wide but is not invoked on any swallow path. `Database.get_error()` returns `None` after a `fetch()` failure because `Database.fetch()` never touches `last_error` (only `Database.execute()` does). So even the framework's own diagnostic channel preserves nothing by the time the caller sees the cascade.

### Suggested fix

Three patches; primary is patch 1 (closes the cascade), 2 and 3 close the broader visibility gap in the same defect class.

| # | File | Change |
|---|---|---|
| 1 | `tina4_python/database/postgres.py` | Wrap the count probe AND the paginated query each in their own `SAVEPOINT` / `ROLLBACK TO SAVEPOINT` block. Add `Log.error` on the count-probe failure path with the original cause + outer SQL. Mirrors the `lastval()` SAVEPOINT pattern at lines 99-122. |
| 2 | `tina4_python/database/connection.py` | Add `Log.error` before the existing `return False` in `Database.execute()`'s `except Exception`. Pure addition — return contract is preserved. |
| 3 | `tina4_python/orm/model.py` | Add `Log.error` in the four ORM CRUD `except` blocks (`save` / `delete` / `force_delete` / `restore`). No contract change — `save()` still returns `False`; the others still re-raise. |

Every `from tina4_python.debug import Log; Log.error(...)` call is wrapped in its own `try / except Exception: pass` so a broken or absent logger cannot break the data path.

After patch 1, the framework call surfaces:

```
UndefinedFunction: operator does not exist: boolean = integer
LINE 1: ...mail = 'schalk@codeinfinity.co.za' AND is_deleted = 0 LIMIT ...
                                                              ^
HINT:  No operator matches the given name and argument types.
```

and the structured log emits:

```
[ERROR] PostgreSQL count probe failed; pagination total set to 0
    error="operator does not exist: boolean = integer\nLINE 1: ..."
    sql="SELECT * FROM gift_cards WHERE created_by_email = %s AND is_deleted = 0"
```

### Verification

Three test files in the reproduction workspace (all 19 tests pass against the patched framework; the bug-direction assertions all flip to failure against pristine 3.13.4, so they double as regression sentinels):

| Layer | Tests | What is verified |
|---|---|---|
| Live PG 18 reproduction | 5 | Original `UndefinedFunction` cause reaches the caller; cascade message gone; `Log.error` captures cause + SQL; `psycopg2` raw query produces the expected `operator does not exist` error. |
| Mock-cursor source-read probe | 4 | `SAVEPOINT` issued before the probe; `ROLLBACK TO SAVEPOINT` on failure; paginated query proceeds cleanly after recovery; `Log.error` emitted with original cause. Runs without a live PG instance. |
| Adversarial sweep | 10 | Repeated identical failures don't compound; alternating pass/fail leaves no residue; failures inside user-driven `start_transaction()` blocks preserve the outer txn (the user's `INSERT` + `rollback()` work normally afterwards); credentials don't leak into the log payload; long SQL doesn't crash the log; `ORM.save()` contract (returns `False`, never raises) preserved; paginated-query failure on an unrelated bad table still propagates; a sabotaged `Log.error` does not escape into the data path; correct counts still reported on healthy queries. |

Pre-patch baseline against pristine `tina4-python==3.13.4`:

```
$ uv pip install --force-reinstall --no-deps tina4-python==3.13.4
$ uv run python -m pytest tests/test_issue_46_live_repro.py -v -s
...
FAILED test_orm_where_surfaces_original_cause_not_cascade
  → Got: current transaction is aborted, commands ignored until end of transaction block
FAILED test_count_probe_logs_original_cause
  → [captured log stream length] 0 chars
```

(The two failures above flip to pass once the patches are applied — that is the cascade-vs-cause inversion, captured as a regression sentinel.)

### Adjacent findings worth a separate filing

Two issues surfaced during adversarial testing of the fix. They aren't part of the patch series, but are in the same defect family and worth flagging:

- **`SQLTranslator.boolean_to_int`** (`tina4_python/database/adapter.py:538-542`) unconditionally rewrites `\bTRUE\b` → `1` and `\bFALSE\b` → `0` on the PG translation path. Against a real `BOOLEAN` column this re-introduces the same BOOLEAN-vs-integer mismatch in framework-generated SQL — a caller writing `is_deleted = FALSE` to dodge this issue still hits the operator error, because the translator silently rewrites the literal to `is_deleted = 0` before it reaches psycopg2. The translator should probably skip this rewrite on engines (PG, Firebird) with native boolean support.

- **`SAVEPOINT _t4_count_probe` / `_t4_paginated`** in the proposed patch use fixed names. If a caller has an outer savepoint with the same name, the framework's `RELEASE SAVEPOINT` will end the caller's savepoint too. Low practical impact (those names are unlikely to collide), but trivially fixed by adding a unique-per-call suffix (e.g. `id(cursor)`).

### Patch files

Three unified diffs against `tina4-python` 3.13.4 — `git apply --check` passes for each one against a pristine checkout:

1. [01-postgres-savepoint-count-and-paginated.patch](#) — primary fix (75 lines)
2. [02-connection-execute-log.patch](#) — Database.execute() visibility (23 lines)
3. [03-model-orm-log.patch](#) — ORM CRUD visibility (80 lines)

(Patch attachments / PR follow.)
