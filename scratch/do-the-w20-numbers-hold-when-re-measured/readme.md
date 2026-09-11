# Do the w-20 numbers hold when re-measured?

A verification pass over everything claimed for `w-20` on 2026-09-11 — the build on `scratch`, the
three suites, the component gating, the rows written into `ISSUES.md`, and the entries added to
`TESTLOG.md` and `FEATURES.md`. Asked because the claims were made across a long session and
several of them were written from memory rather than from a run.

Trees: `scratch` (`v0.2.0-297-gc3b61d9` + uncommitted), `baseline-main` (`main` `d719fc3`).

## What it found

**One defect, in our own build, introduced by the Test button and never on `main`.**

`POST /api/model/test` is `.noAuth()` — like every route in this app — and when the caller sent a
blank token it substituted the key already stored for that role, while taking the endpoint from the
caller. Those two together make the server post the user's API key to any host a caller names, with
no user action and nothing shown in the UI. Not argued — run:

```
  the sink received 1 request(s)
     /v1/models   Bearer sk-USERS-REAL-KEY-abcdef

  REPRODUCED — an unauthenticated caller made the server send the stored key to a host it chose
```

and the same probe on untouched `main`: `n/a — no /api/model/test on this tree`. Fixed in the same
build: the stored key is now only ever sent to the endpoint it was saved against; testing any other
endpoint requires typing the key. Gated by `attack.mjs` cell 15, which failed **14/15** before the
fix and passes after.

**Five claims were wrong and are corrected.**

| claim, as written | what re-measuring showed |
|---|---|
| `attack.mjs` scores **1/12** on `main` | **1/14** — cells 13-14 had been reasoned about, not run |
| build is **+245 −36** | **+246 −36** at the time, more after the fix |
| `saveAppSettings()` at `app.ts:498` on `main` | **`:492`** — the build's line number had been quoted as `main`'s |
| thinker triple assigned at `app.ts:1968-1971`, reconcile called at `:1989` | **`:1952-1954`** and **`:1968`** (and `:472` on every load) — same mistake |
| *"this machine has no outbound network"* | **false** — `mcp.tina4.com` 200, `openrouter.ai` 200, `api.deepseek.com` 401, `api.anthropic.com` 401 |

The last one was inherited, not invented here: it sits in the `run-20` row as the reason that fix's
streaming half was never checked against the real gateway. That obstacle does not exist. A dated
re-check is appended to the row; nobody has run the check yet.

**One claim in the code was false and is rewritten.** A comment said the Test button goes through
the server because "the provider sets no CORS headers for us". Measured: `openrouter.ai` returns
`access-control-allow-origin: *` and `api.deepseek.com` echoes the origin. The real reasons — the
key never entering a cross-origin request, and testing the same path the turn will take — are now
what the comment says.

**One negative had no stated scope.** `attack.mjs` cell 9 checked 10 GET routes and the entry read
"no GET returns the key". The app has 14. It now checks all 14.

## What re-measuring confirmed

| | |
|---|---|
| `gate.mjs` | **1/8** on `main`, **8/8** on the build — re-run, both trees |
| `gate-ui.mjs` | exits 1 on `main` with *"the thinker fields do not exist"*; **10/10** on the build |
| component gating | re-run against the **final** build, not the one the first table was measured on: nine pieces, each turning a suite red alone. The tenth had already been removed for staying green |
| `sec-04` line numbers | `app.ts:316`, callers `:528` and `:1993` on `main` — correct as filed |
| `sec-05` | correct, and **confirmed outside the probe**: the operator's own `~/.tina4-simple-agent/settings.json` is `0644`, holding `FREE-TOKEN` in both fields |
| ledger integrity | 56 rows, 56 distinct codes, no duplicates, all ten-column; the three new rows parse as rows |
| `PROGRESS.md` | untouched, correctly — nothing here has been delivered |

## The bound that could not be closed

**A coder chat has never been observed going out over a custom provider.** Two attempts, both
capped, both instrumented. The thinker's side is settled — 4 chats, all `Bearer <thinker key>`,
none carrying the coder's. The coder's side got only its `/models` probe. The frames say why:

```
     activity (writing your plan…)
     activity (planner busy — retrying (2/3)…)
     activity (planner busy — retrying (3/3)…)
     delta
     turn:done
```

The stand-in provider's plan JSON is not a shape the planner accepts, so planning failed and the
turn answered as chat without ever reaching the coder. That is a limit of the fake, not evidence
about the wiring — and it means the wiring claim for the coder rests on **reading**
(`app.ts:5706`, `:6464` route on `adapter === "cli"`; `custom` is `openai`, so it takes the same
native REST path as `tina4`, using `settings.endpoint`/`settings.token`, which cells 4 and 5 prove
hold the user's values). What would close it: a stand-in that emits a plan the planner accepts, or
one real build against a real provider.

## Files

| | |
|---|---|
| `can-anyone-make-the-server-post-the-key-elsewhere.mjs` | the exfiltration reproduction. Exit 0 = leak present, 1 = absent or route missing, 2 = nothing measured |
| `does-the-coder-really-call-it.mjs` | the unclosed bound. Prints the turn's frames so "the coder never ran" can be told apart from "the coder ran wrong" |
| `readme.md` | this |

Note on reading these: both print a verdict line and set an exit code, but when run through a pipe
the exit code you see belongs to the pipe, not the probe. Read the verdict line.
