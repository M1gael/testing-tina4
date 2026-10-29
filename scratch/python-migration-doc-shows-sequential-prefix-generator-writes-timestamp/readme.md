# python ch05 shows `000001_` migration names; the generator writes timestamps

Ledger row `d-orm-02`. Rebuilt 2026-10-29 on these tips: docs 01c4225, book 20b1006, py efa826a3,
php b321c1fc, rb 74aa1f5, nd b447252.

## Issue

Python ch05 in the docs (`docs/python/05-database.md`) and the book
(`book-1-python/chapters/05-database.md`) says `tina4 generate migration create_notes_table`
writes `migrations/000001_create_notes_table.sql` (+ `.down.sql`). It repeats that name at
:576, :577, :587, :606, :614 (twice), :775 and :792. Gotcha 5 (docs :1088, book :1103) says the
generator "auto-generates sequential numbers".

## Mechanism (read)

`tina4_python/cli/__init__.py:2205` sets `timestamp = ... now.strftime("%Y%m%d%H%M%S")`. :2226
builds `f"{timestamp}_{name}.sql"` and :2262 builds `f"{timestamp}_{name}.down.sql"`. The `tina4`
Rust CLI hands `generate` to `tina4python` (fw-cli `src/main.rs` ~1686-1706, read).

## Runs

- `generators.sh` → `generators.log`: all four generators write `YYYYMMDDHHMMSS_create_notes_table{,.down}.sql`.
  php's clock is UTC, the others use local time. The php, rb and nd ch05 docs already show 14-digit names (grep).
- `runner.sh` → `runner.log`: the python runner accepts hand-written `000001_`/`000002_` files,
  applies them in numeric order whatever order they were written in, and rolls them back
  through `.down.sql`. That is why the naming table keeps its Sequential row.
- `prove.sh`: runs the python generator to get the real prefix length, then checks every
  `<n>_create_notes_table` name in python ch05 has that length and gotcha 5 says timestamp, not
  sequential. Result in `prove.log`: stock docs and stock book each FAIL with 9 wrong (rc 1);
  docs and book with the fix applied both PASS (rc 0).
- `gate.sh` → `gate.log`: reverts each of the 7 hunks per patch on its own (14 reverts in all).
  All 14 turn the result red.

## Not covered by the fix (new findings)

- ch19-scaffolding (docs py/php/rb/nd and book 1-4) lists `migrations/20260401_create_product.sql`,
  an 8-digit prefix. `tina4python generate crud Product` writes `20261029114850_create_product.sql`.
- The python runner sorts by the integer value of the leading number (`migration/runner.py:670`), but ch05
  :565 and gotcha 5 say files sort "alphabetically". This is harmless when prefixes are zero-padded.
- ch32 `20260322_...` and php ch07 `003_...` are hand-written examples, not generator output.

## Re-run

    S=~/.cache/tina4-worktrees/verify-1029/d-orm-02
    DOCS=$S/stock/docs ./prove.sh; BOOK=$S/stock/book ./prove.sh   # FAIL, rc 1
    DOCS=$S/fixed/docs ./prove.sh; BOOK=$S/fixed/book ./prove.sh   # PASS, rc 0
    ./gate.sh; ./runner.sh; ./generators.sh

The venv, the php/nodejs copies and the trees all live in `$S`, not here.
