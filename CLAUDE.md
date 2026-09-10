# testing-tina4

Where work goes in this repo and the repos it acts on. `grindfix` and `grindimplement` are
project-agnostic and read this file for the routing they used to hardcode.

## Investigations

`scratch/` — one sub-directory per issue, named for the behaviour it proves, not for the fix.
**`scratch/readme.md` is the authority on the layout**; read it before creating a directory.

This tree is evidence, not a source tree. The framework here is read-only: record defects,
never fix them in place.

## Fixes and features

The branch lands in `../tinaforks/<repo>`, cut from the **current upstream** branch, never from
the fork's own tip.

| Repo | Develops on |
|---|---|
| `tina4-python`, `tina4-php`, `tina4-ruby`, `tina4-nodejs` | `v3` — their `origin/main` is a stale 3.1.x |
| `tina4` (Rust CLI) | `main` |

Remotes there: `origin` = upstream `tina4stack/<repo>`, `fork` = our own.

## Findings

Every finding gets a row in `known-issues/ledger.md`. A scratch project corresponds to a row;
it does not replace one. "File it" means write the row — never open a PR or an issue upstream.
