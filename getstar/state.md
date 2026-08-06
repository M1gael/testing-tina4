# State — last updated 2026-08-06

Resume file. Everything needed to pick this up cold, without the conversation that
produced it. Read `README.md` for the convention, `python-evaluation.md` for the audit,
`python-refinement.md` for the plan.

## Where we are

Python evaluation and refinement are drafted. Nothing has been written into
`tina4-book` or `tina4-documentation` yet. Next step is implementation on a fork branch,
iterating — the plan is expected to change as pages get written.

## Decisions locked

1. **Scope**: the `tina4.com/python/` section only. Not the site landing, not `/get-started/`. Other languages come after Python, copying whatever shape Python lands on.
2. **Two pages**, each with one job:
   - `/python/` → "Why Tina4 for Python": the argument and the mental model. No setup steps. `tina4-documentation/docs/python/index.md`, ~200 lines.
   - `/python/01-getting-started/` → the mechanics: install assuming nothing, run it, how the CLI works, smallest working app, links out for depth. `tina4-book/book-1-python/chapters/01-getting-started.md`, ~480 lines.
3. **The 621-line cheatsheet at `/python/` is retired, not relocated.** Every section duplicates a chapter; ch38 (Complete Feature List, 97 features with "instead of <dependency>" notes) already does the reference job; nothing links into it; it has drifted wrong in at least three places.
4. **One install story**, in ch1 only. `/python/` gets a three-line "in a hurry" teaser with no output blocks.
5. **The mock program lives in ch1** — one JSON endpoint plus one templated page (bookmarks), in-memory, no database.
6. **The why is mirrored into ch1 as 8 lines** (three numbers + a link), because `docs/*/index.md` is site-only and never reaches the PDF. The only sanctioned duplication in the plan.
7. **Ship on a fork branch and iterate**, rather than perfecting the plan first.

## Decisions open

1. **LOC table** — build it (spec: `python-refinement.md` → *LOC measurement spec*) or pitch on packages / install size / features only?
2. **Throughput numbers** — re-run `benchmark/benchmark.sh` here, cite the March 2026 Apple Silicon run, or link `/comparisons/` and keep no figure on the page?
3. **ch1 §9–11** (~400 lines: request/response fundamentals, exercise, solutions) — relocate into chapters 2–3 in this pass, or cut from ch1 and log the move?
4. **Two CLI defects found while measuring** — `tina4 routes` in a fresh project prints the "Tina4 must be started with the tina4 CLI" guard instead of listing routes; `tina4 test` fails with `No module named pytest` because the scaffold ships no test runner. Document the workaround in ch1, or leave both commands out until they are fixed upstream?

## Git and environment, as of 2026-08-06

| Repo | Path | Branch | HEAD |
|---|---|---|---|
| tina4-book | `/var/home/work/gitdir/tina4-book` | `main` | `d0d3cef` |
| tina4-documentation | `/var/home/work/gitdir/tina4-documentation` | `main` | `ca3feb6` |
| tina4-dev-admin | `/var/home/work/gitdir/tina4-dev-admin` | `main` | `61a15d6` |
| tina4-js | `/var/home/work/gitdir/tina4-js` | `master` | `1434721` |

- All four clones have **only `origin`** (= `git@github-work:tina4stack/<repo>.git`). The `fork` remotes were removed on 2026-08-06.
- `gh` is authenticated as **MichaelC8E**. **No push access to any `tina4stack` repo** (`push=false`), so every change ships as a PR from the fork `MichaelC8E/<repo>`.
- All four forks were synced level with upstream on 2026-08-06 (`ahead=0 behind=0`) and their merged branches deleted.
- Fork branches deliberately left in place because they hold commits upstream does not have: `tina4-dev-admin` → `fix-dashboard-issues` (2 commits, also in the local clone, nowhere else); `tina4-js` → `fix/js-docs`, `release/1.5.1`, two `snyk-upgrade-*`.

