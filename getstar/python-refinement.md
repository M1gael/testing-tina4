# Python — suggested refinement

Proposal for `tina4.com/python/`, built on `python-evaluation.md`. Part 1 is what we
do and why; Part 2 is the skeleton to write against.

Supersedes an earlier draft that put the pitch *and* the install on `/python/`. The
split below gives each page one job and keeps exactly one install story.

---

# Part 1 — The proposal

## Page set

| Page | Job | Repo / path | Target |
|---|---|---|---|
| `/python/` — "Why Tina4 for Python" | The argument and the mental model. No setup steps. | `tina4-documentation/docs/python/index.md` | ~200 lines |
| `/python/01-getting-started/` | The mechanics, assuming nothing: install, run, CLI, smallest working app. | `tina4-book/book-1-python/chapters/01-getting-started.md` | ~480 lines |

Two pages. The 621-line cheatsheet currently living at `/python/` is **retired, not
relocated** — see *The cheatsheet* below.

Nav "Python" keeps pointing at `/python/`, so the argument is the first thing a
newcomer reads. Chapter numbering and every chapter URL stay as they are.

## Division of labour

Four rules that keep the pages from re-merging over time:

1. **`/python/` shows, ch1 tells you to type.** Code on the landing page is illustration — read it, do not run it. Every command the reader executes lives in ch1.
2. **One install story.** Install commands, their real output, and their failure modes exist in ch1 only. `/python/` gets a three-line teaser (below) and no output blocks.
3. **ch1 stays basic and links out.** Each topic gets the minimum to keep moving plus a link to the chapter that owns it: routing → ch2, request/response → ch3, templates → ch4, database → ch5, ORM → ch6, dev tools → ch30, CLI → ch31, env → ch33, deployment → ch34.
4. **Numbers carry a date and a source.** Anything quotable is either re-measured (`[RUN]`) or dated in place. No claim without a figure behind it.

## What moves

| Content | From | To | Why |
|---|---|---|---|
| 36-section cheatsheet (~610 ln) | `/python/` (nav landing) | deleted | Second copy of the book; nothing links into it; ch38 already answers "what is in the box" better |
| Ch1 §9 Request & Response fundamentals (~187 ln) | ch1 | Chapter 3 | Chapter 3 *is* request/response |
| Ch1 §10–11 exercise + solutions (~214 ln) | ch1 | Chapter 2 or 3 | They drill routing and params, not getting started |
| Ch1 §8 Manual Setup (no CLI) (~68 ln) | mid-chapter | ch1 appendix | An escape hatch, not a step |
| Duplicate unnumbered "Installing the Tina4 CLI" (~109 ln) | ch1 | deleted | Second install section, wrong method (`cargo install tina4`) |
| Why + numbers | — | new: full on `/python/`, 8-line summary in ch1 | Absent from the section today |

## Three calls that were open

**Install on `/python/`: three lines, no more.** Two install stories that disagree is
the current defect — the cheatsheet's 15-line version claims "your browser opens" while
`init` actually prompts `Start the server now? [Y/n]` `[RUN]`. So the landing page gets
one unexplained block (`tina4 init python my-app`) under an "in a hurry" aside, linking
ch1. No output, no claims, nothing to drift.

**The mock program lives in ch1.** `/python/` shows a route; ch1 has the reader build
one JSON endpoint and one templated page. It belongs where the reader already has a
running server.

**The why is mirrored into the book, deliberately.** `docs/python/index.md` is site-only
and `scripts/build_pdf.py` reads book chapters only, so a why-page on the site leaves the
downloadable Python book with no Python-specific argument. ch1 therefore opens with an
8-line condensed why — three numbers and a link to `/python/`. One measured number set,
quoted in two places, dated in both. This is the only sanctioned duplication in the plan.

## The cheatsheet: retire it

The three candidate homes were a page of its own, the landing, or Chapter 1. It gets
none of them. Five measured reasons `[REPO]` `[RUN]`:

