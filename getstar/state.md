# State — last updated 2026-08-13

Resume file. Everything needed to pick this up cold, without the conversation that
produced it. Read `README.md` for the convention, `python-evaluation.md` for the audit,
`python-refinement.md` for the plan.

## Where we are

**The restructure was rejected. The correction work was salvaged onto the old structure.**

Andre did not want the new page shape (user, 2026-08-12: "my boss is not a fan of the new
structure, so instead we will go back to the old docs but backport any fixes for syntax or
logical faults, framework mismatches, or inconsistencies"). So the three-page split, the
separate quick-reference page, the sidebar entry, the measured comparison table and every
editorial rewrite are **abandoned**. What survives is the factual corrections, re-applied to
the upstream pages, verified again from scratch against 3.13.98.

Two fresh branches were cut off current `origin/main` — the old docs, untouched structure —
and the corrections hand-applied. Cherry-pick was not usable: the target prose had been
rewritten underneath the fix commits.

| Repo | Branch | Commits | Contents |
|---|---|---|---|
| `tina4-documentation` | `docs/python-consistency-fixes` | 1, `6f176d9` | `docs/python/index.md` — the old quick-reference landing page, structure intact (38 headings before and after, same order), ~30 factual corrections; `docs/python/01-getting-started.md` re-synced from the book |
| `tina4-book` | `docs/python-consistency-fixes` | 1, `5ebe35b` | `book-1-python/chapters/01-getting-started.md` — old 12-section structure intact, output blocks re-captured, wrong defaults fixed, one section added (`tina4 doctor`) |

The superseded branches are **kept, not deleted** — they are the only record of the
restructure and of the measurement work: `docs/python-entry` (15 commits, `32da3ec` pushed to
the fork) and `docs/python-getting-started` (11 commits, never pushed).

**Both PRs are open** (USER instruction 2026-08-13, "if everything looks good make the pull
request" — this supersedes the earlier Andre gate):

- book — <https://github.com/tina4stack/tina4-book/pull/152> · 1 file, +162/-115
- docs — <https://github.com/tina4stack/tina4-documentation/pull/50> · 2 files, +305/-182

Both `MERGEABLE`, cross-linked by a comment on 152. **They must land together** —
`sync-books.sh` regenerates `docs/python/01-getting-started.md` from the book chapter, so
merging one alone loses the other. Both forks were synced level with upstream before pushing.

Three things are flagged in the PR bodies rather than buried: the `expect_*` question (below),
that the two must merge together, and that `TINA4_INIT_NO_SERVE` is deliberately undocumented
because the env gate structurally cannot accept a CLI-only variable.

Site builds clean (272 pages — one fewer than the restructure, since `quick-reference.md` is
gone again). Preview with `npm run docs:dev` in the docs repo
(`http://localhost:5180/python/`) — `pnpm` is not installed here despite the `packageManager`
field, `npm` works.

**Every correction was re-verified for this pass, not trusted from the earlier notes**, and
two of the earlier "fixes" turned out to be wrong and were dropped:

- `@cached` above `@get` is **correct** as the old page had it. `_register_route` returns the
  original function, so a decorator applied above the route decorator still marks the
  registered object. The earlier reorder was unnecessary churn.
- memcached sessions need **no client package**. The handler speaks the memcached text
  protocol over a socket. The earlier fix listed `pymemcache`.

One correction reverses a deliberate upstream commit and is flagged in the commit message:
upstream `10a1e3d` renamed the inline `@tests` builders `assert_*` → `expect_*` in the docs
site, but `tina4_python.Testing` defines `assert_*` on both 3.13.94 and 3.13.98, so the page
as printed raises `NameError` on every released version. This pass uses the names that exist.

**The quick reference was fact-checked by execution, not reading, and 15 of its 36 sections
were wrong** — nine would have failed outright for a reader. Full table:
`python-evaluation.md` section 2a. Every correction was verified against a running server
before it was written.

**The comparison table is measured but published nowhere.** It went out with the restructure
and is *not* in the open PRs. Feature-matched app in four frameworks, all verified 7/7 before
counting: Tina4 56 lines / 0 added packages / 1 distribution / 3.4 MB, against Flask
100 / 3 / 17 / 17.9 MB, FastAPI 86 / 4 / 18 / 24.7 MB, Django 76 / 3 / 16 / 30.6 MB. Harness
and full write-up: [`comparison-testing/`](../comparison-testing/), run
[`results/2026-08-11-python.md`](../comparison-testing/results/2026-08-11-python.md). Still a
real measurement and still worth a home — see G8 for candidates.

**Structure is NOT agreed.** Andre's 2026-08-07 feedback shaped the restructure, and he then
rejected the result on 2026-08-12. The live structure is upstream's own.

**Hard rule set by the user 2026-08-11: the documentation states intended behaviour only.**
Framework defects are fixed separately and never described on the page — not as a gotcha, not
as a "note", not as history of a bug already fixed. Corrections to *wrong* statements stay
(the API name, the port, the tool count); explanations of *broken* behaviour go to
[`outstanding-tasks.md`](../outstanding-tasks.md) G1/G1a instead. Two passes were needed to
honour this: the first removed the defects I had written up, the second swept all three pages
again and found six more in the quick reference and one in chapter 1, including a paragraph on
a session-backend fallback that predated this work. Re-read the pages with this rule in mind
before any future publish.

**Working rule set by the user 2026-08-07:** decide structure now, resolve the detail while
writing the pages. Do not stockpile measurements in these files ahead of the pages that
use them.

## Decisions locked

**Withdrawn 2026-08-12 — items 2 to 10 below describe the rejected restructure.** They are
kept because they record why each choice was made, and because the sibling-language work in
G6 would have copied this shape. Do not act on them. The live decision is: old structure,
factual corrections only.

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
| tina4-book | `/var/home/work/gitdir/tina4-book` | `docs/python-consistency-fixes` | `f2b92b9` (1 ahead of `origin/main` `2818c2f`) |
| tina4-documentation | `/var/home/work/gitdir/tina4-documentation` | `docs/python-consistency-fixes` | `c76e5f5` (1 ahead of `origin/main` `d9ed4be`) |
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
- The docs copy of ch1 differs from the book copy by exactly two site-only things: the title carries no `Chapter 1:` prefix, and a `<div v-pre>` / `</div>` pair wraps the numbered list in *How Template Rendering Works* so VitePress does not interpolate its `{{ }}` and `{% %}`. Re-generate the docs copy from the book by applying only those two, never by hand-editing both.
- Closed 2026-08-12: the `CORS_ORIGINS` / `*` / "all origins allowed" row in the book. It is now `TINA4_CORS_ORIGINS` / unset / deny-by-default in both copies.

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

1. **Watch CI on both PRs.** `scripts/audit-truth.py` could not be run fully here: it wants all
   four framework source trees checked out beside the docs repo and only `tina4-js/src` is
   present, so its env-var check reported 215 pre-existing flags that a provisioned runner
   should resolve. The punctuation gate is genuinely clean, and nothing this change introduces
   is flagged. If CI disagrees, read its output rather than trusting the local run.
2. **Answer the `expect_*` question on docs PR 50** — see G10. It is the one substantive
   decision left in the change and a maintainer has to make it.
3. **Refresh the review handoff** if Andre wants it on paper: `~/Downloads/Tina4 New Docs/`
   still holds the three *restructured* pages, which are obsolete. Replace with the two current
   pages (`/python/` and `/python/01-getting-started/`) and re-print together — a stale PDF is
   indistinguishable from a current one.
4. **Decide what happens to the abandoned branches.** `docs/python-entry` is already on the
   fork at `32da3ec`; leaving it there advertises a structure that was rejected. Either delete
   the fork branch or leave it and say so.
5. Then the backlog: [`outstanding-tasks.md`](../outstanding-tasks.md) G1-G9, plus the two new
   items G10 and G11 logged on 2026-08-12. G2 is now the live one — the same class of error sits
   unfixed on the other five languages' quick-reference pages, and this pass is the template for
   fixing them.
