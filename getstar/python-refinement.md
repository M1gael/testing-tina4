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
| `/python/` — "Why Tina4 instead of Flask" | The argument and the mental model, for a reader already committed to Python. No setup steps. | `tina4-documentation/docs/python/index.md` | ~200 lines |
| `/python/01-getting-started/` | The mechanics, assuming nothing: install, run, CLI, First App. | `tina4-book/book-1-python/chapters/01-getting-started.md` | ~480 lines |
| `/python/quick-reference/` | Per-chapter finder for a reader who knows what they want. **Kept**, moved off the landing page. | `tina4-documentation/docs/python/quick-reference.md` | ~610 lines |

Three pages. The 621-line quick reference currently occupying `/python/` is **kept and
moved, not retired** — see *The quick reference* below.

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
| 36-section quick reference (~610 ln) | `/python/` (nav landing) | its own page — placement TBD | Keeps the finder, frees the landing page to argue. Three wrong entries fixed in the move |
| Ch1 §9 Request & Response fundamentals (~187 ln) | ch1 | Chapter 3 | Chapter 3 *is* request/response |
| Ch1 §10–11 exercise + solutions (~214 ln) | ch1 | Chapter 2 or 3 | They drill routing and params, not getting started |
| Ch1 §8 Manual Setup (no CLI) (~68 ln) | mid-chapter | ch1 appendix | An escape hatch, not a step |
| Duplicate unnumbered "Installing the Tina4 CLI" (~109 ln) | ch1 | deleted | Second install section, wrong method (`cargo install tina4`) |
| Why + numbers | — | new: full on `/python/`, 8-line summary in ch1 | Absent from the section today |

## Three calls that were open

**Install on `/python/`: three lines, no more.** Two install stories that disagree is
the current defect — the quick reference's 15-line version claims "your browser opens" while
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

## The quick reference: keep it, move it

**Decided 2026-08-07 (Andre):** the quick reference is *not* removed — "it serves as a
quick finder". Nothing else on the site does per-chapter lookup, so the finder job is real.

What changes is only *where it sits* and *whether it is right*. It stops being the first
screen a newcomer sees, and its wrong entries get fixed.

**Placement — settled 2026-08-07 (user): its own page, sitting under Overview.**
`docs/python/quick-reference.md`, in the docs repo. Non-numbered, so `sync-books.sh`
preserves it and it never reaches the PDF. Sidebar mechanics in *Moving the quick
reference* below — it needs a `BACKEND_GROUPS` entry or it is silently filed under "More".

The five measured observations below stood behind the earlier retire-it proposal. The
conclusion is withdrawn; the observations still hold, and they are the reasons it cannot
stay on the landing page unchanged `[REPO]` `[RUN]`:

1. **Every one of its 37 sections duplicates a chapter** (title-level map in the evaluation). Not one section documents something the book does not.
2. **"What is in the box" already has a better page.** Chapter 38: Complete Feature List — 190 lines, 97 features in tables, each row naming the dependency the built-in replaces ("instead of gunicorn/uvicorn config", "instead of body-parser"). It is already filed under `Reference`. That is the reference page a returning developer wants; a 610-line snippet wall is not.
3. **Nothing links into it.** All 36 `index.md#…` references in the Python book come from its own link row. Repo-wide, only two pages link to `/python/index.md` at all — the site landing and `js/17-realtime-rtc.md` — and both link the page, not an anchor, so both survive the retasking.
4. **It has already drifted wrong, unnoticed.** Its Services section reads "Due to the nature of Python, services are not necessary" while Chapter 27 documents `ServiceRunner` and the class ships in 3.13.94 `[RUN]`. It calls templates `.twig` where Chapter 1 uses `.html`. It claims `init` opens your browser when `init` prompts `Start the server now? [Y/n]`. 610 hand-maintained duplicate lines need re-verifying every release, and nobody is doing it.
5. **Two placements are ruled out by measurement.** Left on the landing page it *is* the current defect — a newcomer's first screen is a snippet wall, and the page swells from 200 to ~800 lines. Inlined into Chapter 1 the chapter goes back past 1 100 lines and becomes a tutorial glued to a reference, the shape the rewrite exists to undo. So: a page of its own, or a clearly separate page adjacent to Getting Started.

Alongside it, unchanged by this decision: the landing page still carries a short grouped
feature map (each entry linking the chapter that owns it) for orientation, and Chapter 38
stays the answer to "does it ship". Those serve different questions than the finder does.

Worth doing later, not now: generate the quick reference from the chapters instead of
hand-keeping a second copy. Reason 4 is what hand-maintenance costs.

