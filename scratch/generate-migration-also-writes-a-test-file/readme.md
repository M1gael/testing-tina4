# ch05 says `generate migration` writes two files; for a `create_` name it writes three

Ledger row `d-orm-04`. Run 2026-11-02 on: docs 2c09454, book 20b1006 (origin/main);
py 8fbc2254, php b367197f, rb 50c5d2b, nd 44d433c (origin/v3).

## Issue

Every port's ch05 "Generating a Migration" section (docs `docs/<lang>/05-database.md`, book
`book-N-<lang>/chapters/05-database.md`) runs `tina4 generate migration create_<x>` and says it
writes two files, the up `.sql` and the `.down.sql`. Each generator also writes a test that applies
the up SQL then the down SQL against SQLite — but only when the name starts with `create_`.

## Mechanism (read; confirmed by generators.sh)

- py `tina4_python/cli/__init__.py:2224` `is_create = name.startswith("create_") or fields_override`; :2274 emits the test.
- php `bin/tina4php:3577` / :3640.  rb `lib/tina4/cli.rb:2447` / :2505.  nd `packages/cli/src/commands/generate.ts:1484` / :1556.

`generators.log`: `create_notes_table` writes `migrations/<ts>_create_notes_table{,.down}.sql` plus
py `tests/test_notes_table_migration.py`, php `tests/NotesTableMigrationTest.php`,
rb `spec/notes_table_migration_spec.rb`, nd `tests/notes_table_migration.test.ts`.
`add_category_to_product` writes only the two SQL files in every port.

## Proof

`prove.sh` (DOCS= or BOOK= tree root) runs each port's generator with the name the page uses, and
checks the section names every written file, has no wrong file count, and that its "non-create
names write two files" sentence holds. `prove.log`: stock docs and book FAIL ok=0 bad=4 (rc 1);
fixed both PASS ok=4 bad=0 (rc 0). Missing php/ruby/node/python3 or a generator failure = ERROR rc 2.
`gate.sh` reverts each of the 8 fixed pages alone: red=8 green=0 (`gate.log`).
`apply_fix.py <tree>` reproduces the fix on a stock tree byte-for-byte.

## Runtime (outside scratch)

`R=~/.cache/tina4-worktrees/grind-1102/dorm04`: `fw-<lang>` = `git archive origin/v3`; php
`composer install --no-dev`; nodejs `node_modules` hardlinked from verify-1029/d-cli-03 (relative
@tina4 self-links). HOME is redirected to `$R/home` / a temp dir.

## Not covered (new findings)

- The co-emitted test asserts the table the generator derived (`notes_table` for
  `create_notes_table`), but ch05 has readers write `CREATE TABLE notes` / `products`, so the test
  goes red as soon as the chapter's SQL is pasted in.
- ch31 section 6 (py/rb/nd + book) says `generate migration` writes "a timestamped migration file
  with UP and DOWN sections"; it writes separate up/down files (plus the test).
- python ch05 still shows `000001_` names (d-orm-02, separate patch; the two touch adjacent lines).