1. **Every one of its 37 sections duplicates a chapter** (title-level map in the evaluation). Not one section documents something the book does not.
2. **"What is in the box" already has a better page.** Chapter 38: Complete Feature List — 190 lines, 97 features in tables, each row naming the dependency the built-in replaces ("instead of gunicorn/uvicorn config", "instead of body-parser"). It is already filed under `Reference`. That is the reference page a returning developer wants; a 610-line snippet wall is not.
3. **Nothing links into it.** All 36 `index.md#…` references in the Python book come from its own link row. Repo-wide, only two pages link to `/python/index.md` at all — the site landing and `js/17-realtime-rtc.md` — and both link the page, not an anchor, so both survive the retasking.
4. **It has already drifted wrong, unnoticed.** Its Services section reads "Due to the nature of Python, services are not necessary" while Chapter 27 documents `ServiceRunner` and the class ships in 3.13.94 `[RUN]`. It calls templates `.twig` where Chapter 1 uses `.html`. It claims `init` opens your browser when `init` prompts `Start the server now? [Y/n]`. 610 hand-maintained duplicate lines need re-verifying every release, and nobody is doing it.
5. **Both remaining homes recreate the problem being fixed.** On the landing it *is* the current defect — a newcomer's first page as a snippet wall, and the pitch page swells from 200 to ~800 lines. Inside Chapter 1 the chapter goes back past 1 100 lines and becomes a tutorial glued to a reference, which is exactly the shape the rewrite exists to undo.

What replaces it: the feature map on `/python/` (grouped, every entry linking the chapter
that owns it) for orientation, Chapter 38 for "does it ship", and the chapter itself for
"how do I call it". If a genuine snippet index is wanted later, generate it from the
chapters instead of hand-keeping a second copy.

Checked and **not** a defect: the cheatsheet imports `from tina4_python import Api` while
Chapter 21 uses `from tina4_python.api import Api`. Both work — the package re-exports it
`[RUN]`.

## Why this shape

The nav click on "Python" is the section's front door and today it lands on the one page
that teaches nothing. Making it the argument costs no renumbering and breaks no inbound
link — all 36 `index.md#…` references in the Python book come from that page's own link
row `[REPO]`. ch1 becomes what its title promises and ends with an exit it has never had.
Two pages replace two pages; the book loses 610 duplicated lines it was not maintaining.

## Alternatives that lost

- **Pitch page carries the install too** (the earlier draft). Rejected: recreates the two-install-stories defect we are fixing.
- **Fold everything into ch1, delete `/python/`.** One page, everything in the PDF. Rejected: the nav click then lands on a 700-line chapter, and the argument gets buried in a tutorial that a returning reader has to scroll past. Kept the good part of it — the 8-line why-summary in ch1.
- **Keep the cheatsheet as `/python/quick-reference/`** (the earlier draft). Rejected: see *The cheatsheet* above — ch38 does that job, and a hand-maintained duplicate had already gone wrong in at least three places.

## Risks

- **Published numbers are already stale.** `/comparisons/` says Tina4 Python installs at 2.4 MB; measured today it is **4.9 MB** (102 `.py` files, `tina4_python` 3.13.94) `[RUN]`. If Tina4's own figure drifted that far since March 2026, the competitor figures on that page need re-measuring before either page quotes them.
- **The sync runs book → docs.** `scripts/sync-books.sh` will overwrite `docs/python/01-getting-started.md`, which already carries a `TINA4_CORS_ORIGINS` row the book lacks. Upstream that row into the book before syncing.
- **Sidebar is generated by `tina4press` 0.1.9** (`sidebar: null, // auto, section-scoped`), which currently renders the section's `index.md` as an item labelled "Overview". Unverified: whether the retitled page picks up its own `#` heading or stays hard-labelled. Needs `npm i && npm run docs:build` before ship.
- **Retiring 610 lines loses whatever external traffic they had.** Nothing in either repo links to the cheatsheet's anchors, but search engines and the site's own "Ask Tina4" index may. The URL itself (`/python/`) survives, so there is nothing to redirect; deep links to `#orm`, `#queues` and friends will land on the new page top. Acceptable, but say it out loud rather than discover it later.
- **Six sections will copy this.** `nodejs/index.md` 936 lines, `php` 739, `ruby` 566, `js` 260, `delphi` 230 — all the same "Quick Reference" species `[REPO]`. The structure decision outlives the prose.
- **The mirrored why can drift.** Mitigation: ch1's version is three numbers and a link, never prose that has to be kept in step.
- **The CLI section can go stale like the version strings did.** `tina4 --help` on 3.8.64 does not list `migrate`, `test`, or `generate`, yet all three work as passthroughs to `tina4python` `[RUN]`. Anything ch1 documents there should be re-run at ship time.

