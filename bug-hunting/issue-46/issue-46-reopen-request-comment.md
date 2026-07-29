# [SUPERSEDED] Reopen-request draft for tina4stack/tina4-python#46

**Do not post.** This was one of two alternative drafts. The user chose the other path (Pattern A): keep #46 closed, file the residual gaps as a fresh issue — which landed as upstream **#49** (2026-06-10T13:31:43Z, body at `issue-49-comment.md`). The neutral acknowledgment comment for closed #46 is at `issue-46-fix-verification-comment.md` (still pending post). Kept for reference only.

**Status:** superseded 2026-06-10 — never posted.

---

## Reopen request — cascade still hides cause in 3 adjacent paths on 3.13.8

The v3.13.6 + v3.13.8 fix works for the documented call shape — `Model.where(...)` outside an explicit transaction now surfaces the original PG error with sql + params context. Verified live against PG 18.

Three paths in the same defect class still reproduce the original symptom on 3.13.8:

### 1. `fetch()` inside `db.start_transaction()`

```python
db.start_transaction()
GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])
```

Surfaces `InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block`. The `UndefinedFunction: operator does not exist: boolean = integer` cause is lost.

`_heal_aborted_txn()` (`postgres.py:79`) and `_on_query_error()` auto-rollback (`postgres.py:162`) both defer when `self._in_transaction` is True. Documented as design choice at `postgres.py:127-130` — *"Inside an explicit transaction we do NOT auto-rollback — the user owns that transaction."*

### 2. `execute()` inside `db.start_transaction()` — silent failure

```python
db.start_transaction()
db.execute("UPDATE gift_cards SET is_deleted = 0 WHERE id = 1")  # returns False, last_error = original cause
db.execute("UPDATE gift_cards SET created_by_email = 'x' WHERE id = 1")  # returns False, last_error = cascade message
```

`Database.execute()` (`connection.py:412-414`) catches every exception and returns `False`. Inside a txn, the second call on a poisoned conn also returns `False` — caller has no exception to catch and no way to distinguish a real failure from a cascade without parsing `db.last_error`. By the second call, the cascade message has overwritten the original cause in `last_error`.

### 3. `db.last_error` asymmetry on `fetch()` failures

| Surface | After `fetch()` failure | After `execute()` failure |
|---|---|---|
| `db.get_error()` | `None` | original cause |
| `adapter.last_error` | original cause | original cause |

`Database.fetch()` (`connection.py:438-439`) routes straight to `adapter.fetch()` with no `last_error` capture. `Database.execute()` (`connection.py:412-414`) does capture. Adapter's `_on_query_error` (`postgres.py:154`) writes `self.last_error = str(exc)` either way — the Database wrapper just doesn't read it on the `fetch()` path.

## Verification

`pypy/tests/test_issue_46_matrix_probe.py` — 13 assertions covering `{fetch, execute} × {outside txn, inside txn} × {fresh, post-failure, pre-poisoned}`. 6 fix-direction assertions pass (cascade gone outside txn); 5 gap assertions pass (cascade still present inside txn); 2 asymmetry assertions pass. All gap tests are written as positive-direction regression sentinels — if the fix is extended later, they flip to failure (XPASS).

Suite state on 3.13.8: `28 passed, 4 xfailed in 1.66s` across all #46 probe files.

## Potential fix shapes

- **Gaps 1 + 2** — `Log.warning` (not rollback) from `_on_query_error` even inside-txn, so the cause is at least logged when auto-rollback is skipped. Preserves the SAVEPOINT/retry contract for callers who own their transaction; closes the visibility half.
- **Gap 3** — one-line change in `Database.fetch()` to capture `last_error` like `Database.execute()` does. No behavioural change for callers — `fetch()` still re-raises; only `db.get_error()` populates.

## Suggestion on tracking

These are the same defect class as the original report (*"No database error visibility"*) and the same code paths the v3.13.6 + v3.13.8 fix touched. Reopening #46 or filing a fresh issue both work — happy either way. If filing fresh, the analysis is at `bug-hunting/issue-46-residual-gaps-followup.md` and can be lifted directly.
