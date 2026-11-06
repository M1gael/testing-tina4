# 31-cli documents `generate model` flags that every port rejects

Ledger row `d-cli-05`. Run 2026-11-06 on these tips: docs `dfa88c2`, book `f74ab1e`. The ports
are py `13fae160`, php `3cf80d5c`, rb `85b72d7` and nd `e8cdfd3` (each origin/v3). The tina4 CLI is
`b02475f` (origin/main, built from source, reports 3.8.114).

## The issue

`31-cli.md` exists in docs (python, php, ruby, nodejs) and book (book-1..4), and the two copies
are near-identical. Several things in it are wrong:

- The `generate model` Options table lists `--auto-crud`, `--soft-delete` and `--with-route`
  (php: the first two).
- Section 8, "Generate All at Once", runs `generate model Product --with-route --with-migration`.
  On ruby it runs `generate:crud Product`, which is an unknown command.
- The section 13/16/17 exercise does the same for `Customer`.

Every one of these exits 1 with `Unknown option --with-route for "generate model".` (or
`Unknown command: generate:crud`).

The `Created ...` output blocks under `generate model` and `generate route` also name files the
command does not write:

- nodejs writes `src/models/`, not `src/orm/`.
- nodejs `generate route` writes `src/routes/api/<name>/{get,post,[id]/...}.ts`.
- Python writes `Product.py`, not `product.py`.
- Migrations are named `create_<table>.sql` and come with a `.down.sql`.
- A test or spec is written in every port.
- php `generate route Order` writes `src/routes/Order.php`.

## Mechanism (read, at the tips)

Each `generate model` spec allows only `fields`, `table-name` and `no-migration`. Anything else
goes to the unknown-option error. The global `--dry-run`, `--json` and `--help` are accepted.

| Port | Flag spec | Unknown-option error |
|---|---|---|
| py | `tina4_python/cli/__init__.py:4160` | `:549` |
| php | `bin/tina4php:2047` | `:2020` |
| rb | `lib/tina4/cli.rb:46` | `:333` |
| nd | `packages/cli/src/commands/generate.ts:659` | — |

None of `--with-route` or `--soft-delete` ever existed in any port's history (`git log -S`).
`--auto-crud` appears only as a ruby/php feature name, never as a flag. The tina4 CLI forwards
`generate` verbatim. `shim.log` showed 40 of 40 calls reaching the framework CLI unchanged.

## Files

- `setup.sh` builds the runtime outside scratch, in `~/.cache/tina4-worktrees/docs-cli05/rt`.
- `probe.sh` runs each documented form through `tina4`, then prints the rc, the first line and
  the files written. Its output is in `stock-probe.log`.
- `prove.py <docs|book tree>` runs each check and exits 1 on any wrong claim. The checks are:
  - every `tina4 generate model|route` line in a bash fence, run as written;
  - each `Created` block that follows such a fence, compared with the files actually written;
  - every flag in the Options table;
  - the note under the table.
- `gate.sh` reverts one piece of the fix at a time (on a copy).

## Results (run)

    stock docs  VERDICT: FAIL ok=21 bad=28
    stock book  VERDICT: FAIL ok=21 bad=28
    fixed docs  VERDICT: PASS ok=66 bad=0
    fixed book  VERDICT: PASS ok=66 bad=0
    gate        6 pieces, each red alone

The fix is `~/.cache/tina4-worktrees/docs-cli05/fix.patch` (docs) and `fix.book.patch` (book).

## Not covered

- Code blocks inside the sections, such as the model bodies (`table_name = "products"` against
  the generated `product`) and the single-file `-- UP/-- DOWN` migration. They were not run.
  The migration point overlaps `d-cli-07`.
- Ruby section 7 uses `generate:middleware`, which is unknown.
- The exercise's `curl` steps, and `5 commands` (now 6 lines).
- The `init` output listing `src/orm/` for nodejs.
