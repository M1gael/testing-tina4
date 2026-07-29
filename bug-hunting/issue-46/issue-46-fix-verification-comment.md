# Comment to post on tina4stack/tina4-python#46 (closed)

Acknowledgment + heads-up that 3 residual gaps will be filed as a separate issue. Stays neutral — does not request reopen.

**Status:** drafted 2026-06-10, **not yet posted** (EOD batch).
**Identity:** post as MichaelC8E via `gh`.
**Companion:** the residual-gaps issue was filed as upstream **#49** ([https://github.com/tina4stack/tina4-python/issues/49](https://github.com/tina4stack/tina4-python/issues/49)) on 2026-06-10T13:31:43Z. Filed body at `issue-49-comment.md`.

---

## Fix verified on tina4-python 3.13.8

The reporter's call shape — `Model.where("created_by_email = ? AND is_deleted = 0", [email])` — now surfaces the original PG error against live PG 18:

```
psycopg2.errors.UndefinedFunction: operator does not exist: boolean = integer
LINE 1: ...AND is_deleted = 0 LIMIT ...
                             ^
HINT: No operator matches the given name and argument types...
```

`Log.error` emits with full sql + params + LINE + HINT. Cascade message no longer present. v3.13.8's `_heal_aborted_txn()` also recovers connections that arrive poisoned from outside the wrapper — verified by raw-psycopg2 poisoning then a normal `fetch()`.

## Worth noting — 3 residual paths in the same defect class

Three paths on 3.13.8 still surface the cascade message and hide the original PG cause. Filing as a separate issue rather than reopening — they're scoped narrower than the original report.

- **`fetch()` inside `db.start_transaction()`** — cascade surfaces; original cause lost. `_heal_aborted_txn()` defers to explicit txns by design (`postgres.py:79`); `_on_query_error`'s auto-rollback defers similarly (`postgres.py:162`).
- **`execute()` inside `db.start_transaction()`** — cascade path PLUS `Database.execute()` (`connection.py:412-414`) silently catches the exception and returns `False`. Caller has no signal unless they poll `db.get_error()`, which returns the cascade message on a second poisoned call.
- **`db.last_error` asymmetry on `fetch()` failures** — `Database.fetch()` (`connection.py:438-439`) routes straight to `adapter.fetch()` with no `last_error` capture; `Database.execute()` does capture. After `fetch()` failure, `db.get_error()` returns `None` even though `adapter.last_error` holds the original cause.

Verification probes (full 13-test matrix across `{fetch, execute} × {outside txn, inside txn} × {fresh, post-failure, pre-poisoned}`) live alongside reporter's repro setup — gap tests written as positive-direction regression sentinels (flip to failure if the fix is extended).

## Potential fix shapes (in the separate issue)

- Gaps 1 + 2: `Log.warning` from `_on_query_error` even inside-txn, so the cause is at least logged when auto-rollback is skipped — preserves the SAVEPOINT/retry contract for callers who own their transaction.
- Gap 3: one-line capture in `Database.fetch()` mirroring `Database.execute()`. No behavioural change for callers — `fetch()` still re-raises; only `db.get_error()` populates.

Full analysis + verification matrix in the new issue.
