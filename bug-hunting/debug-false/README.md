# `TINA4_DEBUG=false` browser-open, dev-toolbar, route count, Ask-Tina4 links

**Reporter query (verbatim):**
> "Some things spotted tonight (again I might be uninformed)
> Setting TINA4_DEBUG=false, still tries to generate the dashboard, just says it cant find it. Surely it should not even open a browser window for that.
> If the __dev is on, on the website there is a footer that comes back on each click. How can we turn that off.
> On the same footer it shows 99 routes, not sure what that is, but surely there is something amiss there.
> On the Tina4.com when asking Tina4, it produced a link for futher reading that took me to github. It should take me to the appropriate page on the site"

Four claims, split A–D. **All four investigated empirically** — live `tina4 serve` runs, a
clean-room `tina4 init python` project, and live calls to the `tina4.com` RAG endpoint.
Verdicts:

| | Claim | Verdict | Solution |
|---|---|---|---|
| **A** | `TINA4_DEBUG=false` still opens a browser onto a page that 404s | **Confirmed — reproduced** | Gate `_open_browser()` on `is_debug` too |
| **B** | Dev footer returns on every click; no way to turn it off | **Confirmed — no off-switch exists** | **Both:** add `TINA4_NO_TOOLBAR` env flag, and make the footer's ✕ persist |
| **C** | Footer "99 routes" is wrong | **Two defects confirmed; the 99 itself is now OPEN** — reporter has no AutoCRUD, so the count has no known source | Match health paths exactly instead of by prefix; one shared source for all three route listings; make the count clickable into a route browser grouped by origin |
| **D** | Ask Tina4 "further reading" links to GitHub, not the site | **Confirmed — reproduced, plus a worse second defect** | Store the site URL at RAG ingest; harden `md()` against `[text](<url>)` |

### Versions under test

| Component | Version |
|---|---|
| `tina4` CLI (Rust) | **3.8.64** (investigated on 3.8.58) |
| `tina4-python` (harness workspace, `documentation-testing/pypy/`) | **3.13.94** (investigated on 3.13.49) |
| `tina4-python` (clean-room `tina4 init python`, latest from PyPI) | **3.13.94** |

A–C were verified on **both** 3.13.49 and 3.13.94 — none of them are fixed on latest.
Re-checked against 3.13.94 on 2026-07-30 after `tina4 update` + `uv lock --upgrade-package
tina4-python`: every source line reference below still resolves, `TINA4_NO_TOOLBAR` still
does not exist anywhere in the package, and the ✕ at `dev_admin/__init__.py:2139` still has
no persistence. Nothing in A–D has been fixed upstream.

### Run it yourself

`repro/` holds a working Tina4 app and one probe script per claim:

```bash
cd repro
./run-all.sh
```

The mock app carries 19 `auto_crud = True` models, so its dev footer reads exactly
**99 routes** — the reporter's number, reached without padding. See
[`repro/README.md`](repro/README.md).

To check the claims by eye instead, serve the app yourself and follow
[`MANUAL.md`](MANUAL.md):

```bash
cd repro
./serve-manual.sh true      # debug ON  — claims B and C
./serve-manual.sh false     # claim A
```

### Reproduction method (A–C)

The browser-open check is black-box: `webbrowser.open()` honours `$BROWSER`, so a shim
script that appends its argv to a log file records whether the framework opened anything.
No framework patching, no monkey-patching — read-only-framework rule respected.

```bash
# fake-browser.sh
echo "BROWSER_OPENED: $*" >> "$BROWSER_LOG"
```

```bash
export BROWSER=./fake-browser.sh BROWSER_LOG=./browser.log
export TINA4_ENV_FILE=./env-false          # honoured by load_env()
printf 'TINA4_DEBUG=false\nTINA4_LOG_LEVEL=ALL\n' > ./env-false
tina4 serve -p 7333
```

---

## A — `tina4 serve` opens a browser onto a 404 when `TINA4_DEBUG=false`

**Confirmed.** Reproduced on 3.13.12 *and* on a clean-room `tina4 init python` project at
3.13.94.

### Observed

`TINA4_DEBUG=false`, harness workspace, port 7333:

