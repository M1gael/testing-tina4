# Python — evaluation of the current entry pages

> **Status: still current, and the reason this directory earned its keep.** The audit below
> holds — section 2a is the evidence table for the 15-of-36 wrong sections and is cited from
> [`outstanding-tasks.md`](../outstanding-tasks.md). The *proposal* it fed
> ([`python-refinement.md`](python-refinement.md)) was rejected; the *findings* shipped, as
> corrections to upstream's own page structure. Re-verified against tina4-python 3.13.98 before
> shipping, which dropped two of the fixes as wrong (`@cached` decorator order, the memcached
> client package). Read [`state.md`](state.md) for what landed.

What exists on `tina4.com/python/` today. Audit only; the proposal lives in
`python-refinement.md`.

Assessed **2026-08-06**. Evidence tags per `README.md`: `[LIVE]` HTTP-checked on
tina4.com, `[REPO]` read from `origin/main`, `[RUN]` measured on this machine,
`[SRC]` read from installed `tina4_python` 3.13.94.

Both local clones sit on a stale local branch `docs/getting-started`
(`tina4-documentation` 19 commits behind `origin/main`, `tina4-book` 6 behind), but
`docs/python/index.md`, `docs/python/01-getting-started.md` and
`book-1-python/chapters/01-getting-started.md` are byte-identical on HEAD and
`origin/main`, so quotes below are current `[REPO]`.

## 1. The funnel

```
nav "Python" ──> /python/                     sidebar label: "Overview"
                 "Tina4 Python - Quick Reference"     621 lines
                 screen 1: 🔥 Hot Tips box
                 screen 1: a row of 36 anchor links to itself
                 screen 1: ### Installation + curl | sh + init + serve
                 line 26:  "More details" ──────────┐
                                                    │
sidebar "Foundations" ──> /python/01-getting-started/│  1136 lines
                          12 sections <─────────────┘
                          ends: "Fix: Move .env to the project root."
```

1 757 lines before the reader reaches Chapter 2 (itself 1 011 lines). No summary on
either page, no "what next", no prev/next footer `[LIVE]`.

Sidebar for the section: **Overview**, then Foundations (ch 1–10), Building Apps
(11–19), APIs & Protocols (20–25, 39), Advanced (26–29), Developer Tools (30–32),
Operations (33–35), Releases (36), Reference (37–38) `[LIVE]`.

## 2. Page 1 — Overview (`/python/`), 621 lines

37 sections, **average 16 lines each**. Heaviest: Sessions 53, GraphQL 40,
Middleware 32, Environments 31. Lightest: Services, Health Endpoint, Error Overlay,
Dev Admin, MCP Server — 4 lines each `[REPO]`.

What it is: a snippet wall for someone who already knows Tina4. What it is
positioned as: the landing page for anyone clicking "Python" in the top nav.

Three measured facts:

1. **Every section duplicates a chapter.** Title-level map — 36 feature sections, 36 chapters already covering them:

  | Overview section | Chapter | Overview section | Chapter |
  |---|---|---|---|
  | Installation | 1 Getting Started | Consuming REST APIs | 21 API Client |
  | Static Websites | 4 Templates | Inline Testing | 18 Testing |
  | Basic Routing | 2 Routing | Services | 27 Service Runner |
  | Middleware | 10 Middleware & Security | Websockets | 23 WebSocket |
  | Template Rendering | 4 Templates | Queues | 12 Queues |
  | Sessions | 9 Sessions & Cookies | WSDL | 25 WSDL / SOAP |
  | SCSS Stylesheets | 17 Frontend | GraphQL | 22 GraphQL |
  | Environments | 33 Environment Variables | Localization | 14 Localization |
  | Authentication | 8 Authentication | HTML Builder | 4 / 17 |
  | Forms and Tokens | 8 / 10 | Events | 13 Events |
  | AJAX and frond.js | 17 Frontend | Logging | 15 Structured Logging |
  | OpenAPI / Swagger | 20 Swagger | Response Cache | 11 Caching |
  | Databases | 5 Database | Health Endpoint | 30 Dev Tools |
  | Database Results | 5 Database | DI Container | 26 DI Container |
  | Migrations | 5 / 19 Scaffolding | Error Overlay / Dev Admin | 30 Dev Tools |
  | ORM | 6 ORM | CLI Commands | 31 CLI |
  | CRUD | 6 / 19 | MCP Server | 28 MCP Dev Tools |
  | FakeData | 19 Scaffolding | | |

  Nothing on the page is unique content. It is a compressed second copy of the book.

