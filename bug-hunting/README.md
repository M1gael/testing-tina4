# `bug-hunting/` directory

Deep-dive analysis files for each Bug Hunt finding. The **canonical
log** lives in [`findings-log.md` → Bug Hunt section](../findings-log.md#bug-hunt--bh-n-rows);
this directory holds the long-form evidence the table rows there
link out to.

Findings are documented in directories (`issue-<n>/`) where `<n>` is the
upstream GitHub issue number on
[`tina4stack/tina4-python`](https://github.com/tina4stack/tina4-python/issues).

Each issue directory contains `patches.md` (main investigation / report) along with related comments and patch files.

## Companion probes

Probes live alongside the rest of the test suite in
`documentation-testing/pypy/tests/`, named `test_issue_<n>_<slug>.py`.
They follow the existing bug-direction convention: assertions PASS in
the buggy steady state today and FAIL when the upstream fix lands —
regression sentinel.

## Branch scope

**This directory is tracked on `main`** (40 files). The two-branch split
described in `CLAUDE.md` — scratch investigation on a `bug-hunting`
branch, refined work on `main` — was never carried out: no `bug-hunting`
branch exists locally or on `origin`. Rough investigation work has been
landing directly on `main` alongside the refined probes.

Either create the branch and move the scratch work onto it, or drop the
two-branch convention from `CLAUDE.md`. Until one of those happens,
`main` is the only branch and this note is the accurate description.

## Current investigations

See the **Bug Hunt** section in [`findings-log.md`](../findings-log.md#bug-hunt--bh-n-rows)
for the live table. Directories in this folder:

- `issue-46/` — [BH-46](https://github.com/tina4stack/tina4-python/issues/46), live-reproduced + **patches drafted** (see `issue-46/patches.md`)
- `issue-47/` — [BH-47](https://github.com/tina4stack/tina4-python/issues/47), doc gap (see `issue-47/patches.md`)
- `issue-48/` — [BH-48](https://github.com/tina4stack/tina4-python/issues/48), table relation investigation (see `issue-48/patches.md`)
- `issue-49/` — [BH-49](https://github.com/tina4stack/tina4-python/issues/49), follow-up gaps (see `issue-49/patches.md`)
- `serve-port/` — `tina4 serve 7150` positional argument vs `-p` flag investigation (see `serve-port/patches.md`)
- `debug-false/` — `TINA4_DEBUG=false` browser-open onto a 404, dev-toolbar off-switch, footer route count, and Ask-Tina4 GitHub-vs-docs link (see `debug-false/README.md`; runnable repro app + probes in `debug-false/repro/`)
