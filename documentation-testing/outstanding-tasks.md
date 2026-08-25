# Outstanding Tasks

Running backlog of work asked-for-but-not-yet-done. Mutable. When an item lands,
move it to the relevant record (`../known-issues/ledger.md` / `coverage-ledger/`) and delete the row
here. Confirmed issues live in `../known-issues/ledger.md`; chapter progress lives in `coverage-ledger/`. THIS file holds the
to-do list across sessions so nothing the user asked for gets dropped.

**Audit verdicts, version-bump records, and fix re-verification results do NOT belong here — they go to `audit-log.md`. This file holds only the resulting OPEN todo items.**

Status legend: `TODO` not started · `WIP` in progress · `BLOCKED` waiting on something.

---

## Framework fixes and doc alignment — from the 2026-08-19 pass

| # | Item | Status | Notes |
|---|---|---|---|
| R1 | **Decide chapter 27's direction (`PY-DOC-06`)** | BLOCKED | Two ways out and they are opposites. (a) Rewrite the chapter onto the API the runner has — `register(name, instance.run)` or a `Service` subclass with `register_service`. (b) Make `register()` honour the chapter: adapt any object with `run()`, call `stop()` on shutdown. (b) makes every existing example work as written and replaces `fix/service-runner-rejects-non-callable`; (a) is smaller but rewrites the chapter's whole teaching model. User's call. |
| R2 | **Verify the php / ruby / nodejs `tina4 ai` pages** | TODO | Their "Supported AI Tools" tables claim eight tools with a Google Antigravity row, and the `.cursorules` filename — both wrong for Python (`PY-DOC-05`, `CLI-FW-10`). Whether they are wrong for `Tina4\Ai`, `Tina4::AI` and `@tina4/core` is unverified: those repos are not cloned in `gitdir/`. Clone, check `AI_TOOLS`-equivalent, then either extend `docs/ai-installer-behaviour` or open per-language rows. |
| R3 | **Reconcile `docs/python-consistency-fixes` in both doc repos** | TODO | Local is 1 ahead of a base 19 / 73 commits stale; the fork's copy of the same branch was force-updated to a different hash (`82aaffe` / `799dbef` vs local `5ebe35b` / `6f176d9`). Compare the two versions before rebasing either — do not force anything blind. |
| R4 | **Fork `tina4stack/tina4-python`, push, open PRs** | BLOCKED | Four fix branches (`fix/cached-decorator-inert`, `fix/service-runner-rejects-non-callable`, `fix/websocket-decorator-shadowed`, `fix/ai-installer-context-defects`) plus `docs/ai-installer-behaviour` in each doc repo. Waits on user approval. (**`gh` is authenticated as of 2026-08-24** — `gh auth status` reports `MichaelC8E` with `gist, read:org, repo`; this row previously said it was not.) PR granularity (four PRs or one) also undecided. Note `origin` points at `tina4stack`, not a fork: add a `fork` remote before pushing. |
| R5 | **Pull `tina4-js` (7 behind) and `tina4-dev-admin` (1 behind)** | TODO | Not touched this pass. Fast-forward when either is next worked on. |

---

## Coverage-gap closure — from the 2026-06-30 fidelity audit

Fidelity was SOLID (zero our-side bugs); these are *coverage* gaps — missing tests, not framework defects. **Full enumeration lives in each chapter's ledger Open items** (single source): [`py-ch06-orm.md`](coverage-ledger/py-ch06-orm.md), [`py-ch18-testing.md`](coverage-ledger/py-ch18-testing.md).

**Ch12 gaps ALL CLOSED 2026-07-02 · 3.13.48 · CLI 3.8.53** — AUD-12-1/2/3/L, all verified FAITHFUL, no new findings (see the [py-ch12 ledger](coverage-ledger/py-ch12-queues.md) closed block). Remaining: Ch18 + Ch06.