Checked and **not** a defect: the quick reference imports `from tina4_python import Api` while
Chapter 21 uses `from tina4_python.api import Api`. Both work — the package re-exports it
`[RUN]`.

## Why this shape

The nav click on "Python" is the section's front door and today it lands on the one page
that teaches nothing. Making it the argument costs no renumbering and breaks no inbound
link — all 36 `index.md#…` references in the Python book come from that page's own link
row `[REPO]`, and they travel with the quick reference when it moves. ch1 becomes what its
title promises and ends with an exit it has never had. Three jobs, three pages, instead of
one page doing all three badly.

## Alternatives that lost

- **Pitch page carries the install too** (the earlier draft). Rejected: recreates the two-install-stories defect we are fixing.
- **Fold everything into ch1, delete `/python/`.** One page, everything in the PDF. Rejected: the nav click then lands on a 700-line chapter, and the argument gets buried in a tutorial that a returning reader has to scroll past. Kept the good part of it — the 8-line why-summary in ch1.
- **Retire the quick reference entirely.** Rejected by Andre on 2026-08-07: it is a finder, and ch38 answers "does it ship", not "how do I write it". `/python/quick-reference/` — the earlier draft's own rejected idea — is now the leading placement.

## Risks

- **Published numbers are already stale.** `/comparisons/` says Tina4 Python installs at 2.4 MB; measured today it is **4.9 MB** (102 `.py` files, `tina4_python` 3.13.94) `[RUN]`. If Tina4's own figure drifted that far since March 2026, the competitor figures on that page need re-measuring before either page quotes them.
- **The sync runs book → docs.** `scripts/sync-books.sh` will overwrite `docs/python/01-getting-started.md`, which already carries a `TINA4_CORS_ORIGINS` row the book lacks. Upstream that row into the book before syncing.
- **Sidebar is generated by `tina4press`** (`package.json` pins `^0.1.14`; `sidebar: null, // auto, section-scoped`). Resolved 2026-08-07 by reading `src/sidebar.js`: the section's `index.md` is hard-labelled "Overview" and does **not** pick up its own `#` heading, and a stem-less page is filed under a collapsed "More". Both handled in *Moving the quick reference*. Still worth a `pnpm i && pnpm docs:build` before ship to see the rendered result.
- **Moving 610 lines moves their anchors.** Nothing in either repo links to `/python/#orm`, `/python/#queues` and friends, but search engines and the site's own "Ask Tina4" index may. Those deep links will land on the new landing page top, not on the section they name. The anchors themselves survive at the quick reference's new URL. Either accept it or add redirects once placement is settled — decide it, do not discover it.
- **Six sections will copy this.** `nodejs/index.md` 936 lines, `php` 739, `ruby` 566, `js` 260, `delphi` 230 — all the same "Quick Reference" species `[REPO]`. The structure decision outlives the prose.
- **The mirrored why can drift.** Mitigation: ch1's version is three numbers and a link, never prose that has to be kept in step.
- **The CLI section can go stale like the version strings did.** `tina4 --help` on 3.8.64 does not list `migrate`, `test`, or `generate`, yet all three work as passthroughs to `tina4python` `[RUN]`. Anything ch1 documents there should be re-run at ship time.

## Decisions — settled 2026-08-07

1. **Comparison table: build it, feature-matched.** Spec rewritten in Part 2. The first attempt (three routes, no database, no auth, no Swagger) is discarded — it measured the one case where the comparatives need no extra packages. No figure publishes until all four apps run with DB + JWT + Swagger.
2. **Throughput: no re-run.** `hey` is not installed here and this machine is not the Apple Silicon box the March 2026 numbers came from. Cite that run with its date, link `/comparisons/`, and keep one honest cost line. Whether any figure appears at all is settled while writing the page.
3. **ch1 §9–11: cut, relocate nothing.** Measured 2026-08-07 — the destinations already own the material. ch3 (1 000 ln) covers all seven of §9's subsections (`request.params`, `request.body`, `request.headers`, path parameters, `response.json()`, `response.render()`, §4 Status Codes); ch2 (1 011 ln) already has an exercise plus solution at §12–13, as does ch3 at §9–10. So ch1 §9 (187 ln) and §10–11 (214 ln) are a third copy. Nothing is lost by cutting, and no PR to ch2/ch3 is needed.
4. **Quick reference: kept** (Andre), as **its own page under Overview** (user) — `docs/python/quick-reference.md`. Which sidebar slot it gets is the one thing still open. See *The quick reference* and *Moving the quick reference*.
5. **Landing page framing** (Andre): "why Tina4 instead of Flask, as a Python engineer", not "why Python".
6. **ch1's app section is named "First App"** (Andre).

Still open, to resolve while writing rather than up front:

