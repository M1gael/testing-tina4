# getstar

Working notes for rebuilding the Getting Started entry of every Tina4 language
section. Nothing here ships. Edits land in `tina4-book` (chapters) and
`tina4-documentation` (site-only pages, nav, sidebar).

**Goal.** Each language section on tina4.com needs one honest entry path for
someone touching Tina4 for the first time in that language: how to install it,
how it works, a small working program, and — the part that is missing today — why
a developer already using Flask, Laravel, Rails, or Express should care. Fewer
lines of code? Fewer dependencies? Faster? The claim has to be measured, not asserted.

Order of work: **Python first**, then the shape that lands there becomes the
template for PHP, Ruby, Node.js, JavaScript, and Delphi.

## Two files per language

Every language gets exactly two documents, in this order. Never mix them — the
split is what keeps proposals from quietly becoming "findings".

### 1. `<lang>-evaluation.md` — what is there

The audit. Describes the current state of that language's entry pages and nothing
else. No proposals, no rewrites, no opinions about what should replace it.

Must contain:

- The funnel a new user actually walks: nav click → page → page, with line counts.
- Page-by-page state: what each page is, how long, what the first screenful shows.
- Duplication: which sections already exist as chapters.
- Defects: dead links (HTTP-checked), stale versions, invented command output, claims that contradict a real run.
- The gap against the goal: install / how it works / mock program / why — present or absent.
- Reusable assets already on the site.

Every claim carries an evidence tag:

| Tag | Means |
|---|---|
| `[LIVE]` | HTTP-checked against `https://tina4.com` |
| `[REPO]` | Read from `tina4-book@origin/main` or `tina4-documentation@origin/main` |
| `[RUN]` | Measured on this machine — real scaffold, real server, real request |
| `[SRC]` | Read from the installed framework source |

An untagged claim is not a finding.

### 2. `<lang>-refinement.md` — what we will do

The proposal. Two parts, in this order:

**Part 1 — the proposal.** What changes, page by page: which page takes which job,
what moves, what gets deleted, what gets written from scratch, target line counts.
Names the repo and path each edit lands in. States the risks (PDF pipeline, the
book → docs sync, generated sidebar, links that break). Alternatives considered,
with the reason each lost.

**Part 2 — the example refined structure.** Below the proposal, the concrete
skeleton of the pages the proposal asks for: every heading in order, one line of
intent under each, and the real content for anything load-bearing (the pitch
numbers, the mock program, the exit links). Enough that writing the page becomes
transcription, not invention.

Numbers quoted in Part 2 are either already measured (tagged as in the evaluation)
or marked `TODO(measure)`. A refinement file never invents a number.

### Plus one file for the whole project

`state.md` — where the work stands: decisions locked, decisions open, the git and fork
setup, how to reproduce the measurements, and the next actions in order. It is the resume
file; read it first after a break. Keep it current, because the two per-language
documents deliberately say nothing about process.

## Status

| Language | Evaluation | Refinement | Shipped |
|---|---|---|---|
| Python | `python-evaluation.md` | `python-refinement.md` | not started — see `state.md` |
| PHP | — | — | — |
| Ruby | — | — | — |
| Node.js | — | — | — |
| JavaScript (tina4-js) | — | — | — |
| Delphi | — | — | — |

## Where edits land

| Content | Repo | Note |
|---|---|---|
| Chapters (`01-getting-started.md` …) | `tina4-book/book-N-<lang>/chapters/` | upstream source; also feeds the downloadable PDF via `scripts/build_pdf.py` |
| Section landing pages (`docs/<lang>/index.md`), hub, comparisons | `tina4-documentation/docs/` | site-only — never reaches the PDF |
| Nav and sidebar groups | `tina4-documentation/tina4press.config.mjs` | sidebar groups are generated from chapter stems |

`tina4-documentation/scripts/sync-books.sh` copies book chapters into `docs/` and
escapes Twig for VitePress. It runs book → docs, so a site-only fix in `docs/`
is lost on the next sync unless it is upstreamed into the book first.