2. **Nothing links into it.** All 36 `index.md#…` references in the Python book come from one file — the Overview's own link row. Zero chapters link to it. Repo-wide, only two pages link to `/python/index.md` at all — `docs/index.md:133` and `docs/js/17-realtime-rtc.md:464` — and both target the page, not an anchor `[REPO]`. Retiring or retasking it breaks no inbound link.

3. **It teaches install a second way, wrongly.** "The CLI scaffolds your project, installs the dependencies, and starts the server … Your browser opens" — `init` installs deps then *asks* `Start the server now? [Y/n]` `[RUN]`. It also says templates are `.twig` files while Chapter 1 uses `.html` throughout `[REPO]`.

4. **It contradicts a shipped feature.** Its 4-line Services section reads "Due to the nature of Python, services are not necessary", while Chapter 27 documents `ServiceRunner` and `from tina4_python.service import ServiceRunner` imports cleanly on 3.13.94 `[RUN]`.

Checked and **not** a defect: the Overview imports `from tina4_python import Api` where
Chapter 21 uses `from tina4_python.api import Api`. Both work — the package re-exports it `[RUN]`.

No "why Tina4 instead of Flask / FastAPI / Django" anywhere on the page. No number of any kind.

### 2a. Snippet audit — 15 of 36 sections were factually wrong

Every section was **executed** against tina4-python 3.13.95 / CLI 3.8.67 / CPython 3.14.5
on 2026-08-07, not read `[RUN]`. Nine of these would have failed outright for a reader who
copied them. This is the strongest single argument the page needed correcting rather than
relocating unchanged.

| Section | Published | What actually happens |
|---|---|---|
| Websockets | `from tina4_python import websocket` | That name is the implementation **module**, not the decorator. `'module' object is not callable`, and the whole route file fails to load. Correct: `from tina4_python.core.router import websocket` |
| GraphQL | `GraphQL(schema, resolvers)` | `TypeError: GraphQL.__init__() takes 1 positional argument but 3 were given`. Real API: `GraphQL()`, then `schema.add_type()` / `schema.add_query()`; resolver signature `(root, args, ctx)`, not `(info, name)` |
| Services | `runner.register("heartbeat", HeartbeatService(interval=30))` | **Silent no-op** — `run()` called 0 times, nothing logged. `register()` wants a callable; class-based services use `register_service()` |
| Middleware | `response.content += "Before"` | `TypeError: can't concat str to bytes` → HTTP 500. Also the claimed output is fiction: only `before_`/`after_` prefixes are discovered, and a `before_` hook's writes are overwritten by the handler's response |
| Inline Testing | `from tina4_python import tests` + bare `assert_equal` | `NameError: name 'assert_equal' is not defined`. All three names live in `tina4_python.Testing` |
| CRUD | `users.to_crud(request)` + `{{ crud }}` | `to_crud` exists nowhere in the package. Real mechanism: `auto_crud = True` on the model (logs `AutoCrud: registered 5 routes for User (/api/user)`), or `tina4 generate crud` |
| Static Websites | `.html` in `src/templates` served with no configuration | 404. Templates require a route, or `@template(...)` placed *below* the route decorator. `src/public/` is the directory that is served |
| WSDL | "Drop the file in `src/routes/` and the framework serves the SOAP endpoint" | 404 — not auto-mounted. Needs `Calculator(request).handle()` returned from a handler; then `GET` yields the WSDL and SOAP `Add(2,3)` yields `<Result>5</Result>` |
| Response Cache | `@cached(max_age=120)` caches the response | Does not cache. Same route returned different bodies one second apart, with and without `TINA4_CACHE_BACKEND=memory`. The decorator only stamps `_cache_max_age`; `ResponseCache` reads it but is not in the dev server's request path |
| MCP | `/__mcp`, "24 dev tools" | Mounted at `/__dev/mcp` (JSON-RPC over POST; GET returns 405). `tools/list` returns **49** tools |
| Forms | `{{ ("Register" ~ RANDOM()) \| form_token }}` | `RANDOM()` is not a Frond function; it renders empty, so the expression reduces to `"Register"`. `form_token` works as both filter and function |
| Sessions | 5 backends listed | `memcached` missing; the aliases `filesystem`, `mongo`, `memcache`, `db` are accepted and undocumented |
| Migrations | `migrations/00001_create_users_table.sql` | `tina4 migrate:create` emits a timestamped name: `20260807151239_create_users_table.sql` |
| ORM | `User({"name": "Alice"}).save()` | `no such table: user` — the ORM does not create the table; a migration has to run first |
| Dev Admin | six named tabs | `/__dev` is a JS shell (`<div id="app">` + `tina4-dev-admin.min.js`); only routes, database and metrics are confirmable, so the rest cannot be asserted |

