# route-handler-receives-the-response-as-its-request

**Ledger row:** [`f-rt-01`](../../known-issues/ledger.md)
**Reproduced on:** tina4-nodejs **3.13.103** (the version in the upstream report) and
**3.13.114** (current release, 2026-08-24). Present in both.

## The issue

A tina4-nodejs file route whose handler's **first parameter is not literally named `req` or
`request`** does not receive the request. It receives the **response** object in that position,
silently. Nothing throws, nothing is logged, and the route still returns 200.

Inside such a handler `req.user`, `req.session` and `req.cookies` are all `undefined` — not
because the framework built an incomplete request, but because the handler was never given the
request at all.

This is the defect behind upstream issue
[tina4stack/tina4-nodejs#57](https://github.com/tina4stack/tina4-nodejs/issues/57), which reports
the symptom correctly and the mechanism wrongly ("Tina4 then supplies an incomplete request
object"). The request object is complete. The wrong object is handed over.

## The mechanism

`packages/core/src/server.ts:1002` — `invokeRouteHandler` resolves the handler's arguments by
**parsing parameter names out of the function's own source text**:

```js
const fnStr = match.handler.toString();
const argMatch = fnStr.match(/^(?:async\s*)?(?:function\s*\w*)?\s*\(([^)]*)\)/);
const argNames = argMatch?.[1]?.split(",").map((a) => a.trim().replace(/[:=].*/, "")) ?? [];
const filteredArgs = argNames.filter((n) => n.length > 0);

if (filteredArgs.length === 0) return await match.handler();

const args = filteredArgs.map((name) => {
  if (name in routeParams) return routeParams[name];
  if (name === "request" || name === "req") return req;
  return res;                                   // <-- everything else becomes the RESPONSE
});
```

The final `return res` is the bug. It is a default, not a fallback: any parameter the resolver
cannot positively identify as the request becomes the response, **including the first one**. There
is no positional rule and no arity check, so a two-parameter handler can end up with the response
in both positions.

Three ways an ordinary handler lands there:

| handler | why it breaks |
|---|---|
| `(ctx, res) => …` | `ctx` is not `req`/`request`, so it falls to `return res` |
| `(e, t) => …` | any build step that mangles parameter names — the names are read from `toString()`, so a minified or bundled handler has no recoverable names |
| `({ req, res }) => …` | `[^)]*` captures `{ req, res }`; splitting on `,` yields `{ req` and `res }`, neither of which matches, and both become the response |

The last case is worse than the others: `"{ req" in routeParams` is false and the name test fails,
so **both** destructured names resolve to the response and the handler's `req`/`res` are both
`undefined`.

The documented signature (`(req, res)` / `(request, response)`) works, which is why this survives
every example in the docs and every scaffolded route.

## Before / after

Stage 1 — stock framework, nothing patched. `prove.sh` extracts the released `invokeRouteHandler`
bytes straight out of the installed package and calls them with a sentinel request and response:

```
tina4-nodejs 3.13.103

extracted dist lines 35141..35154 from ./node_modules/tina4-nodejs/packages/core/dist/index.js

PASS  (req, res)                 canonical  ->  arg0=REQUEST  arg1=RESPONSE
PASS  (request, response)        canonical  ->  arg0=REQUEST  arg1=RESPONSE
FAIL  (ctx, res)                 renamed    ->  arg0=RESPONSE  arg1=RESPONSE
FAIL  (e, t)                     minified   ->  arg0=RESPONSE  arg1=RESPONSE
FAIL  ({ req, res })             destructured  ->  arg0=undefined  arg1=undefined
```

Identical output on 3.13.114.

Stage 3 (fix proven to close it) is **not done** — no candidate fix has been written yet.

## Why it runs the released bytes rather than a server

The artefact under test is a pure function of the handler's source text and the two objects passed
in. Extracting it from `packages/core/dist/index.js` and calling it runs exactly what ships, with
no server, no port, no database and no patched workspace — so the reproduction cannot be
contaminated by the thing `scratch/readme.md` warns about. The extraction is by search, not by
line number, so it survives a rebuild.

## Cross-port state

`known-issues/readme.md` requires every port to be checked. Only Node has been **executed**. The
other three were read, not run, and the ledger row records them as `?` for that reason:

| port | source | what the source does |
|---|---|---|
| nodejs | `packages/core/src/server.ts:1002` | name-keyed, else response. **Executed — affected.** |
| ruby | `lib/tina4/dispatch_pipeline.rb:692` | name-keyed on `:request`/`:req`, `else resp`. Same shape. Read only. |
| php | `Tina4/Router.php:1562` | name **or type hint** (`Request::class`), plus a two-param positional fallback that corrects an unclaimed first param. Looks immune to the reported case. Read only. |
| python | `tina4_python/core/server.py:2034` | **positional** — `len(_remaining) >= 2` appends request then response, names ignored. Looks immune. Read only. |

Running the other three is open work.

## Run it

```bash
./prove.sh                              # defaults to tina4-nodejs 3.13.103
TINA4_NODEJS_VERSION=3.13.114 ./prove.sh
```

`node_modules/` is gitignored; the script installs the pinned version on first run.
