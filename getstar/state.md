# State — last updated 2026-08-11

Resume file. Everything needed to pick this up cold, without the conversation that
produced it. Read `README.md` for the convention, `python-evaluation.md` for the audit,
`python-refinement.md` for the plan.

## Where we are

**The Python section is content-complete.** All three pages written, the comparison table
measured and published on the landing page. Two branches; only the first docs commit has been
pushed. No PR opened.

| Repo | Branch | Commits | Contents |
|---|---|---|---|
| `tina4-documentation` | `docs/python-entry` | `32da3ec` (pushed) + `3b51667` + `ea658f5` (local) | `docs/python/index.md` rewritten as the argument and carrying the measured comparison table; `docs/python/quick-reference.md` created then fact-corrected; `tina4press.config.mjs` sidebar stem; synced copy of the new ch1 |
| `tina4-book` | `docs/python-getting-started` | `484d014` + `9e95bdc` (both local, never pushed) | `book-1-python/chapters/01-getting-started.md` rewritten 1132 to 637 lines, why-block carrying the comparison result |

Site builds clean (273 pages) and `scripts/audit-truth.py` passes. Preview with
`npm run docs:dev` in the docs repo (`http://localhost:5180/python/`) — `pnpm` is not
installed here despite the `packageManager` field, `npm` works.

**The quick reference was fact-checked by execution, not reading, and 15 of its 36 sections
were wrong** — nine would have failed outright for a reader. Full table:
`python-evaluation.md` section 2a. Every correction was verified against a running server
before it was written.

**The comparison table is measured and on the page.** Feature-matched app in four
frameworks, all verified 7/7 before counting: Tina4 56 lines / 0 added packages / 1
distribution / 3.4 MB, against Flask 100 / 3 / 17 / 17.9 MB, FastAPI 86 / 4 / 18 / 24.7 MB,
Django 76 / 3 / 16 / 30.6 MB. Harness and full write-up:
[`comparison-testing/`](../comparison-testing/), run
[`results/2026-08-11-python.md`](../comparison-testing/results/2026-08-11-python.md).
The page also states what Tina4 loses on, including that its generated OpenAPI carries no
request-body schema.

Structure is agreed, including Andre's feedback of 2026-08-07.

**Working rule set by the user 2026-08-07:** decide structure now, resolve the detail while
writing the pages. Do not stockpile measurements in these files ahead of the pages that
use them.

## Decisions locked

1. **Scope**: the `tina4.com/python/` section only. Not the site landing, not `/get-started/`. Other languages come after Python, copying whatever shape Python lands on.
2. **Three pages**, each with one job:
   - `/python/` → "Why Tina4 instead of Flask": the argument and the mental model, for a reader already committed to Python. No setup steps. `tina4-documentation/docs/python/index.md`, ~200 lines.
   - `/python/01-getting-started/` → the mechanics: install assuming nothing, run it, how the CLI works, a **First App**, links out for depth. `tina4-book/book-1-python/chapters/01-getting-started.md`, ~480 lines.
   - `/python/quick-reference/` → per-chapter finder, ~760 lines after correction. Its own page, filed under the sidebar's `Reference` group. `tina4-documentation/docs/python/quick-reference.md`.
3. **The quick reference is kept, moved and corrected** — Andre, 2026-08-07: "it serves as a quick finder". It stops being the landing page and becomes its own page under Overview (user, 2026-08-07). Three entries are wrong today and get fixed in the move (`ServiceRunner` vs "services are not necessary"; `.twig` vs `.html`; `init` "opens your browser" vs the `[Y/n]` prompt).
4. **One install story**, in ch1 only. `/python/` gets a three-line "in a hurry" teaser with no output blocks.
5. **The First App lives in ch1** — one JSON endpoint plus one templated page (bookmarks), in-memory, no database. Its POST needs `@noauth()`, and ch1 must say why: Tina4 closes non-GET routes by default.
6. **The why is mirrored into ch1 as 8 lines** (three numbers + a link), because `docs/*/index.md` is site-only and never reaches the PDF. The only sanctioned duplication in the plan.
7. **Ship on a fork branch and iterate**, rather than perfecting the plan first.
8. **Comparisons must be feature-matched** — Andre, 2026-08-07: "compare apples with apples … if you need Swagger + auth + database = dependencies". The comparison app carries a database, a JWT-protected write and Swagger docs; whatever the comparatives add to reach parity is counted and named. Spec: `python-refinement.md` → *Comparison measurement spec*.
9. **No throughput figure at all.** `hey` is absent here and this is not the Apple Silicon box behind the March 2026 run. The landing page names the weakness without quoting a number, and does not link `/comparisons/` — upstream de-linked that page pending re-benchmarking.
10. **ch1 §9–11 are cut, not relocated.** ch2 (1 011 ln) and ch3 (1 000 ln) already own every subsection, and both already carry an exercise plus solution. No PR to ch2/ch3 needed.