## Open decisions

1. **LOC table** — build it (spec in Part 2) or ship the pitch on packages / size / features only?
2. **Throughput** — re-run `benchmark/benchmark.sh` on this machine, or cite the dated March 2026 run and link `/comparisons/`?
3. **ch1 §9–11** — relocate into chapters 2–3 in this pass, or cut from ch1 and log the move?
4. **Two CLI defects found while measuring** — `tina4 routes` in a fresh project prints the "Tina4 must be started with the tina4 CLI" guard instead of listing routes, and `tina4 test` fails with `No module named pytest` because the scaffold installs no test runner `[RUN]`. Document the workaround in ch1, or file them and leave both commands out of the chapter until fixed?

---

# Part 2 — Example refined structure

Headings in order, intent under each, real content where it is load-bearing.
`TODO(measure)` marks a number that must be measured before it is written.
Every figure below without that marker is measured — see the fact inventory at the end.

## `/python/` — "Why Tina4 for Python" (~200 lines)

```markdown
# Tina4 for Python Developers

One paragraph: a web framework that ships routing, ORM, templates, auth, queues,
WebSocket and Swagger in a single package with no third-party dependencies, for
Python 3.12+. Who it is for. No feature list yet.

## Why bother

Four rows, every one a number.

  | | Tina4 | FastAPI | Flask | Django |
  |---|---:|---:|---:|---:|
  | Third-party packages installed | 0 | 12 | 6 | 20 |
  | Install size on disk | 4.9 MB | 4.8 MB | 4.2 MB | 25 MB |
  | Of 44 compared capabilities | 44 | 10 | 7 | 24 |
  | Lines to build the app in Chapter 1 | TODO(measure) | TODO(measure) | TODO(measure) | TODO(measure) |

  Tina4 row measured 2026-08-06, tina4-python 3.13.94, Python 3.14.5.
  Other rows from /comparisons/ (March 2026) — re-measure before publishing.
  Throughput lives on /comparisons/; link it, do not restate it here.

### What zero dependencies buys you
No resolver conflicts, one package to upgrade, and the whole supply chain is one
name. `uv sync` on a fresh scaffold: `Resolved 2 packages`, `Installed 1 package`,
`+ tina4-python==3.13.94`. Link /general/01-what-is-tina4/ for the long argument.

### What it costs you
Starlette serves raw JSON faster (15 664 vs 9 761 req/s, March 2026). The ecosystem
is a fraction of Django's. The conventions are fixed — routes live in src/routes,
templates in src/templates, and the framework will not be talked out of it.
Say this here, and the rest of the page is trusted.

## How it works

Illustrations, not steps. Nothing here is meant to be run yet.

**Routes are files.** Drop a .py in src/routes/, decorate a handler, restart nothing:

    from tina4_python.core.router import get

    @get("/api/bookmarks/{tag}")
    async def bookmarks(tag, request, response):
        return response.json({"tag": tag, "items": []})

Path parameters arrive as arguments. Handlers are `async def`. The framework
discovers every file under src/routes/ at boot — no registry, no blueprint, no
app.include_router.

**Pages are templates.** src/templates/ holds Frond templates (Twig-compatible):

    {% extends "base.html" %}
    {% block content %}<h1>{{ title }}</h1>{% endblock %}

    return response.render("page.html", {"title": "Bookmarks"})

**Everything has a place.**

    src/routes/      handlers, auto-discovered
    src/orm/         models, auto-discovered
    src/templates/   Frond templates
    src/public/      static files, served at /
    migrations/      SQL migrations
    .env             configuration

## What's built in

Grouped feature map, each entry linking the chapter that owns it. Replaces the
cheatsheet's job on this page without copying chapter content.

  Web       routing (ch2) · request & response (ch3) · templates (ch4) · middleware (ch10)
  Data      database (ch5) · ORM (ch6) · query builder (ch7) · migrations (ch5)
  Auth      JWT (ch8) · sessions & cookies (ch9)
  APIs      Swagger (ch20) · API client (ch21) · GraphQL (ch22) · SOAP/WSDL (ch25)
  Realtime  WebSocket (ch23) · SSE (ch24) · WebRTC (ch39)
  Ops       queues (ch12) · caching (ch11) · logging (ch15) · deployment (ch34)

Checking whether something ships before you reach for a package? **Chapter 38:
Complete Feature List** — 97 features, each naming the dependency it replaces.

## Start here

→ **Chapter 1: Getting Started** — install from nothing, run it, build a working
  endpoint and page.
→ Weighing it against Flask, FastAPI or Django? **Comparisons** — full tables, method,
  and dates.
→ "Is it already in the box?" → **Chapter 38: Complete Feature List**.

> In a hurry, and the CLI is already installed?
>
>     tina4 init python my-app
>
> Chapter 1 covers what that does and what to do when it does not.
```