Working flow for this project:

```bash
# once per repo, when starting to write
git -C /var/home/work/gitdir/tina4-documentation remote add fork git@github-work:MichaelC8E/tina4-documentation.git
git -C /var/home/work/gitdir/tina4-book          remote add fork git@github-work:MichaelC8E/tina4-book.git

# per change
git -C <repo> checkout -b docs/python-entry origin/main
# edit, commit
git -C <repo> push -u fork docs/python-entry
gh pr create --repo tina4stack/<repo> --head MichaelC8E:docs/python-entry

# keep a fork level with upstream (fast-forward; --force if it ever diverges)
gh repo sync MichaelC8E/<repo> --source tina4stack/<repo>
```

Commit messages from this machine must not reference `owner/repo#NNN` — see the account
separation rule in the user's memory.

## How the two repos fit together

- `tina4-book/book-N-<lang>/chapters/NN-*.md` is the **only** source for numbered chapters. `tina4-documentation/scripts/sync-books.sh` runs book → docs: `rm -f docs/<lang>/[0-9]*.md`, then re-copies from the book, escaping Twig for VitePress. Chapter edits made in the docs repo are destroyed on the next sync.
- `docs/<lang>/index.md`, `docs/get-started.md`, `docs/comparisons.md` and `tina4press.config.mjs` exist only in the docs repo; the sync preserves non-numbered files.
- `tina4-book/scripts/build_pdf.py` globs `chapters/NN-*.md` per `book.yml`, so only chapters reach the downloadable PDF.
- Known drift to fix in the book before any sync: `docs/python/01-getting-started.md` has a `TINA4_CORS_ORIGINS` / unset / deny-by-default row where the book still says `CORS_ORIGINS` / `*` / "all origins allowed".

## Evidence and how to reproduce it

Every `[RUN]` fact in the two Python files came from a real scaffold at
`/tmp/claude-1001/-var-home-work-gitdir-testing-tina4-getstar/49318f5d-0fde-4979-8459-a67cb2c05901/scratchpad/demo/my-store`.
That path is session-scoped and may be gone; recreate with:

```bash
tina4 init python my-store        # answer N to "Start the server now?"
cd my-store && tina4 serve        # banner, /health, /swagger, /__dev
```

Versions behind the measurements: `tina4` CLI **3.8.64** (3.8.67 available),
`tina4-python` **3.13.94**, CPython **3.14.5**. The measured values are tabulated in
`python-refinement.md` → *Fact inventory*; re-measure before publishing if the CLI or
framework has moved.

The Postgres fixture, queue brokers and the `documentation-testing/pypy` workspace
described in the repo's `CLAUDE.md` are **not needed** for this project.

## Boundary against the QA harness

This directory writes documentation; the rest of `testing-tina4` audits it. Findings
uncovered here (for example the two CLI defects) are **not Known Issues Log material** as
they stand — the KI Log requires a quoted documented claim tested inside
`documentation-testing/`. Re-test there if any of them should earn a `PY-NN-NN` ID.

## Next actions, in order

1. Settle the four open decisions.
2. Add the `fork` remote to `tina4-documentation`, branch `docs/python-entry` off `origin/main`, and write `docs/python/index.md` from `python-refinement.md` Part 2 — replacing the cheatsheet, not adding to it.
3. `npm i && npm run docs:build` in `tina4-documentation` to confirm `tina4press` 0.1.9 renders the retitled `index.md` correctly in the sidebar (it currently hard-labels it "Overview").
4. Branch `tina4-book` and rewrite `book-1-python/chapters/01-getting-started.md` against Part 2, re-running each command block so no output is invented.
5. If the LOC row survives decision 1, build the four apps per the LOC spec and record the measurement here before quoting it.
6. Open the two PRs, then repeat the shape for PHP, Ruby, Node.js, JavaScript, Delphi.