**Withdrawn: the "fewer lines of code" pitch.** A first attempt measured a three-route app
with no database, auth or Swagger — the one shape where Flask and FastAPI need no extra
packages — and Tina4 saved nothing. Wrong benchmark, not a result. Nothing publishes until
the feature-matched build runs. Andre has been told the tie bullet is withdrawn.

## Decisions open

None for the Python section. Everything deferred is logged in
[`outstanding-tasks.md`](../outstanding-tasks.md) → *Deferred from the Getting Started
rebuild* as G1–G6, on USER direction 2026-08-11 ("problems for later, focusing on tina4 docs
only now").

Closed 2026-08-11:

- **Quick-reference sidebar slot** — filed under the existing `Reference` group, not a new first group. `autoSectionSidebar` renders only the first group open (`collapsed: i !== 0`), so a top group would have collapsed Foundations and pushed Getting Started a click further away, which is the opposite of the point. Verified after rebuild: Foundations first and open, Quick Reference under Reference, no orphan "More" group.
- **The hard-coded "Overview" sidebar label** — accepted by the USER. Logged as G3 so nobody re-investigates.
- **Two CLI defects** — resolved while writing §4: `tina4 test` is documented with its verified fix (`uv add pytest`), `tina4 routes` is left out because `/__dev` does that job. Logged as G4.

## Git and environment, as of 2026-08-11

| Repo | Path | Branch | HEAD |
|---|---|---|---|
| tina4-book | `/var/home/work/gitdir/tina4-book` | `docs/python-getting-started` | `9e95bdc` (2 ahead of `origin/main` `2818c2f`) |
| tina4-documentation | `/var/home/work/gitdir/tina4-documentation` | `docs/python-entry` | `ea658f5` (3 ahead of `origin/main` `dfbbde1`) |
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

Versions behind everything published on 2026-08-07: `tina4` CLI **3.8.67**, `tina4-python`
**3.13.95**, CPython **3.14.5**. Anything tagged 2026-08-06 was measured on CLI 3.8.64 /
tina4-python 3.13.94 and has been superseded — the two figures that changed are the install
size (4.9 MB was inflated by `__pycache__` from a prior run; a fresh 3.13.95 install is
**3.9 MB / 105 `.py` files**) and the `/health` body, which on 3.13.95 is
`{"status":"ok","version":"3.13.95","uptime":0.94,"framework":"tina4-python"}` — the shape
the old docs already had, so the 3.13.94 payload I measured was the outlier. The scaffolded
`.env` also gained a third line (`TINA4_DATABASE_URL=sqlite:///app.db`).

Re-measure before publishing anything if the CLI or framework has moved again.

The Postgres fixture, queue brokers and the `documentation-testing/pypy` workspace
described in the repo's `CLAUDE.md` are **not needed** for this project.

## Boundary against the QA harness

This directory writes documentation; the rest of `testing-tina4` audits it. Findings
uncovered here (for example the two CLI defects) are **not Known Issues Log material** as
they stand — the KI Log requires a quoted documented claim tested inside
`documentation-testing/`. Re-test there if any of them should earn a `PY-NN-NN` ID.

## Next actions, in order

The Python section is content-complete. What is left is mechanical or belongs to
[`outstanding-tasks.md`](../outstanding-tasks.md) G1-G6.

1. Push `docs/python-entry` (tina4-documentation) and `docs/python-getting-started` (tina4-book) to the `MichaelC8E` forks and open both PRs against `tina4stack`. Neither has been pushed since the comparison table landed.
2. Review the rendered pages before the PRs go out: `npm run docs:dev` in `tina4-documentation`, then `/python/`, `/python/quick-reference` and `/python/01-getting-started` on the printed port.
3. Then G1-G6: the two framework defects, the five sibling language pages, throughput, and repeating the shape for PHP / Ruby / Node.js / JavaScript / Delphi.
