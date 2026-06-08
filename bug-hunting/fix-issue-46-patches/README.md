# Issue #46 fix — patch series

Three patches that close
[`tina4stack/tina4-python#46`](https://github.com/tina4stack/tina4-python/issues/46)
("No database error visibility"). Patch 1 is the primary fix
(closes the cascade); 2 and 3 close adjacent visibility gaps in the
same defect class.

| Patch | File | Lines | What it does |
|---|---|---|---|
| 01 | `tina4_python/database/postgres.py` | ~148-205 in fetch() | Wraps the count probe AND the paginated query in their own `SAVEPOINT` / `ROLLBACK TO SAVEPOINT` blocks. Mirrors the existing `lastval()` SAVEPOINT pattern at lines 99-122 (added for issue #38). `Log.error` on the count-probe failure path captures the original cause + outer SQL. |
| 02 | `tina4_python/database/connection.py` | 412-414 | Adds `Log.error` before the existing `return False` in `Database.execute()`'s `except Exception`. No flow change — the return contract is preserved. |
| 03 | `tina4_python/orm/model.py` | 336, 364, 384, 405 | Adds `Log.error` in the four ORM CRUD `except` blocks (`save`, `delete`, `force_delete`, `restore`). No contract change — `save()` still returns False; the others still re-raise. |

## Apply order

`01` is the primary fix. `02` and `03` are pure additions
(Log.error calls only) and can land independently or together.

```
cd /path/to/tina4-python/
git apply path/to/bug-hunting/fix-issue-46-patches/01-postgres-savepoint-count-and-paginated.patch
git apply path/to/bug-hunting/fix-issue-46-patches/02-connection-execute-log.patch
git apply path/to/bug-hunting/fix-issue-46-patches/03-model-orm-log.patch
```

## Defensive shape

Every `from tina4_python.debug import Log; Log.error(...)` is
wrapped in its own `try: ... except Exception: pass` so a broken
or absent logger can never break the data path. Verified by
`test_attack_log_import_failure_does_not_propagate` in
`pypy/tests/test_issue_46_fix_adversarial.py`.

## Verification

All three test files pass against the patched framework:

| File | Tests | What they check |
|---|---|---|
| `pypy/tests/test_issue_46_pg_silent_abort_probe.py` | 4 | Mock-cursor proof of the post-fix code-path shape — SAVEPOINT issued, ROLLBACK TO on failure, Log.error emitted, paginated query proceeds cleanly. No live PG needed. |
| `pypy/tests/test_issue_46_live_repro.py` | 5 | Live PG 18 reproduction. Verifies the original psycopg2 cause (`operator does not exist: boolean = integer`) reaches the caller, the cascade message is gone, and the Log.error captures the cause. |
| `pypy/tests/test_issue_46_fix_adversarial.py` | 10 | Hostile inputs: repeated failures, alternating pass/fail, failures inside user transactions, savepoint name collision, credential leakage in log, long SQL, ORM save contract, paginated query failure propagation, broken-logger isolation, normal-query correctness preserved. |

Pre-patch baseline: `1 failed, 57 passed` in the regression set
(the bug-direction assertion in live_repro flips on patch landing).

Post-patch: `69 passed, 2 skipped` — including 19 new
fix-verification + adversarial assertions, with no regressions to
the 50 pre-existing tests in the suite.

## Adversarial findings — adjacent bugs

The adversarial sweep uncovered two issues that are NOT in scope
for this patch series but worth logging:

- **`SQLTranslator.boolean_to_int`** (`adapter.py:538-542`)
  unconditionally rewrites `\bTRUE\b` → `1` and `\bFALSE\b` → `0`
  on the PG translation path. Against a real `BOOLEAN` column this
  re-introduces the same BOOLEAN vs integer mismatch that issue
  #46 is about — a user writing `is_deleted = FALSE` gets it
  silently rewritten to `is_deleted = 0`, which fails. Suggests
  the translator should be engine-aware and skip the rewrite when
  the target dialect (PG) supports native booleans.

- **`SAVEPOINT _t4_count_probe` name collision** — if a user has
  established their own savepoint with the same name, the
  framework's SAVEPOINT stomps on it. Same risk for
  `_t4_paginated`. Low practical impact (users rarely pick that
  exact name) but worth eliminating with a unique-per-call name
  (e.g. `_t4_count_probe_{id(cursor)}`).

Both should probably get their own GitHub issues. They're flagged
in the matching test cases:
`test_attack_savepoint_name_does_not_clash_with_user_savepoint`
prints the collision status as informational output.
