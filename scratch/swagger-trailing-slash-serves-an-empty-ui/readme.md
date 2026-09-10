# `GET /swagger/` answers 200 with a Swagger UI that can never load

**tina4-nodejs source `fe3b87d` plus our `f-sw-01` fix (`041f3d0`), node v22.22.2, 2026-09-08.**
Control: published tina4-python 3.13.134, unmodified.

## Why this is measured on a patched tree

On published 3.13.134 both `/swagger` and `/swagger/` serve the same broken page, so this defect
cannot be seen next to `f-sw-01` — the guard bug hides it. Everything here is therefore measured
on a tree that already carries the `f-sw-01` guard fix, which is the honest way to see what that
fix leaves behind. `probe.ts` refuses to be run any other way by design: it takes the tree as
`SB=` and reports which one every number came from.

## The issue

With swagger on, and nothing else configured:

```
GET /swagger       -> 200   the real UI, asks for /swagger/openapi.json
GET /swagger/      -> 200   a DIFFERENT page, asks for "{SWAGGER_ROUTE}/swagger.json"
GET /api/items     -> 200
GET /api/items/    -> 404
```

The last line is the control, and it is what makes this a defect rather than a preference.
**Every ordinary route answers a trailing-slash miss with an honest 404.** The swagger path
answers it with a 200 and a page whose document can never resolve — an empty Swagger UI, with
nothing in the server output to say so.

Two more members of the same family, found by attacking the first fix:

```
GET /swagger//           -> 200   same dead page
GET /swagger/index.html  -> 200   same dead page   (the shared contract REQUIRES a 200 here)
```

## The mechanism

Three lines, in this order:

1. `packages/swagger/src/ui.ts:62` registers the UI at pattern `/swagger`.
2. `packages/core/src/router.ts:355-365` will retry `/foo/` as `/foo` — **but only when
   `TINA4_TRAILING_SLASH_REDIRECT=true`**, which is off by default. So `/swagger/` misses.