## `/python/01-getting-started/` — Chapter 1 (~480 lines)

```markdown
# Chapter 1: Getting Started with Tina4 Python

Two paragraphs: what you will have running by the end (an API endpoint and a
rendered page), and the conventions (snake_case methods, PascalCase classes,
`async def` handlers). Keep the cross-language note about path parameters.

Then the 8-line why, mirrored from /python/:

  Zero third-party packages. 4.9 MB installed. 44 of 44 compared capabilities,
  against Django's 24 and Flask's 7. Measured 2026-08-06 on tina4-python 3.13.94.
  Full argument and method: /python/ and /comparisons/.

## 1. Before you start

Assume nothing installed. Python 3.12+ (`python3 --version`), uv, and the CLI
per OS — Homebrew, install script, PowerShell. Real version output only; the
current chapter's `tina4 0.1.0` is three majors behind 3.8.64.

Verify: `tina4 --version` → `tina4 3.8.64`. And `tina4 doctor` to see what the CLI
found — languages, versions, package managers.

Delete the duplicate unnumbered "Installing the Tina4 CLI" section and the false
claim that `tina4 init` installs the CLI.

## 2. Create the project

    tina4 init python my-app

Real output [RUN], trimmed to what the reader sees:

    ▶ Checking python runtime...
      ✓ python3 found
    ▶ Checking package manager...
      ✓ uv found
    ▶ Scaffolding python project...
      ✓ Created directory structure
      ✓ Created .env
      ✓ Created app.py
      ✓ Created .gitignore
      ✓ Created pyproject.toml
    ▶ Installing dependencies...
      Resolved 2 packages in 634ms
      Installed 1 package in 15ms
       + tina4-python==3.13.94
      Start the server now? [Y/n]

Note it installs dependencies for you, then offers to start. No separate `uv sync`
step, no "next steps" list.

What exists now: five files (`app.py`, `.env`, `.gitignore`, `pyproject.toml`,
`uv.lock`) and ten directories (`data/`, `logs/`, `migrations/`,
`src/{routes,orm,templates,scss,public/{css,images,js}}`). All directories are
empty. `app.py` is three lines — show all three.

The rest of the layout (`src/seeds/`, `src/templates/errors/`, `src/public/icons/`,
`src/locales/`, `secrets/`, `tests/`, `data/.broken/`) appears the first time you
run the server — the framework creates what is missing on boot [SRC]. Say that
plainly instead of listing directories `init` never made.

## 3. Run it

    tina4 serve

Real banner [RUN]:

      Tina4 Python v3.13.94 — The Intelligent Native Application 4ramework

      Server:    http://localhost:7146 (asyncio)
      Swagger:   http://localhost:7146/swagger
      Dashboard: http://localhost:7146/__dev
      Debug:     ON (Log level: ALL)
      Test Port: http://localhost:8146 (stable — no hot-reload)

It opens your browser for you. What is already live before you write a line:

  /            welcome page
  /health      {"status":"ok","uptime_seconds":433,"version":"3.13.94",
                "framework":"tina4py","errors":0}
  /swagger     API docs, generated from your routes
  /__dev       dev dashboard: routes, requests, SQL runner, queues, mailbox (ch30)
  /js/frond.js and /css/tina4.css — served by the framework, not files in your project
  live reload  the file watcher hot-reloads src/ and migrations/ in process

`Ctrl+C` stops it. `tina4 serve --port 8080` moves it. `--no-browser` and
`--no-reload` exist for CI and demos.

## 4. The CLI, in one page

Real flags [RUN]: `serve` takes `--port`, `--host`, `--dev`, `--production`,
`--no-browser`, `--no-reload`, and an optional project name.

  tina4 doctor        what languages and package managers you have
  tina4 init          scaffold a project
  tina4 serve         dev server, watcher, SCSS compile
  tina4 serve --production   detect and use a production ASGI server
  tina4 migrate       run migrations (prints "Nothing to migrate." on a fresh project)
  tina4 generate      model, route, crud, migration, middleware, test, form, view,
                      auth, service, queue, validator, seeder, websocket, listener
  tina4 scss          compile src/scss/ → src/public/css/
  tina4 env           edit environment variables interactively
  tina4 deploy        Dockerfile, systemd unit, nginx block, or cPanel .htaccess
  tina4 books         download this book into your project
  tina4 update        self-update the CLI

Full reference: ch31. Two caveats to settle before publishing — `tina4 routes` in a
fresh project prints the "must be started with the tina4 CLI" guard instead of
listing routes, and `tina4 test` fails with `No module named pytest` until a test
runner is installed [RUN]. See open decision 4.

## 5. Build the smallest real thing

One file, two routes. Create `src/routes/bookmarks.py`:

    GET  /api/bookmarks   -> JSON list
    POST /api/bookmarks   -> append, 201; 400 when "url" is missing

Then one page that renders the same data through a template that extends a base
layout: `src/templates/base.html`, `src/templates/bookmarks.html`, and a
`GET /bookmarks` handler calling `response.render(...)`.

In-memory list, no database — ch5 and ch6 own persistence. Keep the inline CSS to a
few lines; ch17 owns styling.

Then "what just happened", five steps, in the style the current chapter already uses
for its greeting route — it is the best-explained part of the existing page.

Depth from here: routing patterns and typed params → ch2. request.params,
request.body, headers, status codes → ch3. Template inheritance, filters, loops → ch4.

## 6. Configuration

The scaffolded `.env` is two lines: `TINA4_DEBUG=true` and `TINA4_LOG_LEVEL=ALL`.
Port resolution order (CLI flag → .env → PORT → framework default 7146), the four
log levels, and the note that `serve` writes `.env.local` with a generated dev auth
secret [RUN]. All 68 variables: ch33.

## 7. When it does not work

The seven existing gotchas — file not in src/routes/, missing import, handler not
`async def`, template not found, port in use, changes not reflected, .env in the
wrong place. They are good, and they are no longer the last thing on the page.

## Appendix: without the CLI

Current §8, moved here: `pip install tina4-python`, a three-line `app.py`, the
folder skeleton, and the `TINA4_OVERRIDE_CLIENT=true` note.

## Summary

Four bullets: what you installed, what is running, what you built, what the
framework gave you for free. Then the exit the chapter has never had:

→ **Chapter 2: Routing** — path patterns, typed parameters, route groups.
→ **Chapter 5: Database** — give the bookmarks somewhere to live.
→ **Chapter 38: Complete Feature List** — what else ships, and what it replaces.
```

