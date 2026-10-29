# 19-scaffolding documents `--with-*` flags that `generate model` rejects

Ledger row `d-cli-02`. Rebuilt 2026-10-29 on these tips: docs `01c4225`, book `20b1006`,
py `efa826a3`, php `b321c1fc`, rb `74aa1f5`, nd `b447252` (each origin/v3), tina4 CLI `ebb846b`
(built from source, reports 3.8.112; the installed 3.8.77 was not used).

## The issue

The "Combining Generators" section of `19-scaffolding.md` is the same in docs (python, php, ruby,
nodejs) and book (book-1..4). It shows
`generate model Product --fields "..." --with-route --with-migration` and a table of
`--with-route/-migration/-test/-form/-view`. It also says "`generate crud` is equivalent to all
`--with` flags". None of these flags exist. Every port's `generate model` exits 1 with
`Unknown option --with-route for "generate model".` (run).

## Mechanism (read, at the tips)

- `generate model` takes only `fields`, `table-name` and `no-migration`. See py
  `tina4_python/cli/__init__.py:4155`, php `bin/tina4php:2047`, rb `lib/tina4/cli.rb:46` and nd
  `packages/cli/src/commands/generate.ts:659`. Any other flag goes to the unknown-option error
  (py `:549`, rb `:333`).
- The tina4 CLI forwards `generate` without changing it. In `src/main.rs:317-326` an
  `external_subcommand` goes to `:530`, then to `delegate_command` `:1790`, which does
  `cmd_args.extend(args)` `:1808`. The 2026-10-22 pointer `main.rs:438` is stale. The behaviour
  is the same. Run: the shims log argv, and every `tina4 ...` command reached the framework CLI
  verbatim (`. forwarded verbatim:` lines in the logs).

## Files

- `setup.sh` builds the runtime OUTSIDE scratch, in `~/.cache/tina4-worktrees/verify-1029/d-cli-02`.
  It holds copies of fw-*, a py venv, php vendor, ruby gems, the node build, the ebb846b CLI, and
  argv-logging shims. HOME is redirected.
- `prove.sh` takes `DOCS=<docs tree|none> BOOK=<book tree|none>` and returns rc 1 when wrong docs
  are found. It runs each section's bash commands exactly as written, in a fresh marker project
  per port. It checks the files each command claims to make. It probes every `--with...` token
  against `generate model`. It checks each prose claim: migration by default, `--no-migration`,
  `generate form|view|test`, "no form", and `generate crud` making the full set.
- `gate.sh` and `revert_group.py` revert each piece of the held fix alone. The 8 pieces are the
  files, and the 4 hunk groups are intro, block, table and crud. `revert_group.py` with all 4
  groups reproduces stock byte for byte.
- Logs: `stock-docs.log`, `stock-book.log`, `fixed-docs.log`, `fixed-book.log`, `gate.log`.

## Results (run)

    stock docs  VERDICT: FAIL ok=0 bad=4
    stock book  VERDICT: FAIL ok=0 bad=4
    fixed docs  VERDICT: PASS ok=4 bad=0
    fixed book  VERDICT: PASS ok=4 bad=0
    gate        red=12 green=0

The intro and crud groups go red only because their prose names the bare `--with` flag, and
`generate model ... --with` is rejected.

## Remaining instances outside 19-scaffolding

Scope: grep `--with` across the whole stock docs and book trees.

- 31-cli in docs python/ruby/nodejs and book-1/3/4 has `--with-route` and `--with-migration`.
  This is row d-cli-05 and is not counted against this fix. php 31-cli has no hits.
- `34-deployment` (ruby) matches only `bundle install --without` (false positive).

## Also seen (run, not in this fix)

19-scaffolding Model section, py `:174`, says "No routes, no templates, no tests". In fact
`generate model` writes a model test in all four ports (`tests/test_product_model.py`, etc.).
This is already noted under d-cli-05.