**UNBLOCKED** — Docker recovered; `tina4_pg` up (healthy). The 3 queue brokers stay down (not needed for the remaining gaps).

Recommended closure order:
1. **AUD-18-1 (HIGH)** — `tests/test_auth_flow.py` is entirely missing (6-test capstone) + needs a `/api/auth/register` route. ~half the Ch18 exercise uncovered.
2. **Option/edge gaps (MED)** — AUD-06-1..6 (TextField/BlobField, validator=, field_mapping via select()/to_dict(), FK default related_name, include= on where()/select(), declarative has_one), AUD-18-2/3 (`resp.headers`/`content_type`/`text()`/`json()` only in a dormant probe).
3. **LOW batches** — AUD-06-L / AUD-18-L (boundary bounds, weak asserts, default-derivations). AUD-07 is NON-ACTIONABLE (recorded — testing it would violate strict-traceability).

---

## Chapter 7 — QueryBuilder

| # | Item | Status | Notes |
|---|---|---|---|
| Q3 | **S3–S11 + NoSQL/Gotchas/Exercise** — not started | TODO | S3 Filtering, S4 Joins, S5 Aggregation, S6 Sorting, S7 Pagination, S8 `to_sql()`, S9 Execution, S10 Chaining, S11 ORM Models, NoSQL `to_mongo()` (broker-dependent), Gotchas, Exercise. Capped at ≤2 sections/turn per USER directive — await direction on the next 2. S1+S2 done (ledger). |

---

## Chapter 12 — Queues

| # | Item | Status | Notes |
|---|---|---|---|
| D1 | `Queue(visibility_timeout=)` constructor param — reservation reclaim of unacked jobs; **may contradict S6:240**. Candidate real finding | TODO | undocumented in Ch12; lower priority (not average-user) |
| D2 | `max_retries=` overrides on `dead_letters()`/`purge()`/`retry_failed()`; `produce(delay_until=)`; `job.to_hash()/to_array()` aliases | TODO | edge API surface; lower priority |

---

## Codex skill delivery — from the 2026-08-04 mechanism study

**The fixture and both write-ups were removed on 2026-08-19** — `codex/` (the scaffolded
fixture plus `CODEX-CONTEXT-RESEARCH.md`) and `agent-testing/codex-skill-delivery/README.md`.
Recover them from git history if the mechanism detail is needed again. The findings survive as
ledger rows `CLI-FW-05`…`CLI-FW-11` (CODX-01..07 in order), and the seven-tool delivery
scorecard is preserved in the `CLI-FW-06` note. Everything below was measured on
tina4 CLI 3.8.64 · tina4-python 3.13.94 · codex-cli 0.145.0.

**X1 has moved on since this was written.** CODX-01/03/04/06 are fixed on a local branch in
`gitdir/tinaforks/tina4-python` (`fix/ai-installer-context-defects`, with regression tests), along with a
finding this list never had — `CLI-FW-12`, the Claude Code guide read from a checkout-only path
so pip-installed users got a 2 KB stub instead of the 82 KB guide. Nothing is pushed and no PR
is open, so the filing task stands.