## Retiring `docs/python/index.md`'s cheatsheet

Delete the 37 sections and the self-referential 36-link row; the file becomes the
landing page above. Nothing else in either repo needs editing — the two inbound links
(`docs/index.md:133`, `docs/js/17-realtime-rtc.md:464`) point at the page, not an
anchor, and `tina4press.config.mjs:78` already points nav "Python" here.

Before deleting, one harvest pass: read each section and confirm its chapter really
covers it. Two known misfits to settle rather than silently drop — the Services
section's "services are not necessary" contradicts ch27, and its `.twig` template
extension contradicts ch1. Both are wrong on the cheatsheet, so the fix is to correct
the chapters if they are also wrong, not to preserve the cheatsheet's version.

## LOC measurement spec — `TODO(measure)`

The LOC row is only worth printing if it is reproducible. Measure the app the reader
builds in ch1 §5, identically in each framework:

1. `GET /api/bookmarks` → JSON list of three hardcoded bookmarks.
2. `POST /api/bookmarks` → append, 201; 400 when `url` is missing.
3. `GET /bookmarks` → the same list rendered through a template that extends a base layout.

Rules: framework defaults only, no extra abstraction, imports counted, blank lines and
comments not counted, versions pinned and recorded. Each app must actually serve all
three routes before its lines are counted — a count of code that never ran is not
evidence. Report lines, files, and third-party packages installed per framework, with
the date and Python version. Candidates: Tina4, Flask, FastAPI, Django (Starlette and
Bottle optional).