```
=== GET / ===
<title>404 — Not Found</title>
=== toolbar present in / ? ===          (none)
=== /__dev status ===
404
=== BROWSER LOG ===
BROWSER_OPENED: http://localhost:7333
```

Clean-room 3.13.94 project, `TINA4_DEBUG=false`, port 7336 — identical:

```
--- GET / title ---
<title>404 — Not Found</title>
--- /__dev ---
404
--- BROWSER LOG ---
BROWSER_OPENED: http://localhost:7336
```

Same project with `TINA4_DEBUG=true` (port 7337) for contrast — the landing page exists:

```
--- GET / title ---
<title>Tina4Python</title>
--- /__dev ---
200
```

### Root cause

Two independent gates that were never wired to each other.

The browser open is gated **only** on the `--no-browser` flag / `TINA4_NO_BROWSER` env —
never on `TINA4_DEBUG` (3.13.94 `core/server.py:2799-2801`; same code at 3.13.12
`core/server.py:2167-2169`):

```python
_skip_browser = no_browser or os.environ.get("TINA4_NO_BROWSER", "").lower() in ("true", "1", "yes")
if not _skip_browser:
    _open_browser(f"http://{display}:{port}")
```

The page it lands on **is** gated on dev mode (3.13.12 `core/server.py:1392-1393`):

```python
elif request.path == "/" and _is_dev_mode():
    response.html(_render_landing_page())
```

With `TINA4_DEBUG=false` the `elif` is skipped, the request falls through to the 404
handler, and the browser opens onto "404 — Not Found". `is_debug` is already computed
~35 lines above the `_open_browser()` call in the same function (used to derive `_ai_port`
and to pick the production server) — it simply isn't consulted.

The reporter's phrasing "still tries to generate the dashboard, just says it cant find it"
is precise: the framework decides to open a browser window without ever checking whether
there is a dev landing page to show.

**Scope check — debug mode does not break user routes.** Worth ruling out, since a 404 on
`/` could also have meant a real route failing to resolve. Adding a user-defined
`@get("/")` to the mock app gives `GET /` → **200** with the user's own body under *both*
`TINA4_DEBUG=false` and `true`, and it takes precedence over the framework landing page
when debug is on. So the 404 only ever appears when the project genuinely has no `/`
route, and the unwanted window is the entire defect.

### Recommended fix

```python
if not _skip_browser and is_debug:
    _open_browser(f"http://{display}:{port}")
```

A production run (`TINA4_DEBUG` unset or false) should open no browser at all. Note this
also fires for `tina4 serve --production`, where popping a browser tab on a server boot is
actively wrong.

---

## B — No off-switch for the dev footer, and its ✕ doesn't stick

**Confirmed.** Two separate things behind the reporter's question, both real.

### B1 — the ✕ close button has no persistence

The toolbar's close button is inline-only (3.13.94 `dev_admin/__init__.py:2139`):

```html
<span onclick="this.parentElement.style.display='none'" ...>&#10005;</span>
```

No `localStorage`, no cookie, no server round-trip. Every HTML response re-injects the
toolbar server-side, so the next click restores it — exactly "a footer that comes back on
each click."

The sharp edge: **the dashboard overlay sitting in the same toolbar does persist.** Twenty
lines below the close button, the overlay toggle writes `localStorage`
(`dev_admin/__init__.py:2166-2175`):

```js
var STATE_KEY = 'tina4_dev_overlay_open';
...
try { localStorage.setItem(STATE_KEY, hide ? '0' : '1'); } catch (_) {}
```

So one dismissal in the toolbar survives reloads and the other doesn't. That inconsistency
is what makes the behaviour read as a bug rather than a design choice.

### B2 — no env flag suppresses the toolbar

Injection is gated on `is_dev` alone (3.13.94 `core/server.py:1833-1834`):

```python
if is_dev and response.content_type and "text/html" in response.content_type:
    if not request.path.startswith("/__dev"):
```

Grepped 3.13.94 for `NO_TOOLBAR` / `TOOLBAR` / `HIDE_TOOLBAR` / `DEV_TOOLBAR` across the
whole package — **zero hits.** The neighbouring knobs all exist and are documented in the
Rust CLI's env table (`TINA4_NO_RELOAD`, `TINA4_NO_AI_PORT`, `TINA4_NO_BROWSER`,
`TINA4_SUPPRESS`), but none of them touches the toolbar:

- `TINA4_NO_RELOAD` only omits the live-reload polling script **inside** the toolbar — the
  toolbar itself still renders.
- `TINA4_SUPPRESS` silences the startup ASCII banner only.

So the only way to remove the footer is `TINA4_DEBUG=false`, which also gives up the error
overlay, live reload, `/__dev`, Swagger, and the MCP dev tools. There is no answer to
"how can we turn that off" today.

### Recommended fix

**Do both.** They answer different halves of the reporter's question and neither one
subsumes the other: the flag is for *"never show me this on this project"*, the persistent
✕ is for *"not right now"*.

**1. `TINA4_NO_TOOLBAR` env flag** — checked alongside `is_dev` in `_finalize_response()`
(`core/server.py:1833`), matching the existing `TINA4_NO_*` naming:

```python
from tina4_python.dotenv import is_truthy

_no_toolbar = is_truthy(os.environ.get("TINA4_NO_TOOLBAR", ""))
...
if is_dev and not _no_toolbar and response.content_type \
        and "text/html" in response.content_type:
```

Register it in the Rust CLI's env table next to `TINA4_NO_RELOAD`, described as
*"Disable the dev toolbar (footer) without leaving debug mode"*. Everything else gated on
`TINA4_DEBUG` — error overlay, live reload, `/__dev`, Swagger, MCP dev tools — stays on.

**2. Make the ✕ persist** — replace the inline `onclick` at
`dev_admin/__init__.py:2139` with the same `localStorage` pattern the overlay toggle
already uses ~20 lines below, and honour the stored value when the toolbar renders:

```js
var BAR_KEY = 'tina4_dev_toolbar_hidden';
function tina4HideToolbar() {
    var el = document.getElementById('tina4-dev-toolbar');
    if (el) el.style.display = 'none';
    try { localStorage.setItem(BAR_KEY, '1'); } catch (_) {}
}
// on load, before first paint
try {
    if (localStorage.getItem(BAR_KEY) === '1') tina4HideToolbar();
} catch (_) {}
```

That removes the inconsistency rather than routing around it — one dismissal in the bar
behaving like the other. Worth a way back (the `/__dev` dashboard could clear the key, or
`TINA4_NO_TOOLBAR=false` could force it visible) so a user who hides it can't get stuck.

Cross-framework note: the overlay's `localStorage` key is already shared verbatim with
PHP / Ruby / Node for parity, so both changes should land in all four.

---

## C — "99 routes": two defects confirmed, and the 99 itself is unexplained

**Partly confirmed, and one part reopened.** Two adjacent defects are confirmed outright,
and one of them means the footer number is *always* wrong by a small amount. Whether the
reporter's **99** is itself inflated is now **open** — the explanation that accounted for it
(AutoCRUD) was ruled out by the reporter directly. See C1.

### C1 — where the number comes from: hypothesis ruled out, now open

A clean-room `tina4 init python` project with **zero** user route files shows:

```
--- footer route count ---
3 routes
--- api/routes ---
{"routes":[{"path":"/__health",...},{"path":"/__frond/live/{name}",...}],"count":2}
```

So the framework floor is 3, not ~90. The `/__dev/*` surface (70+ paths) is **not** in
`Router.get_routes()` — those are dispatched from a separate `get_api_handlers()` table
(`dev_admin/__init__.py:389+`), so they never reach the footer count. An earlier
source-only reading of mine got this wrong; the live count disproves it.

In the harness workspace (13 route files) the footer shows 46, broken down by handler
module:

```
 10  tina4_python.crud          <- AutoCRUD, generated from the user's own models
 34  src.routes.*               <- the user's routes
  1  tina4_python.core.server   <- /__health
  1  (filtered, see C2)
```

The 10 `tina4_python.crud` routes are AutoCRUD expansions of user models — **5 REST routes
per `auto_crud=True` model** (`GET`/`POST` on `/api/x`, `GET`/`PUT`/`DELETE` on
`/api/x/{id}`).

