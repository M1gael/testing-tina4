# known-issues

**The shared record, not a project.** Every project in `testing-tina4/` logs confirmed findings
here; none keeps its own list.

| File | What |
|---|---|
| [`ledger.md`](ledger.md) | The only issue list — one row per bug or doc discrepancy, schema at its top. |
| [`ledger-check.py`](ledger-check.py) | Run after every ledger edit: `python3 known-issues/ledger-check.py --write`. |
| [`suggested-fixes.md`](suggested-fixes.md) | Long `FIX-NN` proposals the ledger's `Fix` column points to. |

Not here: proofs and candidate fixes → [`scratch/`](../scratch/); chapter coverage →
`documentation-testing/coverage-ledger/`; retest history → `documentation-testing/audit-log.md`;
backlog → `documentation-testing/outstanding-tasks.md`.

## Adding a row

1. **Reproduce first.** `Reproduce` is a command, not prose.
2. **Version what you observed** — say if only the source was read.
3. **`Port status` honestly.** Check every port; `clear` is a finding, `?` means nobody looked.
4. **`Doc verified` per port**, only once that port is settled. A page fault the fix doesn't
   address is a new `d-` row, never an edit.
5. **`Status`, `Issue`, `Cause`, `Origin`** filled at creation — one line each; say if the report
   came from Windows; `Not recorded.` beats a guess.
6. **Never delete a row.**

Before a fix, prove the row in `scratch/` — reproduced on released code, explained to
`file:line`. Scratch is disposable; move anything that must survive into the row first.

## The ledger at every step — mandatory

**Before a step:** read the row; re-check its PRs live (`gh pr view` — nothing tells us about a
merge), the upstream tip, and whether the maintainer fixed it (`git log -S` / `--grep`). Fix the
row if it is wrong.

**After each step, update the row, dated, then run `ledger-check.py --write`:**

| Step | Row change |
|---|---|
| reproduced / checked absent on a port | `Port status` `affected`/`clear`, `Version`, `Reproduce` |
| mechanism found | `Cause`; detail in the Note |
| work picked up | `Status` (`Investigating`, `Fixing`, ...) |
| fix written, gated, attacked | port `fixed`; Note: branch, commit, base commit |
| all short of the PR done | `Status` `Ready`; Note per the ledger's `Ready` bar |
| PR opened from the fork | `filed#N`, `Status` `Filed` |
| CI finished and read (`statusCheckRollup`) | Note |
| merged | `merged#N`, `Status` by what is still owed |
| doc page read | that port's `Doc verified` |
| scratch deleted | Note says so — only once the row stands alone |

Can't update when it happens? Update before the next step. Why: on 2026-09-23 five merged PRs
still read `filed` because rows were left for later.

**`Ready` is where our fixes normally stop** until the user says PR. Uncommitted fixes go to
`~/.cache/tina4-worktrees/<name>/fix.patch` — `gitdir/tinaforks/` is not backed up.

All ten checkouts live in `gitdir/tinaforks/` (layout and fork-refresh rule in its `CLAUDE.md`);
keep them together or `sync-tina4-skills.sh` silently compares nothing (`ALL-FW-05`).
