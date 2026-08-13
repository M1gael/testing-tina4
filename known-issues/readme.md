# known-issues

**[`ledger.md`](ledger.md) is the single home for issues in this repo** — every confirmed problem
in the Tina4 documentation and in framework code, across every language, one row each. 84 rows as
of 2026-08-13.

## What moved here, on 2026-08-13

| From | Rows |
|---|---|
| `findings-log.md` → `## Known Issues Log` | 67 — Python doc-fidelity `PY-NN-NN` and bug-hunt `BH-<n>` |
| `agent-testing/codex-skill-delivery/README.md` → `CODX-01`..`07` | 7 — re-coded `CLI-FW-05`..`11` |
| Backlog rows G1 / G1a / G4 / G10 / G11 | 10 — issues that had only ever been described as *work* |

The move added four columns the old log never had: **Kind** (documentation or framework),
**Language**, the version each issue was **last reproduced on**, and **how to reproduce it**. It
kept every column that carried content — `Filed`, with all 39 upstream links intact, and
`Suggested fix`, whose `→ FIX-NN` pointers still resolve into `findings-log.md` →
*Suggested Fixes*.

**Codes did not change.** A `PY-18-03` or `BH-46` quoted in an upstream GitHub issue still
resolves to the same row. Never renumber a filed row.

## What stayed where it was

- **`findings-log.md`** keeps the Evaluation Progress table, the audit-pass narrative, the Bug Hunt
  index, and the long-form `FIX-NN` proposals. Its Known Issues Log section is now a pointer here.
- **`bug-hunting/`** keeps the long-form evidence per assigned `BH-<n>` investigation.
- **`coverage-ledger/`** keeps per-chapter ✓/⚠/⛔/⏸ coverage. A `⚠ diverges` cell cites an issue
  code; the issue itself lives here.
- **`agent-testing/unverified-leads.md`** stays a triage queue. Those entries are *unverified
  leads*, not confirmed issues — two are already duplicates of ledger rows and the rest have no
  quoted documented claim behind them. A lead earns a row here only once it has been reproduced.
- **`outstanding-tasks.md`** tracks the *work*; this ledger tracks the *issue*. Rows cross-reference
  each other so neither drifts.

## Adding a row

Schema, column meanings, and the rules are at the top of [`ledger.md`](ledger.md). The two that
get broken most often:

1. **Reproduce it before you write it.** How-to-reproduce is the command or the sequence, not
   prose. 54 of the 84 rows have one; the rest are marked for backfill.
2. **Version-stamp what you actually observed.** If you only re-read the source, the row is
   `pending-retest`, not `open` — a found-version is not a reproduced-version.