**AutoCRUD was the working hypothesis for the reporter's 99, and it is now ruled out.**
Asked directly, the reporter said: *"No, was a standard project which took a static site of
about 4 pages and upgraded it."* No AutoCRUD. The arithmetic that fit so neatly
(16 hand-written + 3 framework + 16 models × 5 = 99) was coincidence.

That leaves 99 unexplained, because the package has exactly three registration sites and
nothing else reaches the router table:

| Site | Registers |
|---|---|
| `core/router.py:668` | `@get`/`@post`/… decorators — the user's own routes |
| `crud/__init__.py:142,158,182,216,238` | AutoCRUD, 5 per `auto_crud=True` model |
| `core/server.py:443,445,451` | `/__health`, `/health`, `/__frond/live/{name}` |

In particular there is **no template or static-file auto-registration** — static assets are
served without router entries (verified: `/js/…` and `/images/…` return 200 while absent
from the count). So with AutoCRUD excluded, 99 implies ~96 decorator registrations, which a
four-page static-site upgrade should not produce.

Two live possibilities, undecided:

1. The reporter has far more `@get`/`@post` registrations than they realise — the table
   counts `(method, path)` pairs, so `@get` + `@post` on one path is two entries.
2. There is a genuine inflation path not yet found — which is what their original "surely
   there is something amiss" instinct claimed.

**Needed to settle it:** the reporter's actual route list, from `/__dev/api/routes` or the
dashboard's `routes` dev-tool (`dev_admin/__init__.py:1709`, prints the raw table). 96 real
routes means (1); repeats or unexpected paths mean (2) and C1 becomes a confirmed finding
rather than a disproved one.

Until then C1's verdict is **open**, not "count is honest". C2 and C3 are unaffected — both
were verified directly and stand on their own.

### C2 — footer count and dashboard count permanently disagree

The footer says one number, `/__dev/api/routes` says another, on every single run:

| Project | Footer | `/__dev/api/routes` count |
|---|---|---|
| clean-room, empty | **3** | **2** |
| harness workspace | **46** | **45** |

Root cause is a prefix-match mismatch. The framework registers **two** health routes
(3.13.94 `core/server.py:442-445`):

```python
_HEALTH_PATH = os.environ.get("TINA4_HEALTH_PATH", "/__health")
...
if _HEALTH_PATH != "/health":
    Router.add("GET", "/health", _health_handler)
```

The footer uses the raw table — `len(Router.get_routes())`, counting both
(`core/server.py:1840`). The dashboard's `_api_routes` filters
(`dev_admin/__init__.py:590-596`):

```python
internal_prefixes = ("/__dev", "/health", "/swagger")
...
if path.startswith(internal_prefixes):
    continue
```

`"/__health".startswith("/health")` is **False** — the string is `/__health`, not
`/health`. So the filter hides the legacy `/health` alias but lets the canonical
`/__health` through. Result: `/__health` is listed as if it were an app route, `/health` is
hidden, and the two counts differ by exactly one, forever. The reporter's "surely there is
something amiss there" instinct is right; the defect just isn't where they thought.

### C3 — the count is unexplained and undrillable

The footer renders a bare `{route_count} routes` (`dev_admin/__init__.py:2136`) with no
tooltip, no link, and no breakdown. A user with 20 AutoCRUD models has no way to learn
that 100 of their routes are generated rather than hand-written. The number is correct and
still reads as suspicious.

### Verified non-causes

- **Reload inflation** — hypothesised that `_api_reload`'s re-run of `_auto_discover`
  double-registers. It does not. Five consecutive `POST /__dev/api/reload` calls, reading
  the footer between each: `46/45` every time, no drift. `_register_route`
  (`core/router.py:360-365`) has explicit replace-on-same-`(method, path)` semantics, and
  3.13.94 even logs a before/after delta (`dev_admin/__init__.py:1968-1972`).
- **`/__dev/*` routes polluting the count** — disproved above; they are not in the router
  table.

### Recommended fix

1. Fix the filter to match the real health paths — compare against the resolved
   `_HEALTH_PATH` and the `/health` alias explicitly, not a `/health` prefix. Same bug
   class would bite a `/healthz` app route, which the filter silently hides today.
2. Make the footer and the dashboard use one shared counting function so they cannot
   disagree.
