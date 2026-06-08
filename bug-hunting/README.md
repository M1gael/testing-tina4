# `bug-hunting/` directory

Deep-dive analysis files for each Bug Hunt finding. The **canonical
log** lives in [`readme.md` → Bug Hunt section](../readme.md#bug-hunt);
this directory holds the long-form evidence the table rows there
link out to.

One file per finding, named `issue-<n>-<slug>.md` where `<n>` is the
upstream GitHub issue number on
[`tina4stack/tina4-python`](https://github.com/tina4stack/tina4-python/issues).

Each file contains:
- Reporter's symptom (verbatim quote where available)
- Root cause with file:line references into `tina4_python/`
- Adversarial verification trail (what disproof attempts were tried)
- Empirical confirmation (links to the matching probe files in `pypy/tests/`)
- Recommended fix shape
- Draft upstream comment ready to paste into the GitHub issue

## Companion probes

Probes live alongside the rest of the test suite in `pypy/tests/`,
named `test_issue_<n>_<slug>.py`. They follow the existing
bug-direction convention: assertions PASS in the buggy steady state
today and FAIL when the upstream fix lands — regression sentinel.

## Branch scope

This directory exists only on the `bug-hunting` branch.
`main` stays silver-lined for documentation-fidelity work; framework
defects investigated on user request land here.

## Current investigations

See the **Bug Hunt** section in [`readme.md`](../readme.md#bug-hunt)
for the live table. Files in this directory at time of writing:

- `issue-46-pg-silent-abort.md` — [BH-46](https://github.com/tina4stack/tina4-python/issues/46), live-reproduced + **patches drafted**
- `fix-issue-46-patches/` — 3 unified diffs + README ready for upstream PR (see `fix-issue-46-patches/README.md`)
- `issue-47-psycopg2-dep-gap.md` — [BH-47](https://github.com/tina4stack/tina4-python/issues/47), doc gap
