# tina4-nodejs 3.13.134 serves a Swagger UI whose document 404s

**Framework tina4-nodejs 3.13.134 (published on npm), node v22.22.2. First run 2026-09-07,
re-verified 2026-09-08 in a throwaway worktree.** The Rust CLI used to scaffold the python
control app is 3.8.83.

> Renamed 2026-09-08. This directory used to be called
> `web-push-release-breaks-swagger-and-typecheck`, which named the wrong commit — see
> *Where it came from*. The release breaks these things; the web push feature does not.

## The issue

With swagger switched on, the server advertises Swagger at startup, serves the Swagger UI page,
and then answers **404** for the document that page needs.

```
GET /api/items            -> 200
GET /swagger              -> 200
GET /swagger/openapi.json -> 404
```

The startup banner still prints `Swagger:   http://localhost:7311/swagger`, so nothing in the
output suggests anything is wrong. The page loads and stays empty.

The `/swagger` page that does serve is not the framework's own UI — it is the static file
`packages/core/public/swagger/index.html`, picked up by static serving as a fallback, and it asks
for `{SWAGGER_ROUTE}/swagger.json`, an **unsubstituted template placeholder**. That path 404s
too, as do `/swagger.json` and `/openapi.json`. There is no path on the server that returns the
document.

## The mechanism

`packages/core/src/server.ts:2600-2601`, in `configureSwagger`:

```ts
enabled = swagger.swaggerEnabled();
if (!swaggerAssetsEnabled) {          // <- reads the module-level variable
  throw new Error("__swagger_disabled__");
}
```

`swaggerAssetsEnabled` is the module-level flag at `server.ts:69`, and the only thing that ever
assigns it is `server.ts:2154`:

```ts
swaggerAssetsEnabled = await configureSwagger(router, ormDir, modelsDir);
```

That is `configureSwagger`'s **own return value**. While the function is running the flag is
still its initial `false`, so the guard always fires, the `throw` skips the rest of the block, and
`router.addRoute` is never reached for either swagger route. The outer `catch {}` swallows the
throw, and the function then returns `enabled` — **true**. So it reports swagger as enabled
having registered nothing, which is exactly why the banner and the 404 disagree.

`configureSwagger` has a **single** `return enabled` (`server.ts:2646`) reached by both the throw
path and the success path, so the value handed to the module-level flag is the same before and
after the fix. That is what makes the fix provably unable to affect static-asset gating.

The framework holds two copies of this flag and only one of them was broken. The context copy at
`server.ts:1668-1671` is assigned before use and is correct, which is why static serving still
exposes the bundled `/swagger` asset when swagger is on, and correctly withholds it when off.

### One instance, not a pattern

Checked, so the fix does not need to be broader: `server.ts` has six module-level mutable
bindings, and only two are assigned from a function call at all. `_serverHandle = await
startServer(config)` (`:944`) is the other, and `startServer`'s body never reads it — the four
reads are the return on the next line and `stop()`. The shape is unique to swagger in this file.

### Where it came from

`adeb149` *"refactor(metrics): split core docs and startup"* — **not** the web push feature.
Before it (`14a67e9`) the same block read:

```ts
swaggerAssetsEnabled = swagger.swaggerEnabled();
if (!swaggerAssetsEnabled) {
```

assign then test, on the same variable. The refactor extracted `configureSwagger` into its own
function with a local `enabled` as the return value, redirected the assignment to it, and left
the guard reading the old module-level name.

## Proving it

Two independent reproductions, both from outside any working checkout:

1. A clean `npm install tina4-nodejs@3.13.134` in `app/` — no repo, no source tree.
2. `probe/probe.ts`, run against a throwaway `git worktree` detached at `origin/v3` `fe3b87d`
   with its `node_modules` hardlinked in. `node_modules/@tina4/*` are **relative** symlinks
   (`../../packages/core`), so they resolve inside the worktree and the sandbox cannot silently
   execute the main checkout's code — checked with `readlink -f` before trusting a single number.

The probe reports the whole reachable surface, and in particular it takes the document URL **out
of the HTML that was actually served** and then fetches that exact URL. Asserting a hardcoded
`/swagger/openapi.json` would have passed while the browser was still being handed a page
pointing at a placeholder.