3. **Make the count clickable — open a route browser from the footer.** (Suggested during
   review, and the strongest of the three: it answers "not sure what that is" by letting the
   user look, instead of asking the framework to guess what summary they wanted.) Clicking
   `99 routes` opens the route list, grouped by origin:

   ```
   your routes        16     GET /  · GET /other · …
   AutoCRUD           80     16 models × 5 · GET|POST /api/users · …
   framework           3     GET /__health · GET /health · GET /__frond/live/{name}
   ```

   The plumbing is already there — `_api_routes` (`dev_admin/__init__.py:586`) serves the
   list as JSON and the toolbar already links out to `/__dev`, so this is UI wiring rather
   than new machinery. Origin is cheap to derive: the handler's `__module__` is
   `tina4_python.crud` for AutoCRUD, `tina4_python.*` for framework, anything else is the
   user's.

   A label alone (`"16 app / 99 total"`) is the cheap fallback if the click-through is too
   much, but it still can't answer *which* routes.

4. **Collapse the three route-listing code paths into one.** There are currently three, and
   they disagree: the footer's `len(Router.get_routes())` (raw), `_api_routes` (filtered),
   and a `routes` dev-tool (`dev_admin/__init__.py:1709`) that subprocesses out to print
   `Router.get_routes()` raw. Two of the three bypass the filter, so the dashboard is the
   odd one out. A route browser built on one shared source makes C2 unrepresentable rather
   than merely fixed.

---

## D — Ask Tina4 links to GitHub markdown source instead of the docs site

**Confirmed and reproduced.** Plus a second, worse defect the reporter didn't see.

### How the widget works

`https://tina4.com/` ships `/assets/client.js` with:

```js
__TP_CHAT__={"api":"https://rag.tina4.com","label":"Ask Tina4","model":"Powered by Tina4",...}
```

It `POST`s to `https://rag.tina4.com/v1/ask` with `{query, language, k: 6, stream: false}`
and renders `d.answer` through a small local `md()` markdown converter.

### Observed — reproduced against the live endpoint

```bash
curl -s -X POST https://rag.tina4.com/v1/ask -H 'Content-Type: application/json' \
  -d '{"query":"How do I use the ORM?","language":"python","k":6,"stream":false}'
```

Tail of `answer`:

```
For detailed documentation and further examples, you can refer to the
[source](https://github.com/tina4stack/tina4-book/blob/main/book-1-python/chapters/06-orm.md).
```

Same shape for `"How do I define a route?"` →
`.../book-1-python/chapters/02-routing.md`. The `sources[]` array carries the same GitHub
blob URLs:

```json
{"url": "https://github.com/tina4stack/tina4-book/blob/main/book-1-python/chapters/02-routing.md",
 "title": "Chapter 2: Routing (book-1-python/chapters/02-routing.md)",
 "language": "python", "distance": 0.3856}
```

### Root cause

The **RAG index stores a GitHub blob URL as each chunk's `url`**. The answer's
`[source](...)` link and the `sources[]` entries both come straight from that field. The
frontend does no URL rewriting whatsoever — `md()` only turns `[text](url)` into an
`<a href>`. So this is an indexing-side defect, not a website-frontend one.

The mapping to the published page is entirely mechanical:

| Indexed `url` | Correct site page |
|---|---|
| `…/book-1-python/chapters/02-routing.md` | `https://tina4.com/python/02-routing/` |
| `…/book-1-python/chapters/06-orm.md` | `https://tina4.com/python/06-orm/` |

Both site URLs verified live: `…/02-routing.html` and `…/06-orm.html` each `301` to the
trailing-slash form, which returns `200`. The correct destination exists — the index just
points elsewhere.

### D2 — the GitHub link is often not merely wrong, it's broken

The routing answer emitted the CommonMark angle-bracket destination form:

```
[source](<https://github.com/tina4stack/tina4-book/blob/main/book-1-python/chapters/02-routing.md>)
```

`md()` HTML-escapes first, then applies `\[([^\]]+)\]\(([^)\s]+)\)`, which captures the
angle brackets as part of the URL. Replaying the exact frontend transform on the real
response produces:

