# State — last updated 2026-08-07

Resume file. Everything needed to pick this up cold, without the conversation that
produced it. Read `README.md` for the convention, `python-evaluation.md` for the audit,
`python-refinement.md` for the plan.

## Where we are

**The docs-repo half is written and pushed.** Branch `docs/python-entry` on
`MichaelC8E/tina4-documentation`, commit `32da3ec`: `docs/python/index.md` rewritten as the
argument, `docs/python/quick-reference.md` created from the finder that used to occupy it,
`tina4press.config.mjs` given the `quick-reference` stem. Builds clean (273 pages) and the
`audit-truth.py` CLI gate passes. No PR opened. Preview with `npm run docs:dev` in the
docs repo (`http://localhost:5180/python/`); `pnpm` is not installed on this machine
despite the `packageManager` field, `npm` works.

**Still to write:** `tina4-book/book-1-python/chapters/01-getting-started.md`, and the
feature-matched comparison table the landing page currently leaves out.

Structure is agreed, including Andre's feedback of 2026-08-07.

**Working rule set by the user 2026-08-07:** decide structure now, resolve the detail while
writing the pages. Do not stockpile measurements in these files ahead of the pages that
use them.

## Decisions locked

1. **Scope**: the `tina4.com/python/` section only. Not the site landing, not `/get-started/`. Other languages come after Python, copying whatever shape Python lands on.
2. **Three pages**, each with one job:
   - `/python/` → "Why Tina4 instead of Flask": the argument and the mental model, for a reader already committed to Python. No setup steps. `tina4-documentation/docs/python/index.md`, ~200 lines.
   - `/python/01-getting-started/` → the mechanics: install assuming nothing, run it, how the CLI works, a **First App**, links out for depth. `tina4-book/book-1-python/chapters/01-getting-started.md`, ~480 lines.
   - `/python/quick-reference/` → per-chapter finder, ~610 lines. Kept, its own page under Overview. `tina4-documentation/docs/python/quick-reference.md`.
3. **The quick reference is kept, moved and corrected** — Andre, 2026-08-07: "it serves as a quick finder". It stops being the landing page and becomes its own page under Overview (user, 2026-08-07). Three entries are wrong today and get fixed in the move (`ServiceRunner` vs "services are not necessary"; `.twig` vs `.html`; `init` "opens your browser" vs the `[Y/n]` prompt).
4. **One install story**, in ch1 only. `/python/` gets a three-line "in a hurry" teaser with no output blocks.
5. **The First App lives in ch1** — one JSON endpoint plus one templated page (bookmarks), in-memory, no database. Its POST needs `@noauth()`, and ch1 must say why: Tina4 closes non-GET routes by default.
6. **The why is mirrored into ch1 as 8 lines** (three numbers + a link), because `docs/*/index.md` is site-only and never reaches the PDF. The only sanctioned duplication in the plan.
7. **Ship on a fork branch and iterate**, rather than perfecting the plan first.
8. **Comparisons must be feature-matched** — Andre, 2026-08-07: "compare apples with apples … if you need Swagger + auth + database = dependencies". The comparison app carries a database, a JWT-protected write and Swagger docs; whatever the comparatives add to reach parity is counted and named. Spec: `python-refinement.md` → *Comparison measurement spec*.
9. **No throughput re-run.** `hey` absent here, and this is not the Apple Silicon box behind the March 2026 figures. Cite with the date, link `/comparisons/`.
10. **ch1 §9–11 are cut, not relocated.** ch2 (1 011 ln) and ch3 (1 000 ln) already own every subsection, and both already carry an exercise plus solution. No PR to ch2/ch3 needed.

**Withdrawn: the "fewer lines of code" pitch.** A first attempt measured a three-route app
with no database, auth or Swagger — the one shape where Flask and FastAPI need no extra
packages — and Tina4 saved nothing. Wrong benchmark, not a result. Nothing publishes until
the feature-matched build runs. Andre has been told the tie bullet is withdrawn.

## Decisions open

1. **Where the quick reference sits in the generated sidebar.** Placement as a page is settled; its sidebar slot is not. From `tina4press@0.1.14/src/sidebar.js`: only the first group renders open (`collapsed: i !== 0`), so a new first group puts it under Overview but collapses Foundations and hides Getting Started. Alternative: add the stem to the existing `Reference` group — right meaning, bottom of the sidebar. Options and code refs: `python-refinement.md` → *Moving the quick reference*.
2. **The landing page's sidebar label is hard-coded "Overview"** — `items: [{ text: "Overview", link: indexPage.url }]`, and `titleFromPage()` is never called for it. Retitling `index.md` changes the page, not the nav. Accept the mismatch, or land a small `tina4press` change (fourth repo — follow-up, not a blocker).
3. **Two CLI defects found while measuring** — `tina4 routes` in a fresh project prints the "Tina4 must be started with the tina4 CLI" guard instead of listing routes; `tina4 test` fails with `No module named pytest` because the scaffold ships no test runner. Document the workaround in ch1, or leave both commands out until they are fixed upstream. Resolve while writing §4.

## Git and environment, as of 2026-08-06

| Repo | Path | Branch | HEAD |
|---|---|---|---|
| tina4-book | `/var/home/work/gitdir/tina4-book` | `main` | `2818c2f` |
| tina4-documentation | `/var/home/work/gitdir/tina4-documentation` | `docs/python-entry` | `32da3ec` (1 ahead of `origin/main` `dfbbde1`) |
| tina4-dev-admin | `/var/home/work/gitdir/tina4-dev-admin` | `main` | `61a15d6` |
| tina4-js | `/var/home/work/gitdir/tina4-js` | `master` | `1434721` |

All four pulled level with their remotes on 2026-08-07. `MichaelC8E/tina4-documentation`
is level with upstream at `dfbbde1` and carries `docs/python-entry` at `32da3ec`. No PR
opened.

**Do not trust an earlier read of these repos across a session.** On 2026-08-07 the
documentation clone was 13 commits behind and the stale copy nearly shipped: `origin/main`
had de-linked `/comparisons` pending re-benchmarking and added a CI gate
(`scripts/audit-truth.py`, fails on any `tina4 <cmd>` or `TINA4_*` absent from source).
Re-read before quoting.

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

1. **Look at the render and decide the sidebar trade.** Quick Reference is the first group, so it renders open and Foundations is now collapsed — Getting Started is one click further away than before. Flip by moving the stem into the `Reference` group if that reads worse.
2. Branch `tina4-book` and rewrite `book-1-python/chapters/01-getting-started.md` against Part 2, re-running each command block so no output is invented. Note the chapter must teach `@noauth()` — its First App POST returns 401 without it.
3. Build the four feature-matched comparison apps per the *Comparison measurement spec* — database, JWT-protected write, Swagger — and record the measurement before any figure reaches a page. Naming each added package per framework is the argument. The landing page has a placeholder callout where the table goes.
4. Decide the `tina4press` question: the landing page's sidebar item is hard-labelled "Overview" and cannot be retitled from this repo.
5. Open the PRs, then repeat the shape for PHP, Ruby, Node.js, JavaScript, Delphi. `BACKEND_GROUPS` already carries the `quick-reference` stem for all four backend languages.