`TINA4_SWAGGER_ENABLED=true`, same sandbox, one line different:

| | base `fe3b87d` | base + the one-line fix |
|---|---|---|
| banner advertises `/swagger` | true | true |
| `GET /swagger` | 200 | 200 |
| …and the page it serves asks for | `{SWAGGER_ROUTE}/swagger.json` | `/swagger/openapi.json` |
| …and that URL answers | **404** | **200** |
| `GET /swagger/openapi.json` | **404** | 200 |
| `GET /swagger/` | 200, placeholder page | **200, placeholder page — unchanged** |

`TINA4_SWAGGER_ENABLED=false` is identical on both trees: banner silent, `/swagger` 404,
`/swagger/openapi.json` 404. The switch still closes the gate.

The earlier `npm install` run patched the guard inside `node_modules` to answer the same
question; that copy was restored the same afternoon and re-checked on 2026-09-08 — the installed
`packages/core/dist/index.js`, `packages/cli/dist/bin.js`, `packages/orm/dist/index.js` and
`packages/core/src/server.ts` all still read `if (!swaggerAssetsEnabled)`. Every number above
names the tree it came from.

`python` is **not affected**: the same scaffold on published tina4-python 3.13.134 answers 200
for `/swagger/openapi.json`. php and ruby register or serve the UI behind a direct call to the
gate at the point of use — `Tina4\Swagger::register()` returns early on `!self::isEnabled()`
(`Tina4/Swagger.php:1138`), and ruby's `serve_swagger_ui` returns 404 unless
`Tina4::Swagger.enabled?` (`lib/tina4/rack_app.rb:361`) — with no second module-level flag to
read too early, so the shape cannot occur. **Read, not run.**

## The fix

`gitdir/tinaforks/tina4-nodejs`, branch `fix/swagger-routes-never-register`, cut from
`origin/v3` @ `fe3b87d`. Uncommitted.

One line: the guard tests the value just read (`enabled`) instead of the module-level flag. The
`throw`/`catch` control flow, the local, and the return are all left as they were.

### The regression test

`test/swaggerGateAgrees.test.ts` — a property, not an example, over two axes.

**Axis 1, the gate's vocabulary.** `swaggerEnabled()` (`packages/swagger/src/ui.ts:47`) trims,
lowercases and accepts exactly `["true","1","yes","on"]`, falling back to `TINA4_DEBUG` when the
switch is unset. All four accepted spellings are tested, plus a padded one to pin the `.trim()`;
the rejected side tests `false`, a non-member word, garbage, `false` beating `TINA4_DEBUG=true`,
and **both variables unset — the production default, which nothing in the suite covered.**

**Axis 2, the surface.** Per input: the banner, `GET /swagger`, and the document URL read out of
the served page and then fetched.

12 boots, 36 assertions, ~10s.

- On the fix: **36 passed**.
- With only the guard reverted and nothing else changed: **30 passed, 6 failed** — the six failures
  are the six enabled forms' round-trip assertion, each naming what went wrong:
  `page asked for "{SWAGGER_ROUTE}/swagger.json", which answered 404`.

The two assertions that stay green in the broken state are worth keeping precisely because they
do: the banner still advertises, and `GET /swagger` still answers 200. A suite that checked only
status codes could not see this defect at all — which is how it shipped.

Discovery was checked rather than assumed: `test/run-all.ts:86-92` picks up every `test/*.test.ts`
and runs the ones that do not import from `vitest` under tsx, so this file gates in CI.

**It also pins a second hazard shut.** The banner does not call `swaggerEnabled()` — it calls
`swaggerAdvertised()` (`server.ts:139`), a private re-implementation of the same vocabulary,
which the code comments themselves ask you to "keep in sync". Nothing tested that they agreed;
`bannerSurfaceLines.test.ts` takes booleans, so it cannot. Asserting banner and routes in the
same run makes any divergence in those two lists a failure, for all 12 inputs.

## Not fixed here, deliberately

Three findings that came out of attacking the fix. None is reproduced as a live failure on a
correct build, so none belongs in a one-line fix; each needs its own stage 1.

**1. `GET /swagger/` (trailing slash) — the fix does not fix it.** Measured on both trees:
base answers 200 with the placeholder page, and base **plus the fix** answers 200 with the
placeholder page. Reading `router.ts:342-360` — which retries a non-matching trailing-slash path
without the slash — suggested the registered route would claim it. It does not; running settled
what reading got wrong. So a user who types the trailing slash still gets an empty Swagger UI.