| # | Item | Status | Notes |
|---|---|---|---|
| X1 | **File CODX-02..07 upstream** (`tina4stack/tina4-python`) | TODO | Two substantive: **CODX-02** skills installed only to `.claude/skills/`, so Codex (scans `.agents/skills/`) receives 0 of 158 KB; **CODX-06** `.cursorules` is a one-`r` typo, so Cursor receives nothing at all (3 sites: `ai/__init__.py:22`, `:254`, `CLAUDE.md:1451`). Then CODX-03/04 (non-TTY `EOFError`, dropped `--all`/`--force`), CODX-05 (empty `.cursor/`), CODX-07 (Aider needs `--read`). Follow `readme.md` → *Upstream filing*. Per auto-memory, **no `owner/repo#NNN` refs in commit messages** from this account. |
| X1b | Verify the 5 untested tools in the scorecard | TODO | Only **Claude Code** (works) and **Codex** (half) are measured. Copilot / Cline / Windsurf have plausible-looking paths but were never checked against a running tool; Cursor and Aider are already known-broken by inspection. Each needs the same treatment Codex got — install, then confirm from the tool's side that the file is actually in context. |
| X2 | Re-verify **CODX-01** is fixed before filing again | TODO | Doubled-brace `response({{...}})` was already reported; confirmed still present in 3.13.94. Check whether an upstream issue exists before opening a duplicate. |
| X3 | Run the `nosk`/`sk` arms now that delivery is measurable | TODO | Delivery itself is settled without a model (CODX-02). The arms now answer a *different*, still-open question: does a model **act** on `AGENTS.md`'s pointer block, and does registered-skill delivery change the architecture it produces? Use `codex debug prompt-input` to pin each arm's context before the run. |
| X4 | Keep `AGENTS.md` off the harness repo root | MOOT (2026-08-19) | Codex merges `<git-root>/AGENTS.md` into every session under it. `codex/` sits inside `testing-tina4`, so a root `AGENTS.md` would silently prepend to every arm and contaminate any comparison. **Moot since 2026-08-19** — `codex/` was deleted, so no arm sits under this repo any more. Reinstate the rule before any Codex fixture returns here. |
| X5 | Probe **channel 3 — MCP** end to end | TODO | tina4-python ships an HTTP/SSE MCP server (`tina4_python/mcp/`, gated on `TINA4_MCP`/`TINA4_DEBUG`, port framework+2000 = 9145). `codex mcp add <name> --url <URL>` consumes streamable HTTP. Untested: whether Codex's client negotiates tina4's protocol version and whether the loopback/token gate admits it. **Not** a substitute for the skills fix — it carries executable tools, not conventions. Security note: the built-in dev tools are DB query/execute + file read/write, so never register against a non-loopback URL without a token. |
| X6 | Evaluate a **Codex/Claude/Cursor plugin bundle** as the real distribution channel | TODO | Codex's plugin loader accepts `.codex-plugin/`, `.claude-plugin/` *and* `.cursor-plugin/` manifests, and a plugin can carry `skills/` + `.mcp.json` + `hooks.json` together. One versioned, installable-by-name bundle would replace per-project file writes for all three tools at once — strictly better than fixing `tina4 ai`'s paths tool by tool. Scope this before investing further in the file-copy approach. |

---

## Agent-behaviour investigation — 2026-08-24

Reporter-raised: a Codex session on a tina4-nodejs app kept announcing work and doing little or
none of it. Three ledger rows came out of it — `f-ai-06` (the developer skill's gate inventory and
worker-delegation contract), `f-ai-07` (the `.agents`/`.cursor` copies of the developer skill have
drifted from `.claude` and teach APIs that do not exist) and `f-rt-01` (handler arguments bound by
parsed parameter name) — plus a dated correction on `CLI-FW-06`. Proof projects:
[`scratch/dev-skill-delegates-to-a-worker-the-agent-does-not-have`](../scratch/dev-skill-delegates-to-a-worker-the-agent-does-not-have/)
and [`scratch/route-handler-receives-the-response-as-its-request`](../scratch/route-handler-receives-the-response-as-its-request/).