Verified correct and unchanged: every route decorator, `response()` callable forms and
`redirect()`, the five `dotenv` helpers, the `Auth.get_token`/`valid_token` round-trip,
`Database` + `fetch`, all four result converters, `I18n`, `HTMLElement`, events,
`Log` keyword arguments, `Container`, `FakeData`, `Api`, `tina4 scss`, `/health`, and
`@description` for Swagger.

Undocumented discovery rule found while testing: **a file in `src/routes/` whose name starts
with `_` is skipped silently** — no warning, the route simply 404s `[RUN]`.

## 3. Page 2 — Chapter 1, 1136 lines

Order today: what it is → prerequisites/install → project structure → first route →
first template → `.env` → dev dashboard → manual setup (no CLI) → **request/response
fundamentals** → **exercise** → **solutions** → gotchas.

- Sections 9–11 are ~460 lines (**40% of the chapter**) and duplicate Chapter 2 (routing, path params) and Chapter 3 (request/response). They sit *after* the tutorial, so the page runs long past the point the reader has a working app.
- The tutorial itself is sound material: a greeting API with a path parameter, then a product page with template inheritance.
- Ends on Gotcha 7. No recap, no "you now have X", no link to Chapter 2 `[LIVE]`.
- Named competitors: none. Numbers: none. Links to `/comparisons/`: none.

### Overlap with the Overview, measured

Both pages teach install → first route → first template → config → dev tools. Same
topics, two depths, and the copies disagree (`.twig` vs `.html`; "your browser opens"
vs the real `Start the server now? [Y/n]` prompt).

| Topic | Overview | Ch1 |
|---|---:|---:|
| Install | 15 | 181 (§2 + the duplicate CLI heading) |
| Routing / first route | 24 | 124 |
| Templates (+ static websites) | 28 | 145 |
| Env / config | 31 | 59 |
| Dev admin + error overlay + health | 12 | 33 |
| **Overlapping total** | **110 of 610** (18%) | **542 of 1133** (48%) |

Counting ch1 §9 Request & Response (187 lines, against the Overview's Routing and
Forms sections) takes the ch1 side to **64%**. The overlap is asymmetric: half of
Chapter 1 has an Overview counterpart at a fifth of the depth, while the Overview's
other 82% duplicates chapters 2–39 rather than Chapter 1. Neither page has a single
job — the Overview is an install guide plus a whole-book cheatsheet, Chapter 1 is a
tutorial plus a request/response reference plus an exercise book.

## 4. Chapter 1 against a real run

Measured today: `tina4 init python my-store` then `tina4 serve` in a scratch dir `[RUN]`.

