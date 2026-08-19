# known-issues

**[`ledger.md`](ledger.md) is the only bug log in this repo.** Every confirmed problem
in the Tina4 documentation and in framework code, across every language, one row each.
**105 rows** as of 2026-08-19 (see the header of `ledger.md` for the live status mix).

| File | What |
|---|---|
| [`ledger.md`](ledger.md) | The issue list. One row per bug or doc discrepancy. |
| [`suggested-fixes.md`](suggested-fixes.md) | Long-form `FIX-NN` proposals. Not a second issue list — the ledger's Suggested-fix column points here (`→ FIX-NN`). |

**Not here:**

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
2. **Version-stamp what you actually observed.** If you only re-read the source, the row is
   `pending-retest`, not `open` — a found-version is not a reproduced-version.