| # | Item | Status | Notes |
|---|---|---|---|
| A1 | **Reproduce the stall in an interactive multi-turn session** | TODO | Still the one thing `f-ai-06` does not prove, and the deep pass on 2026-08-24 narrowed rather than closed it. Every arm of both experiments finished the task: `codex exec` is non-interactive, so *"the main session is always free for the **next input**"* and *"so the developer can stop **between steps**"* have no referent. `codex`'s `default_mode_request_user_input` flag was tried as the way in and is **inert** — enabling it changes the rendered prompt by zero bytes. Remaining candidates: `codex app-server` or `remote-control` (both experimental), or driving the TUI. What the deep pass *did* establish: an ablation attributes the `About to:` announcements to the `Announce before you act` block alone (F full 6, G minus-Announce **0**, H minus-worker 6, I minus-both **0**), and the worker instruction is a silent no-op in practice — **0 of 23 and 0 of 27** agent turns mention a worker or delegation. See `scratch/dev-skill-delegates-to-a-worker-the-agent-does-not-have/ablate.sh`. |
| A2 | **Run `f-rt-01`'s reproduction against php, ruby and python** | TODO | All three were *read*, not run, so the row carries `?` for each. Source says: ruby (`lib/tina4/dispatch_pipeline.rb:692`) is name-keyed on `:request`/`:req` with `else resp` — same shape, looks affected; php (`Tina4/Router.php:1562`) resolves by type hint as well as name and has a two-param positional fallback — looks immune; python (`tina4_python/core/server.py:2034`) is positional and ignores names — looks immune. Each needs the equivalent of `argprobe.mjs` before any token moves off `?`. |
| A3 | **Correct the mechanism on upstream tina4-nodejs#57** | TODO | [#57](https://github.com/tina4stack/tina4-nodejs/issues/57), opened 2026-08-24 by `andy-ci-cao` (third party, not us). Symptom right, mechanism wrong — it says Tina4 "supplies an incomplete request object"; the request is complete and the handler is handed the *response* instead. `f-rt-01` has the reproduction. Comment on the existing issue rather than opening a second one, and check remote state first — another session may already have. |
| A4 | **Decide whether `f-ai-06` goes upstream, and to which repo** | TODO | The four SKILL.md copies live in four separate port repos, so one fix is four PRs unless the maintainer wants a different shape. `tina4-js`'s softened copy is `clear` for this defect but carries its own approval gate (*"the plan file (approved to start)"*, *"scope it with the developer first"*) that has never been measured. Ask before filing. |
| A5 | **`npx tina4nodejs <cmd>` silently no-ops and exits 0** | TODO | Not yet root-caused and **not** filed — may well be an npx artefact rather than a Tina4 defect: `node node_modules/tina4-nodejs/packages/cli/dist/bin.js --help` prints the full help, while `npx tina4nodejs --help` emits 169 bytes (two SQLite warnings) and exits 0. Matters because both Codex arms ran `npx tina4nodejs test`, got exit 0 with no output, and **reported their tests as passing** — one of them in as many words. Reproduce outside a codex fixture before writing a row. |
| A6 | **`expectEqual` / `expectTrue` DO exist in tina4-nodejs** | TODO | Data point for **P2** and ledger `PY-DOC-01`: on released **3.13.103**, `import('tina4-nodejs')` exports `TestClient, TestResponse, Tina4AssertionError, Tina4Test, expectEqual, expectFalse, expectRaises, expectTrue, tests` — `expect*`, no `assert*`. So upstream `10a1e3d`'s Node rename was correct **for Node**, which strengthens the case that the Python page's snake_case rewrite was collateral. Separately: both Codex arms wrote `import { assertTrue } from "tina4-nodejs"`, which fails to load with `SyntaxError: The requested module 'tina4-nodejs' does not provide an export named 'assertTrue'` — model error, not skill error (neither `assert*` nor `expect*` appears anywhere in the developer skill, which is arguably the gap worth fixing). |
| A7 | **Finish what `de5358d` started** | TODO | `de5358d` (2026-08-13) is titled *"drop approval-to-start / confirm-to-close / ask-first gates"* and left five of them in place — `:236` approval-to-start, `:850` confirm-to-close, and three UI ask-gates at `:409`, `:483`, `:861`. Verified: the commit's diff matches none of the five, and `git blame` dates all five to commits *before* it. This is now edit **(1)** on `f-ai-06`'s fix list, ahead of the worker change. Same five lines in all four ports. **2026-08-25:** written as a runnable patch — `scratch/dev-skill-delegates-to-a-worker-the-agent-does-not-have/suggested-fix.md` + `apply-fix.sh`, covering this and the other five edits across all twelve files (4 skills x 3 trees), verified to apply with 0 unmatched anchors. Not applied, not branched, not filed — awaiting a decision on **A4**. Note the recorded line numbers are stale: SKILL.md is now 996 lines and the patch anchors on text. |
| A8 | **Two plan doctrines in one file** | TODO | The Working Method (`:120-257`) and *Plan First — Always* (`:764-868`) restate the same rules in different words, and `:769`'s *"No exceptions"* is the stricter of the two. Reconcile or delete one. Edit **(6)** on `f-ai-06`. Not measured — recorded from a full read of the skill, not from a run. |
| A9 | **Re-sync `.agents` / `.cursor` copies of the developer skills** | TODO | `f-ai-07`. Four verified factual drifts reach Codex and Cursor but not Claude: a `tina4nodejs metrics` command that does not exist (×2), `initDatabase(url)` where the real signature reads `config?.url` and a bare string silently falls back to SQLite, `tina4py stage` / `deploy promote` which do not exist, `src/migrations/` where php's canonical location is the project root, and a Ruby minimum of 3.3 where the gemspec says 3.1. Fix belongs in `scripts/sync-tina4-skills.sh`, whose exclusion note reasons about cross-repo drift and misses the two sibling trees inside each repo. **2026-08-25:** `apply-fix.sh` moves all three trees together for the `f-ai-06` edits, so applying that patch does not widen this drift — but it does not close it either; the sync script is still the fix. |