It is a separate defect with a separate mechanism, which is why it is not bolted onto this fix:
the route pattern is `/swagger` (`packages/swagger/src/ui.ts:62`) and does not match `/swagger/`,
so static serving resolves the directory to `index.html` and hands over the dead bundled asset.
Not a regression of ours — the base does the same — and not intended behaviour either:
unmodified published **tina4-python answers `/swagger` and `/swagger/` identically**, both the
real UI pointing at `/swagger/openapi.json`. Upstream's contract test is blind to it, requiring
only a **200** at `/swagger/` (`swaggerContract.test.ts:389`), which the placeholder satisfies.
Recorded as `f-sw-02`; the three candidate fixes (register both forms, substitute the token,
stop shipping the asset) are design decisions, not a patch.

**2. The bundled `public/swagger/index.html` is dead by construction** (the mechanism behind 1)**.** Its
`url: "{SWAGGER_ROUTE}/swagger.json"` is the **only** occurrence of `SWAGGER_ROUTE` in the whole
repo and in the published package: nothing ever substitutes it. The same file ships with the same
unsubstituted token in **tina4-python and tina4-ruby**, neither of which substitutes it either.
It is harmless only while the gated route shadows it — which is to say, it was harmless until
this defect stopped the route from being registered.

**3. `configureSwagger`'s outer `catch {}` swallows every error, not just the
`__swagger_disabled__` control-flow throw.** If `router.addRoute` or the swagger import failed,
the function would again return `true` having registered nothing — the same "reports enabled,
serves nothing" class, reached another way. Never reproduced.

## Effect on the rest of the suite

Whole suite, twice, in the sandbox worktree — pristine `fe3b87d`, then the same tree with the
one line changed and the new test added:

| | base `fe3b87d` | + the fix |
|---|---|---|
| assertions | 7945 passed, 66 failed, 240 skipped | 8260 passed, 41 failed, 240 skipped |
| files | 353 (34 listed failed) | 354 (18 listed failed) |
| vitest batch | 1 failed, 11 passed | **12 passed** |

**Nothing fails on the fixed tree that does not already fail on the base tree.** That direction
is the one that matters and it is clean.

The other direction needs care, and two of its entries do not belong to the fix:

- **`test/swaggerContract.test.ts` — the fix.** Gated directly, with the guard as the only
  variable on one warm tree: reverted it reports `1 failed (13 skipped)` (its `beforeAll` dies at
  `swaggerContract.test.ts:210`), restored it reports **13 passed**. It is also why base's vitest
  batch was red at all — and why `run-all.ts` then listed all 12 vitest files as failed, including
  `swaggerParity31396` and `swaggerPathParams`, which were never actually failing.
- **`integration` — the fix.** Its base failure is the assertion
  `FAIL GET /swagger/openapi.json returns spec`, which took the suite down before it could report.
  38 passed with the fix.
- **`cli.test`, `cliGenerateCoemits.test`, `exportsMap.test` — NOT the fix.** These failed on the
  base run for `Cannot find module .../packages/core/dist/index.js` and
  `./types/core/src/index.d.ts missing -- run npm run build:types`. `cliBuild.test` builds `dist/`
  and `types/` as a side effect partway through a run, so the base run started cold and left the
  tree warm for the second run. Same-tree comparison, different starting conditions: these three
  are an artefact of that, not of the one line. Said plainly rather than counted as a win.

So the honest reading of 34 → 18 is: 12 of it is one vitest failure being mislabelled as twelve,
3 of it is a warm `dist/`, and 2 files — `swaggerContract` and `integration` — are the fix.

## Residual gaps

- php and ruby immunity is established by **reading the guard**, not by running their suites.
- Linux only, node v22.22.2 only.
- Cluster mode is not exercised: the test boots a single process. `configureSwagger` runs per
  process and the flag is per module instance, so the fix is not expected to differ there —
  **expected, not measured.**
- The sandbox worktree has no built `packages/*/dist`, so suites that import the built output
  fail there for an environmental reason. That noise is identical in both runs and the
  comparison below is a diff of failure sets, never an absolute count.