| Chapter says | Reality |
|---|---|
| `tina4 --version` → `tina4 0.1.0` | `tina4 3.8.64` (3.8.67 available) |
| `uv sync` → `Resolved 1 package`, `tina4-python==3.1.0` | `Resolved 2 packages`, `Installed 1 package`, `tina4-python==3.13.94` |
| Banner `Tina4 Python v3.2.0` + `Database: sqlite:///data/app.db` | `Tina4 Python v3.13.94 — The Intelligent Native Application 4ramework`; prints Server / Swagger / Dashboard / Debug / Test Port lines; **no database line** |
| `/health` → `{"status","database","uptime_seconds","version","framework":"tina4-python"}` | `{"status":"ok","uptime_seconds":433,"version":"3.13.94","framework":"tina4py","errors":0}` — no `database` key, different framework string |
| `init` prints 20 `Created …/` lines incl. `src/seeds/`, `src/locales/`, `src/templates/errors/`, `src/public/scss/`, `src/public/icons/`, `secrets/`, `tests/` | 6 `✓` lines; creates `data/ logs/ migrations/ src/{routes,orm,templates,scss,public/{css,images,js}}` and nothing else |
| Then "Next steps: `cd`, `uv sync`, `tina4 serve`" | `init` already ran `uv sync`, then asks `Start the server now? [Y/n]` |
| `src/public/js/frond.js` and `src/public/css/tina4.css` shown as scaffolded files | both directories are empty on disk; the framework serves `/js/frond.js` and `/css/tina4.css` itself (200) |
| `.env` contains `TINA4_DEBUG=true` | contains `TINA4_DEBUG=true` **and** `TINA4_LOG_LEVEL=ALL` |
| `app.py` = docstring + `if __name__ == "__main__": run()` | 3 lines: `from tina4_python.core import run` / blank / `run()` |
| `tina4 init` "installs the Tina4 CLI globally (via cargo, homebrew, or direct download)" | false; and the chapter carries a second, unnumbered "Installing the Tina4 CLI" section with `cargo install tina4` right after the numbered one |
| `src/public/scss/` | `init` creates `src/scss/`; `serve` never creates `src/public/scss/` |

**Does `serve` provision the missing directories?** Yes. `_ensure_folders()` creates 16
on every boot: `src/{routes,orm,seeds,templates,templates/errors,public,public/js,public/css,public/icons,locales}`,
`migrations`, `data`, `data/.broken`, `logs`, `secrets`, `tests` `[SRC]` — confirmed by
tree diff `[RUN]`. So the chapter's structure tree roughly matches *post-serve* state
while claiming to show *post-init* state. `src/public/scss/` is wrong either way.

**Undocumented behaviour a first-timer meets anyway** `[RUN]`: an agent server on port
9146 with 7 agents scaffolded into `.tina4/agents/`, a "background thinking loop …
every 5 min", a stable test port on 8146, `/swagger` live, `.env.local` written with a
generated dev auth secret, `plan/` and `data/sessions/` created, `Discovered 3 routes`
on an empty project, and the browser opening by itself.

**CLI surface, measured** `[RUN]` — relevant because the rebuilt chapter is meant to
cover "how the CLI works":

- `tina4 --help` on 3.8.64 lists: `doctor setup install init serve scss ai i-want-to-stop-using-v2-and-switch-to-v3 update books docs agent build deploy env metrics help`.
- It does **not** list `migrate`, `test`, `generate` or `routes`, all four of which `/get-started/` documents. Three work anyway as passthroughs to `tina4python`: `migrate` prints `Nothing to migrate.`, `generate` offers 15 generators (model, route, crud, migration, middleware, test, form, view, auth, service, queue, validator, seeder, websocket, listener).
- `tina4 routes` in a fresh project prints the guard `Tina4 must be started with the tina4 CLI: tina4 serve (development)` instead of listing routes.
- `tina4 test` fails with `No module named pytest` — the scaffold installs no test runner.
- `serve` flags: `--port`, `--host`, `--dev`, `--production`, `--no-browser`, `--no-reload`, plus an optional project-name argument. `--help` says production servers are auto-detected and `--dev` forces the dev server, while the docs present `--production` as the opt-in.

## 5. Gap against the goal

| Needed | Present today |
|---|---|
| A reason to switch, in Python terms | nowhere in `/python/` |
| Lines-of-code argument | nowhere on the site |
| Dependency / install-size / feature numbers | only on `/comparisons/`, unlinked from `/python/` |
| Throughput numbers | only on `/comparisons/`, March 2026, unlinked |
| One mock program, start to finish | Chapter 1, buried at line 240 of 1136 |
| An exit ("now read Chapter 2") | neither page |

## 6. Reusable assets