3. A route miss falls through to `serveStaticAsset` (`server.ts:1568`, "No route claimed the
   path, so NOW try the filesystem"), whose index resolution turns the directory
   `packages/core/public/swagger/` into its `index.html`.

And that file is dead by construction. `packages/core/public/swagger/index.html:74` reads

```js
url: "{SWAGGER_ROUTE}/swagger.json",
```

Both halves are wrong: `SWAGGER_ROUTE` is the **only** occurrence of that token in the entire
repo and in the published package — nothing substitutes it — and `swagger.json` is not a route in
any of the four ports either. The document is at `/swagger/openapi.json`.

So: **a miss on a swagger path is answered by a bundled page that asks for a URL which has never
existed.**

## Disproving it

- **Necessary.** Move that one file aside, change nothing else: `/swagger/` becomes **404**,
  exactly like `/api/items/`. Restored immediately; tree verified clean afterwards.
- **Control.** `/api/items/` 404s under the identical configuration, so this is not "the
  framework has no trailing-slash support" — that part is a documented opt-in behaving as
  documented. It is that one path lying instead of 404ing.
- **Conditional, and said so.** With `TINA4_TRAILING_SLASH_REDIRECT=true` the route claims
  `/swagger/` and serves the real UI. There is a supported configuration in which this is fine.
  The default is not it.
- **No second instance to broaden into.** The framework ships 12 static files;
  `swagger/index.html` is the only `index.html` among them, and `{SWAGGER_ROUTE}` is the only
  unsubstituted `{TOKEN}` in the whole bundled set.
- **Not intended behaviour.** Unmodified published tina4-python answers `/swagger` and
  `/swagger/` identically, both the real UI pointing at `/swagger/openapi.json`, with no env var
  set. And upstream's own contract test requires a 200 at `/swagger/`
  (`test/swaggerContract.test.ts:389`) — a requirement currently satisfied *only* by the dead
  file, which is why their suite never noticed.

## Cross-port: this is not nodejs-only

Measured on unmodified published **tina4-python 3.13.134**:

| path | python | nodejs (`f-sw-01` fixed) |
|---|---|---|
| `/swagger` | 200 real UI | 200 real UI |
| `/swagger/` | 200 real UI | **200 dead page** |
| `/swagger//` | **200 dead page** | **200 dead page** |
| `/swagger/index.html` | **200 dead page** | **200 dead page** |

So python has the same defect in the narrower form: its handler claims the canonical
trailing-slash path, but the dead bundled asset is still reachable underneath it. **tina4-ruby
ships the identical unsubstituted file** (`lib/tina4/public/swagger/index.html`) and serves
bundled swagger assets when the gate is open (`lib/tina4/rack_app.rb:232`), so it is affected the
same way — **read, not run.** **tina4-php ships no such asset at all** and renders its UI only
from `renderSwaggerUI()`, so the shape cannot occur there; its worst case on a miss is an honest
404.

## The fix

`gitdir/tinaforks/tina4-nodejs`, branch `fix/swagger-routes-never-register` (stacked on
`041f3d0` so one pull request carries the whole symptom). Uncommitted.

Two changes, because the family has two reachable halves:

1. **`packages/swagger/src/ui.ts` — register the UI at `/swagger/` as well**, sharing one
   `serveUi` handler with `/swagger` so the two forms cannot drift apart. Deliberately *not* done
   by defaulting `TINA4_TRAILING_SLASH_REDIRECT` on: that would change how every route in the
   framework treats trailing slashes, which is a behaviour decision for the maintainer and is not
   what the evidence is about.
2. **`packages/core/public/swagger/index.html` — one string**, the dead
   `{SWAGGER_ROUTE}/swagger.json` becomes `/swagger/openapi.json`. This is what closes
   `/swagger//` and `/swagger/index.html`, which registering a route cannot reach.

Deliberately **not** in the fix: deleting the bundled asset (the shared contract requires it to
answer 200), adding template substitution to static serving for one file, changing global
trailing-slash matching, and porting either change to python or ruby — each of those is its own
decision.

### What gates what

`test/swaggerGateAgrees.test.ts` grew a second axis: every way to *reach* a UI page
(`/swagger`, `/swagger/`, `/swagger//`, `/swagger/index.html`), and for each, the document URL
read out of the HTML that was actually served and then fetched. 12 boots, 98 assertions, ~14s.
Redirects are followed rather than asserted against, so serving the UI directly and redirecting
to it both pass; what cannot pass is ending up on a page whose document does not resolve.

Three components, each reverted **alone** against the shipped source:

| reverted | result | which assertions |
|---|---|---|
| all three present | **98 passed** | — |
| the `f-sw-01` guard | 66 passed, **32 failed** | the document is gone on every path, and both CDN assertions |
| the `/swagger/` route | 97 passed, **1 failed** | `TINA4_SWAGGER_UI_CDN` is honoured at `/swagger/` |
| the bundled asset's token | 86 passed, **12 failed** | `/swagger//` and `/swagger/index.html` round-trips |

The middle row is the interesting one, and it is why there is a CDN assertion at all. Once the
bundled file works, removing the `/swagger/` route no longer breaks the page — it just quietly
hands that one path to a **different Swagger UI implementation**, the bundled one, which hardcodes
cdnjs while the route-rendered page loads from `TINA4_SWAGGER_UI_CDN`. An air-gapped deployment
repointing that variable at a local mirror would have kept reaching cdnjs on `/swagger/` alone.
Without that assertion the route would have been indistinguishable from dead weight, so it was
written rather than assumed.

Upstream's own swagger suites on the fixed tree: `swaggerContract`, `swaggerParity31396`,
`swaggerPathParams` — 3 files, 36 tests, all passed; `swaggerStaticGate` 12, `swaggerConfig` 21,
`swagger` 75, `swaggerStackedMeta` 8, all passed. `swaggerStaticGate` and `swaggerContract` are
the two that could reasonably have objected to touching the bundled asset; neither did.

## Effect on the rest of the suite

Both runs on a **pre-built** tree, so unlike the `f-sw-01` measurement neither run was warmed by
the other. Baseline is the same code with only `f-sw-01` in it:

| | `f-sw-01` only | + `f-sw-02` |
|---|---|---|
| assertions | 8260 passed, 41 failed | 8312 passed, 37 failed |
| files | 354 (18 failed) | 354 (18 failed) |
| vitest batch | 12 passed | 12 passed |
| failing file set | — | **identical** |

**Nothing introduced and nothing cleared.** Nothing cleared is the expected result: no upstream
test covers this defect, which is why it shipped. `swaggerGateAgrees.test` reports 98 passed
inside the real suite run, so the gate runs in CI rather than only by hand.

The assertion totals moved by more than the 62 this change adds, so the counts are not compared —
only the sets are. The whole of that difference is one file: `aiSkillInstall.test` fails in **both**
runs and simply died earlier in the second (`died before reporting`, `got: []` rather than
`got: [tina4-developer-nodejs, tina4-maintainer]`). It reads which skills are installed from the
machine, which is a known contamination source and is untouched by a route registration, an HTML
asset and a test file.

## The other two ports

Both were reproduced in their own throwaway worktree cut from their own `origin/v3`, not inferred
from the nodejs finding. The main checkouts were left alone — python's carries another session's
`uv.lock` churn — so each port's branch lives in a worktree beside its fork.

**python** (`3072339`), branch `fix/swagger-ui-asset-asks-for-a-url-that-never-existed`. Its
canonical paths were never at risk: `core/server.py:1704` handles `("/swagger", "/swagger/")`
inline and renders its own UI pointing at `/swagger/openapi.json`. The exposure is the bundled
asset underneath, reached by `core/server.py:3227` index resolution (`/swagger//`) or by name
(`/swagger/index.html`). Measured on the unmodified published build, swagger on: those two answer
**200 with the dead page** while `/swagger` and `/swagger/` answer the real UI. Swagger off: all
five paths 404 — `core/server.py:3220` gates them, so there is no production exposure here, only a
UI that cannot work. Fix is therefore the one string in
`tina4_python/public/swagger/index.html`; no route needed.

**ruby** (`f67adc4`), same branch name. This is the one that was previously *read, not run*, and
running it closed the gap: real requests through `Tina4::RackApp` via `Rack::MockRequest` give
`/swagger` and `/swagger/` the real UI, and `/swagger//` and `/swagger/index.html` **200 with the
dead page** — with the app logging its own `404 Not Found: /swagger/swagger.json` behind it. Same
one-string fix in `lib/tina4/public/swagger/index.html`.

Neither port routes `swagger.json` anywhere, checked by grep in both — so the old URL named a path
that has never existed in any of the four ports.

### Their gates

Each port's regression test went into the file that already owns this surface, rather than a new
one — both were written for the *earlier* leak on these same assets and both stop at status codes,
which is exactly why neither noticed:

| port | file | on the fix | asset string reverted alone |
|---|---|---|---|
| python | `tests/test_swagger_static_gate.py` | 7 passed | **1 failed**, 6 passed |
| ruby | `spec/swagger_static_gate_spec.rb` | 7 examples, 0 failures | **1 failure**, 6 pass |

Full suites, each port compared against its own pristine `origin/v3` in the same worktree:

| port | base | + the fix | failing set |
|---|---|---|---|
| ruby | 5722 examples, 24 failures, 470 pending | 5723 examples, 24 failures, 470 pending | **identical** |
| python | 5244 passed, 5 failed, 664 skipped | 5245 passed, 5 failed, 664 skipped | **identical** |

The `+1` in each is the new test. Nothing introduced, nothing cleared — and nothing cleared is
again the expected answer, because no existing test in either port covers this.

Both python runs were made under `uv sync --extra test`. An earlier run of the same tree without
that extra reported **15** failures rather than 5: ten of those were missing test dependencies, not
code. That is why the pair was re-run under one env rather than compared across two, and why the
15 is not quoted anywhere as this tree's health.

Both assert the same property as nodejs: for every path that hands a browser a UI page
(`/swagger`, `/swagger/`, `/swagger//`, `/swagger/index.html`), the document URL read out of that
page must itself answer 200. Ruby's rescues the request, because braces are not legal in a URI and
an unsubstituted placeholder makes `Rack::MockRequest` raise — without that the failure is an
opaque parse error from inside Rack instead of a sentence naming the URL.

All swagger suites on the fixed trees: python 117 passed across six files plus `test_swagger_contract`
13 passed; ruby 103 examples, 0 failures across all eight.

python's contract suite needs `openapi_spec_validator`, which a plain `uv sync` does not install —
and I first wrote that up as a missing dependency. It is not. It is declared in the **`test`
extra** (`pyproject.toml:99`) with a comment saying it is TEST-ONLY for exactly that file and that
the generator "stays zero-dependency", and CI installs it with `uv sync --extra test`
(`.github/workflows/test.yml:266`). The right invocation is `uv sync --extra test`; my first pass
used `uv add --dev`, which duplicated an already-declared dependency, and that change was reverted
out of the branch.

## Residual gaps

- **Ruby is read, not run.** It ships the identical dead file and serves bundled swagger assets;
  that is an inference from its source, not a measurement.
- **The two document URLs are still hardcoded twice** — once in `SWAGGER_UI_HTML`, once in the
  bundled asset. Pre-existing, and the round-trip assertions on both paths now fail if they
  drift, but the duplication itself is untouched.
- **The bundled page's rendering is not verified**, only the URL it asks for. Its scripts load
  from cdnjs and were not changed; whether swagger-ui then draws is a browser question no curl
  answers.
- `/SWAGGER/` 404s (paths are case-sensitive, framework-wide) and `/swagger/openapi.json/` 404s.
  Both are honest 404s, so both are left alone.
- Linux only, node v22.22.2 only.

## A note on python's `uv.lock`

`uv run` / `uv sync --extra test` re-resolves the lock in place: it adds the test extra's
transitive dependencies and drops the dev-only `ruff`. That happened identically in both runs of
the base-vs-fix pair, so it does not bias the comparison, and it was reverted out of the branch
afterwards — the python commit is the asset string and the test, nothing else. Expect the file to
come back dirty after any run in that worktree, and revert it rather than committing it.

## 2026-09-09: rebased onto 3.13.135, and what upstream took off our plate

All five upstreams moved overnight to **3.13.135**. Every branch here was rebased and
re-proven against its new base; nothing was carried forward on trust.

| port | branch | head | base |
|---|---|---|---|
| nodejs | `fix/swagger-trailing-slash-serves-an-empty-ui` (renamed) | `3a847ea` | `8bbc53d` |
| python | `fix/swagger-ui-asset-asks-for-a-url-that-never-existed` | `df1146f` | `a380345` |
| ruby | same name | `d828bb2` | `7d244c3` |

**`f-sw-01` is upstream's now, and the nodejs branch lost a commit.** Andre landed `3368ef8`,
which is the same one-line change to the same line as our `041f3d0` — `if (!swaggerAssetsEnabled)`
becomes `if (!enabled)` — differing only in the comment. So the rebase dropped ours
(`git rebase --onto origin/v3 041f3d0`) and nodejs is a single commit. Two consequences worth
recording because neither is obvious:

- The dropped commit had **created** `test/swaggerGateAgrees.test.ts`, so replaying the commit
  that merely *grew* it produced a delete/modify conflict. Resolved by taking the file's final
  state whole. It now gates upstream's version of the guard fix rather than ours, and passes
  98/98 against it — which is a better outcome than gating our own code, since it is upstream's
  fix that has to keep working.
- Upstream `512cac3` moved **every** test file off `fileURLToPath(import.meta.url)` to
  `import.meta.dirname`, because vitest 4 installs a non-file URL base that makes the old form
  throw at module import and takes the whole file to 0 tests run. Our new test still used the
  old form, so it was migrated to match. It runs under tsx, not vitest, so it was not actually
  broken — but a file that reads as the house exception invites the next person to "fix" it.

### Re-proven at the new bases

Component gates, each revert alone:

| revert | result |
|---|---|
| nodejs, nothing reverted | 98 passed |
| nodejs, asset token only | 86 passed / **12 failed** |
| nodejs, `/swagger/` route only | 97 passed / **1 failed** |
| python, asset string only | **1 failed** / 6 passed — `asks for '{SWAGGER_ROUTE}/swagger.json', which answered 404` |
| ruby, asset string only | **1 failure** / 7 — `which is not even a fetchable URL` |

Full suites, each port against its own pristine `origin/v3` in the same tree. This round the
failure **identities** were captured and diffed, not just the counts — a count match is not a
set match, and the earlier rounds only had counts:

| port | base | fix | failure set |
|---|---|---|---|
| python | 5247 passed / 5 failed / 664 skipped | 5248 / 5 / 664 | identical, by name |
| ruby | 5729 examples / 25 failures / 470 pending | 5730 / 25 / 470 | identical, by rerun locator |
| nodejs | 8230 passed / 35 failed / 240 skipped, 354 files, 16 failed | 8328 / 35 / 240, 355 files, 16 failed | identical, by file name |

Every delta is exactly what the fix adds: +1 python test, +1 ruby example, +1 nodejs file
carrying +98 assertions. Python's five are the skill installer, a firebird connect timeout and
three port-takeover specs; ruby's 25 are cache/memcached/session-database/port-takeover/installer;
nodejs's 16 are queue, session, mongo, memcached, greenmail, port takeover and skill install. All
need services this machine does not run, none is swagger, and none of them moved.

One measurement was thrown away rather than reported: a first attempt ran python's and ruby's
suites concurrently, and python was killed at a 1800s cap. The re-runs were serial. A killed run
reports nothing useful, and `tail`'s exit code made the pipeline look successful.

### php is a fourth instance, and this readme had it wrong

The cross-port section above says php ships no such asset. That is **wrong** and is corrected
here rather than edited out. php ships `src/public/swagger/index.html`, whose line 81 asks for
`{{baseURL}}/swagger/json.json`. php's own `tests/SwaggerStaticGateTest.php` opens by stating
that the framework ships the Swagger UI as static files under `src/public/swagger/`, and asserts
both that they ship and that they serve. `{{baseURL}}` occurs **exactly once in the entire php
tree** — in that file — so nothing substitutes it and static serving hands it over byte-for-byte;
`/swagger/json.json` is a route in no port. php's real document route is `/swagger/openapi.json`
(`Tina4/Swagger.php:1142`), and its route-rendered page names that correctly at `:1466` — the
same split between a correct rendered page and a dead bundled asset as nodejs.

Same mechanism, different dead literal. **Read, not run** — not reproduced, no branch, no test —
so the ledger keeps php at `?` rather than `affected`.

### Also cleared by 3.13.135, without us

- `f-dev-01` landed in all four ports (py `3c68ef1`, php `d493952a`, rb `04cb590`, nd `6d7f629`).
  Ruby's upstream version is wider than ours, adding a `TINA4_VERSION_CHECK_URL` override.
  So **php#207 and ruby#45 are open, green, and superseded**, and python#127 / nodejs#62 no
  longer need refiling.
- `f-bld-01`: `npm run typecheck` exits 0 at `8bbc53d` (`16585cb`, `7eba290`).
- `f-pkg-01` and `f-dep-01` were the two judgement calls held for Andre, and he made both:
  the core-barrel ceiling is 79 (`d7194b0`), and `cryptography` is an allowed opt-in extra
  (`1dec834`).
