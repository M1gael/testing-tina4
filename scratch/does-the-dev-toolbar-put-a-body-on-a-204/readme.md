# Does the dev toolbar put a body on a 204?

**Yes — and it is wider than the report says.** With `TINA4_DEBUG=true`, `_stage_dev_toolbar_inject`
appends ~1 KB of toolbar markup to **every** `204 No Content` response, and `build_headers`
then declares a matching `Content-Length`. Under uvicorn that is a hard protocol error that
kills the connection; under `tina4 serve` the bytes go on the wire and a conforming client
silently discards them.

Investigated against **tina4stack/tina4-python `origin/v3` @ `198e09b`** (version `3.13.136`),
2026-09-18, to review **[PR #132](https://github.com/tina4stack/tina4-python/pull/132)** from
@Hartslief.

## The question

*Is the defect PR #132 describes real on stock v3, does the patch close it, and does it close
all of it?*

Answers that would have ended it differently: a 204 whose `content_type` is not `text/html`
(the guard would never be reached), or an ASGI layer that drops the body for a 204 (nothing
would reach the wire).

## The mechanism, to file:line

1. `Response.__init__` (`tina4_python/core/response.py:112`) sets
   `content_type = "text/html; charset=utf-8"` **unconditionally**.
2. `response(None, 204)` — what `tina4 make crud` scaffolds for every delete handler
   (`tina4_python/cli/__init__.py:1851`) — takes the `data is None` branch
   (`response.py:170`), which sets `content = b""` and **leaves the content type alone**. The
   204 is therefore an HTML response as far as anything downstream can tell.
3. `_stage_dev_toolbar_inject` (`tina4_python/core/server.py:2591`) gates on `ctx.is_dev` and
   on `"text/html" in content_type`. **There is no status check.** The empty body has no
   `</body>`, so it takes the `body + toolbar` append branch (`server.py:2606`).
4. `Response.build_headers` (`response.py:499-502`) always emits
   `content-length: len(self.content)` — now ~1037 instead of 0.

The sibling stage `_stage_head_strip` (`server.py:2705`) already enforces the matching rule for
HEAD, and the `_RESPONSE_STAGES` comment (`server.py:2744-2752`) explains its ordering. 204 was
simply never given the same treatment.

## What was run

`./prove.sh`, against two detached worktrees of `origin/v3 @ 198e09b`:
`~/.cache/tina4-worktrees/pr132-stock` (untouched) and `…/pr132-fixed` (`pr132.patch` applied,
`git apply` exit 0). `drive.py` drives the **real ASGI app** and reads the
`http.response.start` / `http.response.body` messages — the same instrument
`tests/test_head_no_body_conformance.py` uses, for the same reason.

| case | stock | with PR #132 |
|---|---|---|
| `DELETE /item/1` → `response(None, 204)` | 204, **1037 bytes**, `CL=1037` | 204, 0 bytes, `CL=0` |
| `OPTIONS /item/1` → 204 + `Allow` | 204, **1032 bytes**, `CL=1032` | 204, 0 bytes, `CL=0` |
| `GET /page` (ordinary HTML 200) | 200, 1068 bytes, toolbar present | **unchanged** — 1068, toolbar present |
| `GET /weird` — handler returns 204 *with* a body | 204, 1071 bytes | 204, **39 bytes** (the handler's own) |
| `HEAD /page` | 200, 0 bytes | 200, 0 bytes |

Both directions: remove the toolbar stage's reach and the 204 goes empty; leave it and the 200
still gets its toolbar. The 200 row is the negative control — a fix that killed the toolbar
outright would look identical on the 204 rows alone.

### On a real socket

**uvicorn (`h11`), keep-alive, DELETE then GET on one connection** (`wire.py`):

```
stock:  h11._util.LocalProtocolError: Too much data for declared Content-Length
        total bytes: 167   responses seen: 1      <- the GET is never answered
fixed:  total bytes: 1436  responses seen: 2
```

The 204 headers reach the client, the body raises inside `send`, and the connection is torn
down. Any request already pipelined behind it is lost. **This is the "DELETE fails" in the
report** — and it also takes the *next* request with it.

**tina4's own HTTP/1.1 bridge (`tina4 serve`)** (`wire_builtin.py`):

```
stock:  raw bytes: 1150  b'HTTP/1.1 204 No Content\r\n...content-length: 1037\r\n\r\n<link rel="stylesheet" href="/__dev/t'
        http.client: status=204 read=0 bytes  (no exception)
fixed:  raw bytes: 110   content-length: 0
```

The bridge (`server.py:4005-4066`) writes the body verbatim, then **closes the connection after
every response** — it has no keep-alive — so there is no response smearing here and a conforming
client (RFC 9112 §6.3: a 204 has no body regardless of `Content-Length`) reports a clean 204 and
throws the 1037 bytes away. Wasteful and wrong on the wire, but not fatal.

**So the severity depends on the server**, and that is worth knowing before anyone calls this
cosmetic.

## Attacks on the answer

- **Is `== 204` a complete guard for this stage?** For the statuses this framework can actually
  produce, yes. 304 is decided *after* `handle()` returns, in `app()` (`server.py:3126-3141`),
  and sends its own empty body — injected bytes never reach the wire. 205 is not in
  `_HTTP_REASON_PHRASES` and is emitted nowhere. 1xx is not produced. *(read)*
- **Is CORS preflight hit too?** No. `_stage_cors_preflight` is a **pre-match** stage and
  `handle()` returns a pre-match answer *as is*, skipping `_RESPONSE_STAGES` entirely
  (`server.py:2800-2805`). `OPTIONS`-on-a-known-path is a **fallback** stage and does fall
  through, which is why it is affected. *(run — the table above)*
- **Does the patch break anything else?** `test_dispatch_pipeline.py`,
  `test_dispatch_characterisation.py`, `test_head_no_body_conformance.py`, `test_dev_admin.py`,
  `test_dev_admin_conformance.py`: **117 passed** on the patched tree. *(run)*
- **Could the failure have been something other than the toolbar?** The other HTML injector,
  `inject_feedback_widget` (`server.py:3090-3100`), also has no status check — but it requires
  `response.content` to be non-empty and a whitelisted user, so on a stock `response(None, 204)`
  it is a no-op until the toolbar has already filled the body. *(read)*

## Where the answer stops

- **The patch does not make a 204 bodiless — it makes the toolbar stop adding to one.** A
  handler that returns `response("<b>x</b>", 204)` still ships 39 bytes on a 204 after the fix
  (`GET /weird` above). `_stage_head_strip` strips HEAD *unconditionally*, "even for an explicit
  `Router.head()` handler that accidentally returned one". A `_stage_no_content_strip` placed
  last, next to its HEAD sibling, would hold that same line and cover every future injector;
  a guard inside one stage covers one stage. **Not a defect in the PR — a narrower fix than the
  file's own precedent.** *(run + read)*
- **PR #132 ships no test.** The repo already has the shape for it —
  `tests/test_head_no_body_conformance.py`, one case per path, driven through the real ASGI app.
  Those same 117 tests pass on the **stock** tree too, so no existing test detects the defect and
  nothing would catch its return. *(run, both trees)*
- **The suite never ran on the PR.** Its only check is `security/snyk`; `.github/workflows/test.yml`
  triggers on `pull_request: [v3]` and the run exists — `Tests` and `Docker image` both sit at
  `conclusion=action_required` on head `0e7ce30`, i.e. queued behind a maintainer's approval of a
  fork contribution. Nobody has seen this patch go green.
  *(run — `gh api repos/tina4stack/tina4-python/actions/runs?head_sha=…`)*
- **Two trailing-whitespace characters** in the added lines (`git apply` warns). `[tool.ruff]`
  in `pyproject.toml` sets only `target-version` and `line-length`, so ruff's defaults (E4/E7/E9/F)
  do not include `W291` and CI will not catch or care. Cosmetic. *(read)*
- **Axes not visited:** a real browser's `fetch()` against either server; HTTP/2; a reverse proxy
  in front (nginx/Caddy may reject or strip the body itself); `granian`/`hypercorn` rather than
  uvicorn; and a 204 that has been gzip-compressed (`build_headers` only compresses above 1024
  bytes, which the toolbar pushes it past — untested).
- **Other ports — read, not run.** The same injector with the same missing status check exists in
  php (`Tina4/Router.php:2246` `injectDevToolbar`: dev + path + `text/html`, no status) and ruby
  (`lib/tina4/dispatch_pipeline.rb:499` `dev_toolbar_inject`: same three gates). nodejs gates on
  `isInjectableHtml` (`packages/core/src/server.ts:1260`) = html + no content-encoding, also no
  status — though it then *drops* `content-length`, so its failure mode differs. **Whether any of
  the three actually produces a `text/html` 204 is unverified**; that is the reproduction each
  needs before the row can claim them.

## Verdict on PR #132

The defect is real, the mechanism in the PR body is correct, the patch closes it in both
directions with the 200 path untouched, and it applies clean to `198e09b`. It is a **correct,
under-tested fix that is narrower than the file's own precedent**, on a change whose test suite
has not been allowed to run.