- **Two CLI defects found while measuring** — `tina4 routes` in a fresh project prints the "Tina4 must be started with the tina4 CLI" guard instead of listing routes, and `tina4 test` fails with `No module named pytest` because the scaffold installs no test runner `[RUN]`. Document the workaround in ch1, or leave both commands out until fixed upstream.

---

# Part 2 — Example refined structure

Headings in order, intent under each, real content where it is load-bearing.
`TODO(measure)` marks a number that must be measured before it is written.
Every figure below without that marker is measured — see the fact inventory at the end.

## `/python/` — "Why Tina4 instead of Flask" (~200 lines)

Framing fixed 2026-08-07 (Andre): this is not "why pick Python". The reader already
writes Python. The page answers *why I would use Tina4 instead of Flask, as a Python
engineer* — a framework choice, addressed to someone with an incumbent.

```markdown
# Tina4 for Python Engineers

One paragraph, aimed at someone who already has a Flask, FastAPI or Django habit:
routing, ORM, templates, auth, queues, WebSocket and Swagger in a single package with
no third-party dependencies, for Python 3.12+. What it replaces, not what it is.
No feature list yet.

## Why not just use Flask?

Every row a number, and every row feature-matched — the same app, with a database,
a JWT-protected write, and Swagger docs. See the comparison spec; whatever the
comparatives need to reach parity is counted against them, and named.

  | | Tina4 | FastAPI | Flask | Django |
  |---|---:|---:|---:|---:|
  | Third-party distributions installed | TODO(measure) | TODO(measure) | TODO(measure) | TODO(measure) |
  | Packages you add for DB + JWT + Swagger | TODO(measure) | TODO(measure) | TODO(measure) | TODO(measure) |
  | Install size on disk | TODO(measure) | TODO(measure) | TODO(measure) | TODO(measure) |
  | Lines to build the Chapter 1 app | TODO(measure) | TODO(measure) | TODO(measure) | TODO(measure) |

  Name the added packages inline, per framework — the list is the argument.
  Every figure carries its date, Python version and framework versions.
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

Grouped feature map, each entry linking the chapter that owns it. Orientation only —
no snippets. The Quick Reference (own page) is the finder; this is the map.

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
→ Know what you want, need the syntax? **Quick Reference** — every subsystem, one
  snippet each, linking the chapter.
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

## 5. First App

Section name set 2026-08-07 (Andre): "First App".

One file, two routes. Create `src/routes/bookmarks.py`:

    GET  /api/bookmarks   -> JSON list
    POST /api/bookmarks   -> append, 201; 400 when "url" is missing

Then one page that renders the same data through a template that extends a base
layout: `src/templates/base.html`, `src/templates/bookmarks.html`, and a
`GET /bookmarks` handler calling `response.render(...)`.

**The POST needs `@noauth()`, and the chapter has to say why.** Verified 2026-08-07:
without it the handler returns 401 `{"error":"Unauthorized","message":"Valid
authorization token required","status":401}` — Tina4 secures non-GET routes by
default. Teach it as the feature it is (writes are closed until you open them),
name `@noauth()` and `@secured()`, and point at ch8. Getting this wrong is how a
reader's first POST fails with no explanation on the page.

In-memory list, no database — ch5 and ch6 own persistence. Keep the inline CSS to a
few lines; ch17 owns styling.

Note for the writer: this is the same app as the comparison spec, minus the database,
JWT and Swagger requirements. The comparison build is a separate exercise — do not
grow ch1 to match it.

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

## Moving the quick reference out of `docs/python/index.md`

Cut the 37 sections and the self-referential 36-link row out of `index.md` and paste
them into their new home; `index.md` becomes the landing page above. The two inbound
links (`docs/index.md:133`, `docs/js/17-realtime-rtc.md:464`) point at the page, not an
anchor, so both keep working, and `tina4press.config.mjs:78` already points nav "Python"
at `index.md`.

Destination: `tina4-documentation/docs/python/quick-reference.md`. Non-numbered, so
`sync-books.sh` (`rm -f docs/<lang>/[0-9]*.md`) leaves it alone, and `build_pdf.py`
(globs `chapters/NN-*.md`) never sees it. Site-only, by design.

**Sidebar — read `tina4press@0.1.14/src/sidebar.js` before touching this.** Ground truth
from `autoSectionSidebar()` `[SRC]`:

- Grouping is by **stem**, per section; `docs/python/` uses the shared `BACKEND_GROUPS`.
- A page whose stem matches no group is **not dropped** — `orphans` collects it into a group literally titled **"More"**, `collapsed: true`, at the bottom. Without a `BACKEND_GROUPS` entry the finder is a finder nobody finds.
- `collapsed: i !== 0` — only the **first** group renders open. Inserting `{ text: "Quick Reference", stems: ["quick-reference"] }` at index 0 puts it directly under Overview and open, but collapses Foundations, which hides Getting Started. That trade is the one real cost of "under Overview".
- `orderKey()` returns 9999 for non-numbered files, so it sorts last inside whatever group holds it. Frontmatter `order: <n>` overrides that.
- `BACKEND_GROUPS` is shared by python / php / ruby / nodejs, so one stem entry serves all four when their turn comes. A language without the file simply shows nothing.

Placement options inside the sidebar, in preference order:

1. **New first group** — literal "under Overview", open. Cost: Foundations collapses.
2. **Add `quick-reference` to the existing `Reference` group** (beside `feature-list`, `upgrading-from-v2`) — semantically right, but bottom of the sidebar and collapsed.
3. **Fix it properly in `tina4press`** — let the `${label} Reference` group carry configured siblings, and stop hard-coding the item label. See the note below; this is a fourth repo, so treat it as a follow-up, not a blocker.

**Separate finding, same file:** the landing page's sidebar label is hard-coded —
`items: [{ text: "Overview", link: indexPage.url }]` `[SRC]`. `titleFromPage()` is not
called for it, so retitling `index.md` to "Tina4 for Python Engineers" changes the page
heading and nothing in the sidebar. Either accept the nav still saying "Overview", or land
a small `tina4press` change. Decide before the PR, so the mismatch is a choice.

Three fixes to make during the move, not after — all three are wrong today `[REPO]` `[RUN]`:

1. Services: "Due to the nature of Python, services are not necessary" — ch27 documents `ServiceRunner` and the class ships in 3.13.94.
2. Templates called `.twig`; ch1 uses `.html`.
3. `tina4 init` described as opening your browser; it prompts `Start the server now? [Y/n]`.

Where a chapter is also wrong, fix the chapter — do not preserve the quick reference's
version as the tie-breaker.

## Comparison measurement spec — `TODO(measure)`

**Revised 2026-08-07 (Andre): the comparison must be feature-matched.** "Functionality
tested on comparatives needs to add packages to achieve what Tina4 has under the hood…
if you need Swagger + auth + database = dependencies. Compare apples with apples."

This invalidates the first attempt. A three-route app with no Swagger, no auth and no
database is the one shape where Flask and FastAPI need nothing extra, so it measures
nothing about what Tina4 replaces. No figure from it gets published, and the
"fewer lines of code" claim is withdrawn until a matched build says otherwise.

The app to build, identically in each framework:

1. `GET /api/bookmarks` — JSON list, read from a **database** table.
2. `POST /api/bookmarks` — insert, 201; 400 when `url` is missing; **requires a valid JWT**.
3. `GET /bookmarks` — the same rows rendered through a template that extends a base layout.
4. **OpenAPI/Swagger docs** for both API routes, browsable.
5. A **migration or schema step** that creates the table.

Rules: framework defaults only, no extra abstraction, imports counted, blank lines and
comments not counted, versions pinned and recorded. Every app must actually serve all
three routes, authenticate a real token, and render its own Swagger page before its lines
are counted — a count of code that never ran is not evidence. Report, per framework:
lines authored, files touched, framework-wiring lines, third-party distributions
installed, and install size — with the date and Python version.

Frameworks: Tina4, Flask, FastAPI, Django. Tina4 needs no added packages for any of the
five requirements; the others each need several, and naming them *is* the argument.

Note on the existing published figures: a spot-check on 2026-08-07 disagreed with the
dependency counts and install sizes on `/comparisons/`. Treat that whole table as
unverified until re-measured under this spec.

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
| Non-GET routes require auth by default | POST without `@noauth()` returns 401 `{"error":"Unauthorized",…}` | `[RUN]` 2026-08-07 |
| OpenAPI spec, generated, no extra code | `/swagger/openapi.json` — OpenAPI 3.0.3, lists every declared route (`/swagger.json` and `/openapi.json` both 404) | `[RUN]` 2026-08-07 |
| Competitor deps / size / features | FastAPI 12 / 4.8 MB / 10 · Flask 6 / 4.2 MB / 7 · Django 20 / 25 MB / 24 | `[REPO]`, March 2026 — **do not republish**; a 2026-08-07 spot-check disagreed. Re-measure under the comparison spec |
| Throughput (JSON / list req/s) | Tina4 9 761 / 5 769 · Starlette 15 664 / 9 302 · FastAPI 11 523 / 2 709 · Flask 5 722 / 962 · Django 2 333 / 2 150 | `[REPO]`, March 2026 |
