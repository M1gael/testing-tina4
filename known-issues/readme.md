# known-issues

**Not a project — the shared record.** Every project in `testing-tina4/` logs its confirmed
findings *out* to here, and no project keeps a second list of its own. This is the one
directory that more than one project writes into; that is deliberate, and it is the only
exception to one-directory-per-project.

**[`ledger.md`](ledger.md) is the only bug log in this repo.** Every confirmed problem
in the Tina4 documentation and in framework code, across every language, one row each.
**116 rows** as of 2026-08-24 (see the header of `ledger.md` for the live status mix).

| File | What |
|---|---|
| [`ledger.md`](ledger.md) | The issue list. One row per bug or doc discrepancy. |
| [`suggested-fixes.md`](suggested-fixes.md) | Long-form `FIX-NN` proposals. Not a second issue list — the ledger's `Fix` column points here (`→ FIX-NN`). |

**Not here:**

- The proof that a row is real, and the fix built on it → [`scratch/`](../scratch/)
- Chapter coverage → [`documentation-testing/coverage-ledger/`](../documentation-testing/coverage-ledger/)
- Version-bump / retest history → [`documentation-testing/audit-log.md`](../documentation-testing/audit-log.md)
- Work backlog → [`documentation-testing/outstanding-tasks.md`](../documentation-testing/outstanding-tasks.md)

The `bug-hunting/`, `agent-testing/`, `codex/` and `comparison-testing/` directories were
removed on 2026-08-19. Everything issue-shaped in them was migrated into `ledger.md` first,
as self-contained rows carrying their own root cause, reproduction and suggested fix — so no
row depends on a directory that no longer exists. Recover the originals from git history.

A `PY-NN-NN` finding comes from walking a chapter. A `BH-<n>` row is an assigned hunt against an upstream `tina4-python` issue. Both are ledger rows. Never renumber a filed row.

## Adding a row

Schema, column meanings, and the rules are at the top of [`ledger.md`](ledger.md). The two that
get broken most often:

1. **Reproduce it before you write it.** How-to-reproduce is the command or the sequence, not
   prose. Rows reading *not recorded* need one written the next time anyone touches them.
2. **Version-stamp what you actually observed.** A found-version is not a reproduced-version.
   If you only re-read the source, say so in the `Version` cell rather than implying a run.
3. **Fill in `Port status` honestly.** Tina4 ships the same framework in six languages and the
   ports are translated from one another, so a defect found in one usually travelled with the
   translation. A row is not characterised until every port has been checked, and `clear` —
   checked, defect absent — is a finding worth recording, not an omission. Write `?` when
   nobody looked, and never write `clear` to make a row look finished.

## Rows that become fixes

A row is a claim. Before anyone writes a fix for it, the claim gets proven in its own project
under [`scratch/`](../scratch/) — reproduced on the released framework, explained down to the
`file:line` that causes it, and only then used to demonstrate that a candidate fix closes it.
That order is not bureaucracy: a fix built on a symptom rather than a mechanism is a guess, and
three of the fixes on this ledger were blocked in review for exactly that reason.

Note the proof project on the row, and keep the row the source of truth — `scratch/` is
disposable and its projects are deleted once a fix is merged. Anything that must survive the
project belongs in the row, self-contained, before the project goes.

There is no Status column — a row's state is whatever its ports say. A port reaches `filed#N`
only when an issue or PR is actually open in *that port's* repository. A fix sitting on a local
branch is `fixed`, and the Note must name the branch; that is a real state the old schema could
not express, so branch work used to read as though nothing had been done.

All ten Tina4 checkouts live in `gitdir/tinaforks/`, so a cross-port check needs no cloning —
see that directory's `CLAUDE.md` for the layout and the fork-freshness rule. Keeping them in
one directory is load-bearing: `sync-tina4-skills.sh` finds siblings relative to its own repo
and silently compares nothing when they are split (`ALL-FW-05`).
