# `repro/` — run the findings yourself

A real Tina4 app plus three probe scripts, one per claim in
[`../README.md`](../README.md). Nothing is simulated: the probes start an actual
`tina4 serve`, curl it, and read what comes back. Claim D talks to the live
`rag.tina4.com` endpoint that `tina4.com` itself calls.

The framework is never patched, shimmed or monkey-patched. The browser check is
black-box: Python's `webbrowser.open()` honours `$BROWSER`, so `lib/fake-browser.sh`
records any window the framework tried to open.

## Run it

```bash
cd repro
./run-all.sh
```

First run does a `uv sync` inside `mockapp/` (one package, a few seconds). Needs
`tina4`, `uv`, `curl`, `python3`, and network access for claim D.

Or run one at a time:

```bash
./probe-a-browser.sh      # A — browser opens onto a 404 with TINA4_DEBUG=false
./probe-bc-footer.sh      # B + C — the dev footer: no off-switch, two route counts
./probe-d-asktina4.sh     # D — Ask Tina4 links to GitHub, not the docs site
```

Each takes an optional port argument (defaults 7361/7362, 7363). The probes free
their own ports on the way out.

`probe-bc-footer.sh` pauses at the end and leaves the server up, because half of
claim B is something you have to see: dismiss the footer, click a link, watch it
return. Press Enter to shut it down.

## What you should see

```
Claim A — browser auto-open vs TINA4_DEBUG

TINA4_DEBUG=false   (port 7371)
  GET /              -> 404  <title>404 Error - </title>
  GET /__dev         -> 404
  browser opened     -> BROWSER_OPENED: http://localhost:7371
  FAIL  CONFIRMED: a browser window was opened onto a 404 with debug off.

TINA4_DEBUG=true   (port 7372)
  GET /              -> 200  <title>Tina4Python</title>
  browser opened     -> BROWSER_OPENED: http://localhost:7372
  PASS  Browser opened onto a real landing page — correct behaviour.
```

```
C — footer count vs dashboard count
  dev footer (raw table)          : 99
  /__dev/api/routes (filtered)    : 98
  FAIL  CONFIRMED: two numbers for one router table, off by 1.

  Which route is being dropped:
    /__health                  in dashboard list: True
    /health                    in dashboard list: False
```

```
D — where the link goes vs where the page lives
      indexed : https://github.com/tina4stack/tina4-book/blob/main/book-1-python/chapters/06-orm.md
      correct : https://tina4.com/python/06-orm/
```

A `FAIL` line means the reported behaviour reproduced. A `PASS` on claim A or B
means your version has been fixed since the report — the probes are written to
say so rather than to always go red.

## The mock app

`mockapp/` is a normal Tina4 project — `app.py`, `src/orm/`, `src/routes/`,
sqlite, nothing exotic. Two files carry the whole demonstration.

**`src/orm/models.py`** — 19 models, each with `auto_crud = True`. That flag is
the documented Chapter 6 one-liner and generates five REST routes per model:

```
GET    /api/<table>        POST   /api/<table>
GET    /api/<table>/{id}   PUT    /api/<table>/{id}   DELETE /api/<table>/{id}
```

19 × 5 = 95. Plus one hand-written route, plus the three the framework registers
itself, the footer reads exactly **99 routes** — the number in the bug report,
reached without padding anything. Delete a model, restart, and it drops by 5.

**`src/routes/hello.py`** — one route, `/hello/{page}`, deliberately parameterised
so two clickable URLs cost one router entry and the total stays at 99. It returns
HTML because the dev toolbar is only injected into `text/html` responses. Every
number on the page is read live from `Router.get_routes()` at render time and the
filtered count is fetched from `/__dev/api/routes` in the browser, so the page
compares the two itself and stays truthful if you edit the models.

No database is needed for any of this. Routes register at import time in the ORM
metaclass; only executing a query would touch the DB. The `.env` points at sqlite
so nothing has to be installed either way.

### Poking at it by hand

```bash
cd mockapp
cp .env.example .env      # TINA4_DEBUG=true
tina4 serve -p 7400
```

Then open `http://localhost:7400/hello/one`. Flip `TINA4_DEBUG` to `false` in
`.env`, restart, and watch a browser window open onto a 404 while `/__dev` and the
footer are gone.

## Layout

```
repro/
  run-all.sh              all three probes in sequence
  probe-a-browser.sh      claim A
  probe-bc-footer.sh      claims B + C
  probe-d-asktina4.sh     claim D
  lib/
    common.sh             server start/stop, count readers, output helpers
    fake-browser.sh       $BROWSER shim — records what got opened
  mockapp/                the Tina4 project under test
    src/orm/models.py     19 AutoCRUD models = 95 routes
    src/routes/hello.py   the one hand-written route
  .runs/                  gitignored: server logs, scratch .env files, RAG responses
```

Probe output is terse by design; `../README.md` has the source line references,
the version matrix, and the recommended fixes.

## A note on measuring the footer count

`lib/common.sh` scopes its search to the `tina4-dev-toolbar` div before matching
`N routes`. Grepping the whole page instead picks up any prose that happens to
mention a route count and silently reports the wrong number — which is exactly
how the first pass at this investigation briefly convinced itself the counts
agreed. Worth knowing if you extend these scripts.