```html
<a href="&lt;https://github.com/tina4stack/tina4-book/blob/main/book-1-python/chapters/02-routing.md&gt;"
   target="_blank" rel="noreferrer">source</a>
```

That is a **relative** href. Clicking it resolves against the current page and 404s —
verified:

```
curl -o /dev/null -w '%{http_code}' \
  "https://tina4.com/python/%3Chttps://github.com/.../02-routing.md%3E"
404
```

So depending on which form the model emits, "further reading" either sends the user to raw
markdown on GitHub or to a dead link on tina4.com. The second is worse and is a frontend
bug independent of the index.

### Recommended fix

1. **Index-side (primary):** store the published site URL in each chunk's `url`
   (`https://tina4.com/<lang>/<NN-topic>/`), derived from the book path at ingest.
   Optionally keep the GitHub URL in a separate `source_url` field for "edit this page"
   affordances. This fixes the answer text and `sources[]` together.
2. **Frontend hardening:** strip a wrapping `<`/`>` (post-escape: `&lt;`/`&gt;`) from the
   captured destination in `md()`, and reject any destination that isn't `http(s):` or a
   site-relative path, so a malformed model emission can never render as a broken relative
   link.

---

## Notes for upstream filing

Nothing filed yet — no GitHub issue number assigned, hence this lives in
`bug-hunting/debug-false/` rather than an `issue-<n>/` directory.

Split across repos when filing:

| Finding | Repo / component | Severity | Solution |
|---|---|---|---|
| **A** browser opens onto 404 with `TINA4_DEBUG=false` | `tina4-python` (`core/server.py:2799`) — likely all four frameworks, worth a parity check | Functional; hits the recommended production config | Add `and is_debug` to the `_skip_browser` condition; `is_debug` is already in scope |
| **B1** ✕ dismissal doesn't persist while the overlay's does | `tina4-python` (`dev_admin/__init__.py:2139`) | DX inconsistency | Persist to `localStorage['tina4_dev_toolbar_hidden']`, same pattern as the overlay toggle |
| **B2** no `TINA4_NO_TOOLBAR` switch | `tina4-python` (`core/server.py:1833`) + Rust CLI env table | Missing feature | New `TINA4_NO_TOOLBAR` env, checked alongside `is_dev`; register in the CLI env table |
| **C2** footer count ≠ dashboard count; `/health` prefix filter misses `/__health` | `tina4-python` (`dev_admin/__init__.py:590`) | Real off-by-one, plus hides any `/health*` app route | Compare against resolved `_HEALTH_PATH` + the `/health` alias exactly, not by prefix; share one counter with the footer |
| **C3** route count unlabelled / undrillable | `tina4-python` (`dev_admin/__init__.py:2136`) | UX — and it's why C1 can't be answered without asking the reporter | Make the count clickable into a route browser grouped by origin (yours / AutoCRUD / framework); `"N app / M total"` as the cheap fallback |
| **C4** three route-listing code paths that disagree | `tina4-python` (`dev_admin/__init__.py:586`, `:1709`, `core/server.py:1840`) | Latent — C2 is one symptom of it | Collapse onto one shared source so footer, `_api_routes` and the `routes` dev-tool cannot diverge |
| **D1** RAG index stores GitHub blob URLs | `rag.tina4.com` ingest pipeline | Wrong destination on every answer | Store `https://tina4.com/<lang>/<NN-topic>/` as the chunk `url`; keep GitHub in a separate `source_url` |
| **D2** `md()` mangles `[text](<url>)` into a broken relative link | `tina4.com` `/assets/client.js` | Dead link | Strip wrapping `&lt;`/`&gt;` from the captured destination; reject non-`http(s):` / non-site-relative hrefs |

A is the one with real functional impact. **C1 is not ready to file** — the AutoCRUD
explanation was ruled out by the reporter (no AutoCRUD in their project), so the 99 has no
known source and needs their route list before anything is claimed about it either way.
Filing it as "working as intended" would be wrong.

The reporter's hedge ("I might be uninformed") was unwarranted. Three of four claims
reproduce exactly as described; the fourth turned out to sit next to two confirmed defects
*and* a still-unexplained count — so on C they were closer to right than the first pass
gave them credit for.
