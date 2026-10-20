# A failed ORM save() rolls back the caller's whole transaction (php)

Found 2026-10-19 while checking a report that ORM `save()` on SQLite reports success but rows do not persist on php 3.13.151 (regression claimed from 3.13.132, broken at 3.13.150).

## Result

- The reported regression is **not reproduced**. A plain `save()` persists on every tree tested.
- A `save()` made inside a caller's explicit transaction is durable only at the caller's `commit()`. Documented nested-transaction behaviour, not a defect.
- **Defect:** a failed `save()` inside a caller's explicit transaction issues a real ROLLBACK. The caller's earlier successful `save()` is discarded, and the caller's `commit()` still returns normally.

Trees (all `git worktree add --detach`, `HOME` redirected): tina4-php v3 `77156098` (tip, 2026-10-19), tags `3.13.151`, `3.13.150`, `3.13.132`. Results identical across all four unless stated.

## Mechanism (read, then run)

- `Tina4/ORM.php:869` `save()` calls `$this->_db->startTransaction()`.
- `Tina4/Database/Database.php:1277-1285`: a begin while a transaction is open only increments `txDepth`. No BEGIN is issued.
- `Tina4/Database/Database.php:1316-1318`: `commit()` at depth > 1 only decrements. No COMMIT. The write becomes durable at the caller's outer commit. The WARNING logged at `:1279` says so.
- `Tina4/ORM.php:888` (failure branch) and `:901` (exception branch) call `$this->_db->rollback()`.
- `Tina4/Database/Database.php:1349` `rollback()` never checks `txDepth`. It calls the adapter's rollback, which rolls back the whole transaction, and releases the pin (`:361`).

## Runs

`nested-rollback.php`: first `save()` succeeds (same=1); second `save()` fails with `NOT NULL constraint failed: company.name` (returned false); caller `commit()` returns ok; afterwards same=0 fresh=0. Same on 132, 150, 151, tip.

`repro.php <tree> <workdir> null <plain|outer|outer-rollback> [pool]`:
- `plain`: `save()` persists (fresh=2). Same on all four trees, autocommit 1/0/unset, pool 0/2.
- `outer`: inside a caller's transaction, `save()` returns a model, same=2 fresh=1; after `commit()`, fresh=2. Same on all four trees.
- `outer-rollback`: caller `rollback()` discards it (fresh=1, the earlier row only). Same on all four trees.
- `TINA4_AUTOCOMMIT` (1/0/unset) changes none of the above.

Read: `ORM.php` never calls `getNextId`; the sequence-collision hypothesis from the report does not apply to ORM inserts.

## Bounds

- php only. py, rb, nd, js not checked.
- SQLite file DBs only. `:memory:` and other drivers not run.
- Versions tested: 3.13.132, 3.13.150, 3.13.151, tip. Tags between not run.
- The reporter's own code (ModelCollection migration, test harness, login service) was not available. Whether it opens an outer transaction, or whether a save fails inside one, is unknown.
- Not reproduced: a same-connection read returning null after a plain `save()`.
