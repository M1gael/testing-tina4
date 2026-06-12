# Issue #49 — filed body + history

**Upstream:** https://github.com/tina4stack/tina4-python/issues/49
**Title:** *Database error visibility — follow-up gaps remaining after #46 fix*
**Filed by:** MichaelC8E, 2026-06-10T13:31:43Z
**Status:** OPEN
**Relation to BH-46:** files the 3 residual gaps surfaced during BH-46 fix verification on 3.13.8. #46 closed-as-fixed by maintainer 2026-06-09; these are same defect class but scoped narrower. Companion comment on closed #46 acknowledging the fix + flagging this follow-up is at `issue-46-fix-verification-comment.md` (not yet posted).

The body below is the posted issue text (verification section removed during user review — code citations + reproductions already carry the evidence weight).

---

# Cascade still hides original cause inside explicit transactions + db.last_error asymmetry on fetch()

Three residual paths verified on `tina4-python` 3.13.8 against live PG 18. All three reproduce the BH-46 symptom (cascade message hides the original cause) in scenarios narrower than the closed-and-fixed reporter case.

Probe: `pypy/tests/test_issue_46_matrix_probe.py` — full `{fetch, execute} × {outside txn, inside txn} × {fresh, post-failure, pre-poisoned}` matrix; 13 assertions; 6 fix-direction pass + 5 gap pass (gap tests written as positive-direction regression sentinels — flip to fail when extended).

## Gap 1 — `fetch()` inside `db.start_transaction()`

`PostgreSQLAdapter._heal_aborted_txn()` defers to explicit transactions (`postgres.py:79`); `_on_query_error()`'s auto-rollback defers similarly (`postgres.py:162`). The maintainer's stated reasoning at `postgres.py:127-130` — *"Inside an explicit transaction we do NOT auto-rollback — the user owns that transaction"* — is reasonable for callers running SAVEPOINT/retry patterns, but leaves the visibility gap intact for any user wrapping a write in a txn.

**Symptom:** reporter's exact query shape inside a txn surfaces `InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block`. Original `UndefinedFunction: operator does not exist: boolean = integer` is lost.

**Reproduction (fresh `Database()` instance, no prior pollution):**
```python
db = Database(url=PG_URL); orm_bind(db)
db.start_transaction()
try:
    GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])
except Exception as e:
    print(str(e))  # cascade, not original cause
```

**Verifying probe:** `test_gap_fetch_inside_explicit_txn_cascades` + `test_gap_fetch_inside_explicit_txn_logs_only_cascade`.

## Gap 2 — `execute()` inside explicit txn cascades AND swallows the exception

`Database.execute()` (`connection.py:412-414`) catches every exception, stores `str(e)` in `last_error`, returns `False`. Outside a txn this is fine — `last_error` holds the original cause. Inside a txn:

- Call #1 fails: `last_error` = original cause, returns `False`
- Call #2 fails (poisoned conn): `last_error` = cascade message (overwrites), returns `False`
- Caller can't distinguish "real error" from "cascade" without parsing `last_error`

**Worth noting:** call #2 returns `False` silently — no exception, no log surfaced to the caller's try/except. A user who isn't polling `db.get_error()` after every call sees no signal at all.

**Verifying probe:** `test_gap_execute_inside_explicit_txn_swallows_second_call`.

## Gap 3 — `db.last_error` asymmetric between `fetch()` and `execute()`

`Database.fetch()` (`connection.py:438-439`) routes straight to `adapter.fetch()` with no `last_error` capture. `Database.execute()` (`connection.py:412-414`) catches and stores. After `fetch()` failure:

| Surface | Value |
|---|---|
| `db.get_error()` | `None` |
| `db.last_error` (attr) | `None` |
| `adapter.last_error` | original cause |

`_on_query_error` (`postgres.py:154`) writes `self.last_error = str(exc)` on the adapter. The data is there — the `Database` wrapper just doesn't read it on the `fetch()` path.

**Verifying probes:** `test_gap_fetch_failure_does_not_populate_db_last_error` + `test_data_exists_on_adapter_last_error_not_db_last_error`.

## Potential fixes

- **Gap 1 + 2** — symmetric option to opt out of the explicit-txn defer. One shape: a `Log.warning` from `_on_query_error` that fires inside-txn too (so the cause is at least in the log even when auto-rollback is skipped), without forcing rollback semantics on SAVEPOINT/retry callers. Alternatively, document the txn-cascade behaviour at `db.start_transaction()` so users know to inspect `adapter.last_error` after a failed txn-wrapped query.
- **Gap 3** — `Database.fetch()` to mirror `Database.execute()`'s last_error capture, e.g. wrap the `adapter.fetch()` call in `try/except`, set `self.last_error = str(e)`, re-raise. One-line behavioural symmetry — `fetch()` already re-raises, so caller behaviour unchanged; only `db.get_error()` populates.