- `/comparisons/` Python block `[REPO docs/comparisons.md]` — method stated (Apple Silicon 8-core, `hey`, 5 000 requests, 50 concurrency, 3 runs averaged, March 2026):

  | | Tina4 | Starlette | FastAPI | Flask | Django | Bottle |
  |---|---:|---:|---:|---:|---:|---:|
  | JSON req/s | 9 761 | 15 664 | 11 523 | 5 722 | 2 333 | 3 165 |
  | List req/s | 5 769 | 9 302 | 2 709 | 962 | 2 150 | 1 105 |
  | Features of 44 | 44 | 6 | 10 | 7 | 24 | 5 |
  | Dependencies | 0 | 4 | 12 | 6 | 20 | 0 |
  | Install size | 2.4 MB | 3.5 MB | 4.8 MB | 4.2 MB | 25 MB | 0.3 MB |

  Caveat on the same page: it opens with "Tina4 Python runs ASGI on uvicorn". uvicorn is
  **optional** — `_find_production_server()` tries uvicorn → hypercorn → granian and falls
  back to the built-in asyncio server; a default install has none of them and the dev
  banner prints `(asyncio)` `[SRC]` `[RUN]`. As written it undercuts the zero-dependency
  claim on the same page.

- `tina4-documentation/benchmark/benchmark.sh` — 569 lines, drives `hey` / `wrk` / `ab` across four endpoints (json, list, db, template) for tina4python, FastAPI, Flask, Django, Starlette, Bottle. Re-runnable, so numbers can be refreshed instead of quoted from March.
- `/general/01-what-is-tina4/` — 223 lines, the zero-dependency argument already written (security, size, portability, upgrades), language-agnostic.
- **Chapter 38: Complete Feature List** `[REPO]` — 190 lines, "97 built-in features", grouped into 13 tables (Core HTTP, Database, Auth, Templates, Caching, Background/Messaging, APIs, i18n, DX, Security, Additional, IoT, Parity). Every row names the dependency the built-in replaces: "instead of gunicorn/uvicorn config", "instead of body-parser", "instead of express-rate-limit". Already filed under the `Reference` sidebar group. This is the section's "is it in the box?" page — a different question from the Overview's "how do I write it", which is why the Overview's snippet index is a finder rather than a second feature list.

## 7. How these pages are produced

| Content | Repo | Note |
|---|---|---|
| Chapter 1 | `tina4-book/book-1-python/chapters/01-getting-started.md` | upstream; feeds the PDF via `scripts/build_pdf.py` |
| Overview | `tina4-documentation/docs/python/index.md` | site-only — never reaches the PDF |
| Sidebar groups | `tina4-documentation/tina4press.config.mjs` → `BACKEND_GROUPS` | generated from chapter stems |

`scripts/sync-books.sh` runs **book → docs**, escaping Twig for VitePress. Drift already
exists in that direction: `docs/python/01-getting-started.md` carries a site-only fix the
book lacks — the `.env` table row reads `TINA4_CORS_ORIGINS` / unset / deny-by-default in
docs, `CORS_ORIGINS` / `*` / "all origins allowed" in the book `[REPO]`. A sync would
regress it.

Every language section is the same species, so whatever shape Python lands on becomes the
template: `nodejs/index.md` 936 lines, `php/index.md` 739, `ruby/index.md` 566,
`js/index.md` 260, `delphi/index.md` 230 — all titled "Quick Reference" `[REPO]`.

## 8. Out of scope, verified, worth keeping

Not part of `/python/`, but on the path to it and confirmed dead `[LIVE]`:

| Link | Where | Status | Correct target |
|---|---|---|---|
| `github.com/tina4stack/tina4-documentation/blob/main/{python,nodejs,php,ruby,js,delphi}/index.md` | `/get-started/` "deeper dive" ×6 | 404 | `/python/`, `/nodejs/`, … (files live under `docs/`) |
| `…/blob/main/install-security.md` | `/get-started/` "For security teams" | 404 | `/install-security` (file is `docs/install-security.md`) |
| `/build-with-ai.md` | `/get-started/` "What's next" | 404 | `/build-with-ai` (200) |
| `github.com/tina4stack/tina4-documentation/benchmark/` | `/comparisons/` methodology | 404 | needs `/tree/main/benchmark/` |

The repo is public — these are wrong paths, not permissions. Also: `/get-started/` is not
in the top nav (hero button only), and its Python block never links to `/python/` or to
Chapter 1. Feature count conflicts site-wide — 97 (landing tagline), "70 other features"
(Python ch1), 44 (Introduction, and `/comparisons/` says 44 is only a comparison
denominator). Landing advertises v3.13.56 (2026-07-08); PyPI ships 3.13.94 `[RUN]`.
