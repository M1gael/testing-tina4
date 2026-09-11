# `tina4 init` runs off bare `$PATH`, so two installs scaffold nothing

`2026-09-11 · baseline-main v0.2.0-290-gd719fc3 · scratch v0.2.0-295-g9d159fe · tina4 CLI 3.8.77 · node v22.22.2`

Ledger row: `run-22` (harness, high, affected since 2026-09-04).

## The behaviour

`phaseScaffold` issues the first CLI call of every build:

```ts
// app.ts:5060
const initRes = await runTool("run_shell", { cmd: `tina4 init python ${backendDir}` }, ctx);
```

The `run_shell` dispatch (`src/app/tools.ts:2417-2428` on `d719fc3`) hands that straight to
`runShell()`. It never calls `usesTina4Cli` / `ensureTina4` / `resolveTina4InCommand` — the three
that `spawn_service` calls twelve hundred lines earlier, at `tools.ts:2080`, under a comment that
says exactly why: *"a client may not have it on PATH — resolve/download it and rewrite the
command."* Those three are called from that one site and nowhere else.

So the command runs as whatever bare `tina4` `$PATH` yields.

## Why it is not simply "PATH is fine, everyone has tina4"

`app.ts:151` widens `PATH` at boot, before any tool runs — homebrew, `/usr/local/bin`,
`~/.local/bin`, `~/.bun/bin`, `~/.cargo/bin`, `/usr/bin`, `/bin`. That covers where a **human**
installs a CLI, and it is why this defect has never been seen on a developer's machine.

It covers neither place the **agent itself** owns:

| | |
|---|---|
| `dirname(process.execPath)` | the hand-delivered bundle — DISTRIBUTION.md ships `tina4` beside the executable |
| `~/.tina4-simple-agent/bin` | where `ensureTina4()`'s download lands (`tools.ts:692`) |

Both are `tina4Candidates()` entries, so **resolution would have found the binary**. Nothing asked
it to.

## What actually happens next — milder than the ledger row said, and worse

`tina4 init` exits 127, `initOk` is false, and the build does not stop. It takes the `else` at
`app.ts:5230`:

```
⚠ tina4 init unavailable — generating from scratch (boilerplate may need a fix).
```

Everything inside `if (initOk)` is skipped with it — including the `tina4 generate model` /
`generate seeder` calls, which are correctly resolved through `ensureTina4()` but are never
reached. So on those two installs the agent silently builds **with no Tina4 scaffolding at all**,
which is the one thing Andre's priority #1 is about, and the only signal is a single activity line.

## Reproduce

```sh
node repro.mjs                                               # untouched main -> exit 1
T4_TREE=…/tina4-simple-agent-work/scratch node repro.mjs      # patched        -> exit 0
node attack.mjs                                              # 12 cells
```

Four boxes, one factor varied — where the binary is. Box A and D are built inside a mount
namespace with `/usr/local/bin` masked by an empty directory, so this host's real CLI cannot leak
in and make a run pass for the wrong reason.

| box | binary at | `d719fc3` | patched |
|---|---|---|---|
| A | `~/.tina4-simple-agent/bin` (downloaded) | `exit 127` | runs |
| B | `~/.local/bin` (human install) | runs | runs |
| C | `/usr/local/bin` (this host) | runs | runs |
| D | beside the executable (hand-delivered) | `exit 127` | runs |

## The fix

`src/app/tools.ts`, in the `run_shell` dispatch — the same three calls `spawn_service` makes,
placed **after** `longRunningRefusal`. Order is load-bearing: the refusal matches a
command-position `tina4`, and a rewritten `"/path/tina4" serve` is no longer in that shape, so
resolving first would let `tina4 serve` past the guard and hang for the full 60s timeout. That is
cell 1 of `attack.mjs`.

Regression test lives with the project's own, in `test/tina4-cli-resolution.mjs` — that suite
already tested the helpers and `spawn_service` exhaustively, and was green over this the whole
time. Its blind spot *was* the defect.

## Verified

- `repro.mjs` exit 1 on `d719fc3`, exit 0 patched.
- `attack.mjs` 12/12 patched; **6/12 on `d719fc3`**, and the six that pass there are the
  no-regression cells (guard fires, non-command-position `tina4` untouched) — they are meant to
  pass on both.
- `npm run test:tina4cli` 16/16 patched. Reverting only `tools.ts` and keeping the new test:
  15/16, the dispatch case failing `exit 127`. Restored byte-identical (`diff -q` against the
  saved patch).
- `npm test` 34/34, `tsc --noEmit` clean.
- **Round-tripped on a real project.** `tina4 init python .` into a throwaway dir, then
  `uv run tina4 migrate` both bare and rewritten: both print `Nothing to migrate.`, and
  `uv run which tina4` is `/usr/local/bin/tina4`. The venv ships `tina4python`, **not** `tina4`,
  so `uv run tina4` was already falling through to `$PATH` — rewriting it to the absolute path of
  that same binary changes nothing. This mattered: the harness sends `uv run tina4 migrate` and
  `uv run tina4 seed` through `run_shell` (`app.ts:4590`, `:5023`), and they are now rewritten too.

## Residual

- **Precedence can change which binary runs.** `tina4Candidates()` checks its fixed locations
  before `PATH`, so on a box with a CLI in *both*, the rewrite runs the fixed-location one where
  bare `tina4` ran the `PATH` one. Same precedence `spawn_service` has always had; cell 8 of
  `attack.mjs` exists to record it, not to complain about it.
- `findWorkingTina4()` tests `isFile`, not executability. A non-executable file named `tina4` in a
  candidate directory is selected and then fails to run. Pre-existing; now reachable from
  `run_shell` too.
- `phaseScaffold` itself was **not** driven — that needs a model. The call site was verified by
  reading; everything below it by running.
- `.env`-supplied values are not involved here (this is a tool dispatch, not boot).

## Mistakes worth keeping

- **The first cap timer had no `.unref()`**, so every probe run cost the full 60s cap *after*
  already having its answer. It looked like a hang in the code under test. It was in the probe.
- **The first attack run reported `1/10` — and that one PASS was vacuous.** `unshare` was being
  handed `-r-m`, nothing ran, and every field came back `undefined`; one cell's assertion was
  satisfied by `undefined`. A cell that cannot run must FAIL, never pass. Same trap as the
  secret-dialog probe, second time.
- **The `uv run` cell failed against the fixed tree for an environment reason** — `uv` lives in
  `/usr/local/bin`, which the cell masks. It was measuring `uv`, not the rewrite. Fixed by
  planting a stand-in `uv`, not by dropping the cell.