---

## Python docs PRs in flight — opened 2026-08-13

Both are OPEN, MERGEABLE and unreviewed. This replaces the `getstar/state.md` resume file, which
was deleted once the work shipped.

| PR | Contents | Checks |
|---|---|---|
| [tina4-book 152](https://github.com/tina4stack/tina4-book/pull/152) | Chapter 1 re-run against the current release; output blocks re-captured, wrong defaults fixed, a `tina4 doctor` section added. 1 file, +162/-115 | none configured on that repo |
| [tina4-documentation 50](https://github.com/tina4stack/tina4-documentation/pull/50) | The Python quick reference corrected against a running server, plus the chapter re-sync. 2 files, +305/-182 | `audit` ×2 + snyk, all SUCCESS |

| # | Item | Status | Notes |
|---|---|---|---|
| P1 | **They must merge together** | BLOCKED | `sync-books.sh` regenerates `docs/python/01-getting-started.md` from the book chapter, so merging the docs PR alone loses the book edits, and merging the book alone leaves the site stale until the next sync. Say so in review if anyone tries to take one. |
| P2 | **Answer the `expect_*` question on docs PR 50** | BLOCKED | Ledger `PY-DOC-01`. Upstream `10a1e3d` renamed `assertEqual`->`expectEqual` for tina4-nodejs and the same pass rewrote the Python page's snake_case names to `expect_*`, which exist in no released `tina4-python`. The PR uses `assert_*`, the names that exist. A maintainer has to confirm Python was not meant to follow. PHP and Ruby were never touched. |
| P3 | **Decide what happens to `docs/python-entry` on the fork** | TODO | The rejected restructure, pushed at `32da3ec`, no PR. Leaving it there advertises a page shape Andre turned down. Delete the fork branch or leave it deliberately — but the local branches `docs/python-entry` and `docs/python-getting-started` are the only record of that work and of the comparison measurement, so keep those. |
| P4 | **Do not trust a stale read of the upstream repos** | TODO | `tina4-documentation` moved **58 commits** under this work in a single day, twice (13, then 56, then 2). Always `git fetch` and re-read before quoting a file or rebasing. `scripts/audit-truth.py` is a CI gate there and it is strict: ASCII-only punctuation, and `TINA4_*` names must appear via `getenv()` in one of the four framework source trees. Locally it reports ~215 false env-var failures because only `tina4-js/src` is checked out beside the docs repo; CI resolves them. `pnpm` is not installed here despite the `packageManager` field — use `npm`. |

---

## Deferred from the Getting Started rebuild — 2026-08-11

Parked on USER direction ("problems for later, focusing on tina4 docs only now") while the
Python section rewrite shipped. **The `getstar/` working notes were deleted on 2026-08-13** once
the work shipped as PRs — the evidence now lives in the PR descriptions,
[tina4-book 152](https://github.com/tina4stack/tina4-book/pull/152) and
[tina4-documentation 50](https://github.com/tina4stack/tina4-documentation/pull/50), which
enumerate every corrected claim and where each fact was read from. Recover the notes from git
history (`git log -- getstar/`) if the audit detail is ever needed again.

**Where the issues themselves live, from 2026-08-13:** these G-rows track the *work*; the
issues they describe now have version-stamped rows with reproduction steps in
[`known-issues/ledger.md`](../known-issues/ledger.md). G1, G1a, G4, G10 and G11 are all
represented there. Update the ledger row when a version is re-tested; update the G-row when
the work moves.

**Update 2026-08-12 — the restructure was rejected and the corrections were re-applied to the
old page structure instead.** Andre did not want the new shape. Consequences for the rows
below: **G6 has no template to repeat** (there is no new Python shape to copy — what
transfers is the correction pass, which is G2); **G7 and G3 are moot** (both were about
placing the quick-reference page in the sidebar, and that page no longer exists); **G8's
counterweight concern is closed** (the comparison table is not published, so there is nothing
to counterbalance). G1 and G1a stand unchanged — they are framework work either way.

| # | Item | Status | Notes |
|---|---|---|---|
| G1a | **Framework/CLI behaviour the docs deliberately do not describe** | TODO | Found while re-running every claim, and **kept out of the documentation on USER direction 2026-08-11** — "keep the documentation as intended and we will fix the framework separate". Each is measured on CLI 3.8.67 / tina4-python 3.13.97. <br>1. **`.env` `TINA4_PORT` overrides `--port`.** With `TINA4_PORT=7821` set, `tina4 serve --port 7899` binds 7821. The flag does beat a bare `PORT`. Most tools give the explicit flag precedence. <br>2. **A busy port is taken, not avoided.** `tina4 serve` logs `Port 7146 in use — killing existing process...` and terminates the listener rather than failing or incrementing. Can kill an unrelated service. <br>3. **`tina4 routes`** prints the "must be started with the tina4 CLI" guard instead of listing routes; the command is simply omitted from the chapter. <br>4. **`tina4 test`** fails `No module named pytest` on a fresh scaffold, which ships no runner. The chapter now reads as ordinary setup (`uv add pytest`) rather than a bug report. <br>5. **`tina4_python.websocket` shadows the decorator** — the top-level name is the module, so `@websocket(...)` raises `'module' object is not callable`. Docs give the `core.router` import with no explanation. |
| G1 | **Two framework defects found while fact-checking the quick reference** | TODO | `@cached(max_age=N)` does not cache — same route returned different bodies a second apart, with and without `TINA4_CACHE_BACKEND=memory`. `ServiceRunner.register(name, instance)` accepts an object with `run()` and **silently never runs it** — 0 invocations, nothing logged; `register_service()` is the working path. Framework behaviour, not documentation. **Already ledger rows `PY-FW-01` / `PY-FW-02`.** Raise with Andre separately from the docs PRs. |
| G2 | **Sibling language quick-reference pages carry the same class of errors** | TODO | 15 of 36 sections were wrong on `docs/python/index.md`; nine would not run at all. `nodejs/index.md` (936 lines), `php` (739), `ruby` (566), `js` (260), `delphi` (230) are the same species of hand-maintained page and have never been fact-checked. Fixing Python's did nothing for theirs. |
| G3 | **`tina4press` hard-codes the section landing label as "Overview"** | ACCEPTED | `autoSectionSidebar` emits `items: [{ text: "Overview", link: indexPage.url }]` and never calls `titleFromPage` for it, so retitling `docs/<lang>/index.md` changes the page and not the nav. **USER accepted the mismatch 2026-08-11** — recorded so nobody re-investigates. Reopen only if the label starts to matter. |
| G8 | **"What it costs you" is written and measured, but published nowhere** | TODO | Five bullets naming what Tina4 is worse at — shallow generated OpenAPI (no `requestBody` schema, one generic `200`), no request typing or validation, throughput, ecosystem size, fixed conventions. Every one measured. **Removed from the landing page on USER direction 2026-08-11** ("keep it aside but remove it from the overview"). All five lived in `comparison-testing/results/2026-08-11-python.md` → *What Tina4 lost on*, **removed 2026-08-19** with that directory — recover from git history. Candidate homes if they are ever published: `/comparisons/` once it is re-benchmarked, or a trade-offs page. The counterweight concern is closed — the comparison table was never published, so there is nothing to counterbalance. |
| G9 | **`tina4press` highlights plain output blocks as JavaScript** | TODO | `node_modules/tina4press/src/highlight.js`: `const src = KEYWORDS[lang] != null ? KEYWORDS[lang] : KEYWORDS.javascript;` — an unknown or absent fence language falls back to the JavaScript keyword set, so every terminal-output block on the site gets `do`, `default`, `from`, `return`, `in`, `of`, `new` coloured as code. Measured on the built site: `php/01-getting-started` 25 stray keyword spans, `nodejs/01-getting-started` 38, `ruby/01-getting-started` 16, `general/01-what-is-tina4` 2 — **site-wide and pre-existing**, on pages this project never touched. No docs-only fix: `text`, `console` and `output` all fall through to the same default, and only `json`/`yaml`/`yml` carry empty keyword sets, which would mean mislabelling command output. Fix belongs with G7: add a `text`/`plain` entry, or make the fallback empty rather than JavaScript. |
| G7 | **`tina4press` cannot place a page beside a section's Overview** | SHELVED | Asked for 2026-08-11: Quick Reference directly under Overview in the top "Python Reference" group. **Not doable from config** — that group is built inside `autoSectionSidebar` with one hard-coded item, and `themeConfig.sidebar` is all-or-nothing (a truthy value bypasses the auto sidebar for every page). A second `sidebarGroups` entry with the same title was tried and renders **two identical stacked headers**. <br><br>**A working fix was written and verified locally** against a patched `node_modules/tina4press/src/sidebar.js`: a new `themeConfig.sidebarIndexStems[section]` option whose stems are appended to the index group's items and seeded into `seen` so they are not also collected as orphans. ~12 lines, backwards-compatible (absent config = current behaviour). Rendered correctly: Overview, then Quick Reference, with Foundations still open. <br><br>Both the patch and the config change were **reverted** — `node_modules` is gitignored and tina4.com builds against `tina4press@^0.1.14` from npm, so shipping the config alone would drop the page into the collapsed "More" group, worse than today. Needs a PR to `tina4stack/tina4press` (public, not cloned here) plus a release, then a dependency bump. **Shelved on USER direction: "focus on the docs directly only".** Current state: Quick Reference sits in the `Reference` group, which works on the live site today. |
| G4 | **Two CLI defects, left out of Chapter 1 rather than documented** | TODO | `tina4 routes` in a fresh project prints the "must be started with the tina4 CLI" guard instead of listing routes — omitted from the chapter, since `/__dev` does that job. `tina4 test` fails `No module named pytest` because the scaffold ships no runner — documented *with* its fix (`uv add pytest`), verified to work. |
| G5 | **Throughput unmeasured, and the published figures are stale** | TODO | `/comparisons` still carries a March 2026 Apple Silicon run this machine cannot reproduce (`hey` is not installed). Upstream has already de-linked that page from the home page pending re-benchmarking. Needs matched hardware and its own spec — `comparison-testing/readme.md` deliberately excludes throughput. |
| G10 | **The site's inline `@tests` builders are named for an API that does not exist** | RAISED | Upstream `10a1e3d` ("docs(132): rename inline @tests descriptor builders assert_*->expect_* in the docs site") renamed them across the docs site. `tina4_python.Testing` defines `assert_equal`, `assert_raises`, `assert_true`, `assert_false` and `tests` — and no `expect_*` — on **both 3.13.94 and 3.13.98** (latest published). A reader copying the snippet gets `NameError`. Corrected back to `assert_*` on `docs/python/index.md` in `docs/python-consistency-fixes`, and **flagged in that commit message** because it reverses a deliberate upstream change: if the rename anticipates an unreleased framework change, that section should revert and land with the release instead. **Correction 2026-08-13:** the rename was **Node-led and Python was collateral**. `10a1e3d` renamed `assertEqual`->`expectEqual` in `docs/nodejs/{18-testing,35-complete-app,index}.md` -- camelCase, presumably correct for tina4-nodejs -- and the same pass rewrote `docs/python/index.md`'s snake_case names. **PHP and Ruby were never touched**, so this is one page's collateral damage, not a four-language decision. **Raised as an explicit open question on docs PR 50** so a maintainer confirms Python was not meant to follow. Full row with a repro: [`known-issues/ledger.md`](../known-issues/ledger.md) `PY-DOC-01`. Separately, `docs/python/18-testing.md` documents a *different* API — `from tina4_python.test import Test, assert_equal` with `(actual, expected, message)` — which is the pytest-style helper, not the `@tests` descriptor builder; the two are easy to confuse and neither page says so. |
| G11 | **Chapter 38 states 97 features; its own table has 102 rows** | TODO | `book-1-python/chapters/38-feature-list.md` says "**97 built-in features**" in the opening line and "The same 97 features ship in every Tina4 framework" at line 166, while the feature tables carry 102 rows. Chapter 1 was aligned to the stated 97 on 2026-08-12 (it previously said "70 other features", contradicting both). Whichever number is right, three places currently disagree. Count is worth re-deriving from the framework rather than from the table. |
| G6 | **Repeat the section rewrite for the other five languages** | SUPERSEDED | **Superseded 2026-08-12** — the Python restructure it was meant to replicate was rejected, so there is no new shape to copy. What actually transfers to the other five languages is the correction pass, which is already tracked as G2. Kept for the record: the plan was landing = the argument, chapter 1 = the mechanics, quick reference = the finder, with per-language comparatives (Laravel/Slim, Rails/Sinatra, Express/Nest). |

---

## Housekeeping

| # | Item | Status | Notes |
|---|---|---|---|
| F1 | Docker containers (`tina4_pg` + `tina4_rabbit`/`tina4_mongo`/`tina4_kafka`) + `tina4 serve` (7146) | TODO | **Docker recovered 2026-07-02: `tina4_pg` up (healthy).** The 3 brokers + serve are down (only needed for Ch12 broker-gated tests / live mocks — start on demand). At EOD stop the 3 brokers + serve if started; leave `tina4_pg`. Native PG fallback (`Start-Service postgresql-x64-18`) needs admin. |

---

## Notes
- Standing constraints (read-only framework, doc-only, no test rigging, find-don't-fix, certainty-over-cause, no "we", file at EOD, coverage ledger per chapter) live in `documentation-testing/readme.md` + auto-memory — not repeated here.
- Completed work is recorded in `../known-issues/ledger.md` (issues), `coverage-ledger/` (chapter progress), and `audit-log.md`. DONE rows are not kept here.