## Fact inventory — measured 2026-08-06, ready to use

| Fact | Value | Tag |
|---|---|---|
| CLI version | `tina4 3.8.64` (3.8.67 available) | `[RUN]` |
| Framework version | `tina4-python==3.13.94` | `[RUN]` |
| Python used | CPython 3.14.5; `pyproject.toml` floor `>=3.12` | `[RUN]` |
| Third-party packages | 0 — site-packages holds `tina4_python`, its dist-info, and virtualenv shims only | `[RUN]` |
| Install size | 4.9 MB, 102 `.py` files | `[RUN]` |
| Post-`init` contents | 5 files, 10 empty directories | `[RUN]` |
| Folders `serve` adds on boot | 16, via `_ensure_folders()` | `[SRC]` `[RUN]` |
| `.env` as scaffolded | `TINA4_DEBUG=true`, `TINA4_LOG_LEVEL=ALL` | `[RUN]` |
| `app.py` | 3 lines | `[RUN]` |
| `/health` body | `{"status":"ok","uptime_seconds":433,"version":"3.13.94","framework":"tina4py","errors":0}` | `[RUN]` |
| Dev server | built-in asyncio; uvicorn/hypercorn/granian optional, for `--production` | `[SRC]` |
| Extras on boot | agent server :9146, 7 agents in `.tina4/agents/`, test port :8146, `.env.local` secret, browser opens | `[RUN]` |
| `tina4 generate` targets | 15 generators | `[RUN]` |
| Competitor deps / size / features | FastAPI 12 / 4.8 MB / 10 · Flask 6 / 4.2 MB / 7 · Django 20 / 25 MB / 24 | `[REPO]`, March 2026 — re-measure |
| Throughput (JSON / list req/s) | Tina4 9 761 / 5 769 · Starlette 15 664 / 9 302 · FastAPI 11 523 / 2 709 · Flask 5 722 / 962 · Django 2 333 / 2 150 | `[REPO]`, March 2026 |
