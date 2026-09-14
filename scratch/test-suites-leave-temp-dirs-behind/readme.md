# The test suites leave temp directories behind — `dx-04`

2026-09-14 · measured on `v0.2.0-300-gd3e4b76` · fixed on `scratch` `f0448bd`

## What it actually leaks

Counted, not estimated: `count.sh` before and after one `npm run test:unit` + one `turn-harness`.

| prefix | per run | source |
|---|---|---|
| `t4a-guards-*` | 7 | `test/write-guards.mjs:25` — one per case, no removal anywhere |
| `t4a-state-*` | 1 | `test/turn-harness.mjs:101` — the child's state dir; the projects root IS removed at `:393` |
| `wc-*` | 1 | `test/write-checks.mjs:81` — **the row missed this one**, because the original count only looked for `t4a-` |
| **total** | **9** | → **0** after the fix |

Everything else that makes a temp dir already removes it: `ideation`, `tina4-cli-resolution`,
`spawn-service-dispatch`, `build-e2e-live`, and the app's own `chk_*` syntax-check files.

## The half that matters more than the leak

Every removal that did exist was `try { rm } catch {}`. A removal that failed and a clean run
printed exactly the same thing, so the workspace could lie and look identical either way.
`test/tmpdirs.mjs` removes and then **reads each path back**; survivors come back named and the
suite reports them as its own failure.

## Files

| file | what it answers |
|---|---|
| `count.sh` | how many are on disk, by prefix |
| `gate.mjs` | revert each cleanup alone — does `/tmp` fill again? **3/3** |
| `does-the-cleanup-report-its-own-failure.mjs` | make a directory genuinely unremovable (a child inside a read-only parent) — is it **named**, or swallowed? PASS |

The last one skips itself with a loud verdict if run as root, because root ignores the permission
the whole test depends on.
