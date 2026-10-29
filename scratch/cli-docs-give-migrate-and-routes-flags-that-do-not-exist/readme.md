# CLI docs give migrate and routes flags that do not exist

Ledger row `d-cli-04`. Found by the Android Termux sweep, reproduced here on host Linux.
Rebuilt 2026-10-28 on the current upstream tips (the first version was deleted by a cleanup).

## Issue

The CLI, routing and architecture pages, in all four language guides and in the book, tell the
reader to run commands that no framework CLI accepts:

| Documented | What the CLI does (all four ports) | Real form |
|---|---|---|
| `tina4 migrate --rollback` | `Unknown option --rollback` (ruby: `--rollback needs a value`) | `tina4 migrate:rollback` |
| `tina4 migrate --status` | `Unknown option --status` | `tina4 migrate:status` |
| `tina4 routes --method POST` / `--filter` / `--middleware` | `Unknown option` | none: `routes` takes no options |
| php flag table: `--rollback-all` | `Unknown option` | none |
| ruby `tina4 migrate:reset` / `migrate:fresh` | `Unknown command` | none |

Every rejected form exits 1; every colon form exits 0. The docs' own database chapters
(`05-database.md`) already use `migrate:rollback` / `migrate:status`.

## Mechanism

- The `tina4` client forwards any command it does not own verbatim to the framework CLI:
  tina4 `src/main.rs:314-323` (`External`, "the framework owns arg parsing and rejects unknowns"),
  dispatch `:526`, `delegate_command` `:1787`. It used to translate `migrate --rollback/--status`;
  commit 072d7d7 dropped that on purpose.
- The framework CLIs declare `migrate` and `routes` without those flags, and the colon subcommands:
  python `tina4_python/cli/__init__.py:4178-4184` (rejection message `:549`); php `bin/tina4php:2071-2076`;
  ruby `lib/tina4/cli.rb:99-110` (`migrate` takes only `--create NAME`, `--rollback N`); nodejs
  `packages/cli/src/bin.ts:369-391`.

So this is a docs defect: the code's surface is uniform, deliberate and self-described.

Code-side, not fixed here (generate-migration hints that print wrong commands, still true at the tips):
python `cli/__init__.py:1400-1401` prints `tina4 migrate --rollback` / `--status`;
ruby `cli.rb:555-556` prints `tina4ruby migrate status` / `migrate rollback`, and `migrate rollback`
silently runs `migrate` ("No pending migrations", rc 0).

## Proof

- `cli.sh <py|php|rb|nd> args...` runs that port's real framework CLI from a worktree at the upstream
  tip (`~/.cache/tina4-worktrees/dcli04-stock-{python,php,ruby,nodejs}`; nothing installed here).
- `prove.sh` extracts every `tina4 migrate*` / `tina4 routes` command from the pages (`doccmds.py`:
  fenced blocks and inline code, verbatim) and runs each in a fresh project with a SQLite DB and its own
  HOME. BAD = the CLI's parser rejects it. `DOCS=` / `BOOK=` select trees; default is origin/main.
- `forward.sh` runs `tina4 <cmd>` through the real client with each framework CLI replaced by an
  argv-logging shim, showing the client passes the documented argv through unchanged. `TINA4=` picks
  the binary.

Pinned: tina4-python efa826a3, tina4-php b321c1fc, tina4-ruby 74aa1f5, tina4-nodejs b447252,
tina4 client main 47ac777 (3.8.109, built in `~/.cache/tina4-worktrees/dcli04-tina4-target`) and
installed 3.8.77, docs 98c70a4, book 20b1006.

```
bash prove.sh                                       # stock: VERDICT ok=64 bad=71, exit 1
#   18 migrate --rollback, 7 migrate --status, 16 routes --method, 18 routes --filter,
#    8 routes --middleware, 2 migrate:reset, 2 migrate:fresh
DOCS=~/.cache/tina4-worktrees/docfix-dcli04-docs \
BOOK=~/.cache/tina4-worktrees/docfix-dcli04-book bash prove.sh   # fixed: VERDICT ok=89 bad=0, exit 0
TINA4=~/.cache/tina4-worktrees/dcli04-tina4-target/release/tina4 bash forward.sh
#   16/16 verbatim; the three flag forms rc=1 in every port, migrate:rollback rc=0
```

Per-piece gating (whole fix minus one piece, via `apply_fix.py`): without migrate bad=23;
without routes bad=42; without ruby reset/fresh bad=4; without the php table bad=4 (its
`migrate --rollback` / `--status` examples, and `--rollback-all` returns).

## Fix

`apply_fix.py <docs|book> <root> [pieces]` reproduces `~/.cache/tina4-worktrees/docfix-dcli04-{docs,book}.fix.patch`
byte for byte on the tips (uncommitted, branch `docs/dcli04-fix` in `docfix-dcli04-docs` / `-book`):
colon form for rollback/status; drop the routes Filtering examples and the 02-routing `--method`/`--filter`
samples; php solution step becomes plain `tina4 routes`; php flag table becomes a two-row Related Commands
table; drop ruby "Other Migration Commands". Left alone: the 36-releases note (historical, the client
translated then) and ruby `migrate --create` (works). Implementing a routes filter instead is the
maintainer's call. Site build on the fixed docs: `tina4press build .` built 283 pages, rc 0.
