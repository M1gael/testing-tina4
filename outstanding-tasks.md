# Outstanding Tasks

Running backlog of work asked-for-but-not-yet-done. Mutable. When an item lands,
move it to the relevant record (`findings-log.md` / `coverage-ledger/`) and delete the row
here. `findings-log.md` holds confirmed findings + chapter progress; THIS file holds the
to-do list across sessions so nothing the user asked for gets dropped.

**Audit verdicts, version-bump records, and fix re-verification results do NOT belong here — they go to `findings-log.md` → Maintenance & Audit Log. This file holds only the resulting OPEN todo items.**

Status legend: `TODO` not started · `WIP` in progress · `BLOCKED` waiting on something.

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

Study + evidence: [`codex/CODEX-CONTEXT-RESEARCH.md`](codex/CODEX-CONTEXT-RESEARCH.md).
Findings CODX-01..05 recorded in [`agent-testing/codex-skill-delivery/README.md`](agent-testing/codex-skill-delivery/README.md).
Fixture: `codex/` (tina4 CLI 3.8.64 · tina4-python 3.13.94 · codex-cli 0.145.0).

| # | Item | Status | Notes |
|---|---|---|---|
| X1 | **File CODX-02..07 upstream** (`tina4stack/tina4-python`) | TODO | Two substantive: **CODX-02** skills installed only to `.claude/skills/`, so Codex (scans `.agents/skills/`) receives 0 of 158 KB; **CODX-06** `.cursorules` is a one-`r` typo, so Cursor receives nothing at all (3 sites: `ai/__init__.py:22`, `:254`, `CLAUDE.md:1451`). Then CODX-03/04 (non-TTY `EOFError`, dropped `--all`/`--force`), CODX-05 (empty `.cursor/`), CODX-07 (Aider needs `--read`). Follow `documentation-testing/readme.md` → *Upstream filing*. Per auto-memory, **no `owner/repo#NNN` refs in commit messages** from this account. |
| X1b | Verify the 5 untested tools in the scorecard | TODO | Only **Claude Code** (works) and **Codex** (half) are measured. Copilot / Cline / Windsurf have plausible-looking paths but were never checked against a running tool; Cursor and Aider are already known-broken by inspection. Each needs the same treatment Codex got — install, then confirm from the tool's side that the file is actually in context. |
| X2 | Re-verify **CODX-01** is fixed before filing again | TODO | Doubled-brace `response({{...}})` was already reported; confirmed still present in 3.13.94. Check whether an upstream issue exists before opening a duplicate. |
| X3 | Run the `nosk`/`sk` arms now that delivery is measurable | TODO | Delivery itself is settled without a model (CODX-02). The arms now answer a *different*, still-open question: does a model **act** on `AGENTS.md`'s pointer block, and does registered-skill delivery change the architecture it produces? Use `codex debug prompt-input` to pin each arm's context before the run. |
| X4 | Keep `AGENTS.md` off the harness repo root | TODO | Codex merges `<git-root>/AGENTS.md` into every session under it. `codex/` sits inside `testing-tina4`, so a root `AGENTS.md` would silently prepend to every arm and contaminate any comparison. |
| X5 | Probe **channel 3 — MCP** end to end | TODO | tina4-python ships an HTTP/SSE MCP server (`tina4_python/mcp/`, gated on `TINA4_MCP`/`TINA4_DEBUG`, port framework+2000 = 9145). `codex mcp add <name> --url <URL>` consumes streamable HTTP. Untested: whether Codex's client negotiates tina4's protocol version and whether the loopback/token gate admits it. **Not** a substitute for the skills fix — it carries executable tools, not conventions. Security note: the built-in dev tools are DB query/execute + file read/write, so never register against a non-loopback URL without a token. |
| X6 | Evaluate a **Codex/Claude/Cursor plugin bundle** as the real distribution channel | TODO | Codex's plugin loader accepts `.codex-plugin/`, `.claude-plugin/` *and* `.cursor-plugin/` manifests, and a plugin can carry `skills/` + `.mcp.json` + `hooks.json` together. One versioned, installable-by-name bundle would replace per-project file writes for all three tools at once — strictly better than fixing `tina4 ai`'s paths tool by tool. Scope this before investing further in the file-copy approach. |

---

## Deferred from the Getting Started rebuild — 2026-08-11

Parked on USER direction ("problems for later, focusing on tina4 docs only now") while the
Python section rewrite shipped. Notes in [`getstar/`](getstar/); the evidence table is
[`getstar/python-evaluation.md`](getstar/python-evaluation.md) section 2a.

| # | Item | Status | Notes |
|---|---|---|---|
| G1 | **Two framework defects found while fact-checking the quick reference** | TODO | `@cached(max_age=N)` does not cache — same route returned different bodies a second apart, with and without `TINA4_CACHE_BACKEND=memory`. `ServiceRunner.register(name, instance)` accepts an object with `run()` and **silently never runs it** — 0 invocations, nothing logged; `register_service()` is the working path. Framework behaviour, not documentation. **Not KI Log material as they stand** — needs re-testing inside `documentation-testing/` against a quoted chapter claim to earn a `PY-NN-NN` ID. Raise with Andre separately from the docs PRs. |
| G2 | **Sibling language quick-reference pages carry the same class of errors** | TODO | 15 of 36 sections were wrong on `docs/python/index.md`; nine would not run at all. `nodejs/index.md` (936 lines), `php` (739), `ruby` (566), `js` (260), `delphi` (230) are the same species of hand-maintained page and have never been fact-checked. Fixing Python's did nothing for theirs. |
| G3 | **`tina4press` hard-codes the section landing label as "Overview"** | ACCEPTED | `autoSectionSidebar` emits `items: [{ text: "Overview", link: indexPage.url }]` and never calls `titleFromPage` for it, so retitling `docs/<lang>/index.md` changes the page and not the nav. **USER accepted the mismatch 2026-08-11** — recorded so nobody re-investigates. Reopen only if the label starts to matter. |
| G7 | **`tina4press` cannot place a page beside a section's Overview** | SHELVED | Asked for 2026-08-11: Quick Reference directly under Overview in the top "Python Reference" group. **Not doable from config** — that group is built inside `autoSectionSidebar` with one hard-coded item, and `themeConfig.sidebar` is all-or-nothing (a truthy value bypasses the auto sidebar for every page). A second `sidebarGroups` entry with the same title was tried and renders **two identical stacked headers**. <br><br>**A working fix was written and verified locally** against a patched `node_modules/tina4press/src/sidebar.js`: a new `themeConfig.sidebarIndexStems[section]` option whose stems are appended to the index group's items and seeded into `seen` so they are not also collected as orphans. ~12 lines, backwards-compatible (absent config = current behaviour). Rendered correctly: Overview, then Quick Reference, with Foundations still open. <br><br>Both the patch and the config change were **reverted** — `node_modules` is gitignored and tina4.com builds against `tina4press@^0.1.14` from npm, so shipping the config alone would drop the page into the collapsed "More" group, worse than today. Needs a PR to `tina4stack/tina4press` (public, not cloned here) plus a release, then a dependency bump. **Shelved on USER direction: "focus on the docs directly only".** Current state: Quick Reference sits in the `Reference` group, which works on the live site today. |
| G4 | **Two CLI defects, left out of Chapter 1 rather than documented** | TODO | `tina4 routes` in a fresh project prints the "must be started with the tina4 CLI" guard instead of listing routes — omitted from the chapter, since `/__dev` does that job. `tina4 test` fails `No module named pytest` because the scaffold ships no runner — documented *with* its fix (`uv add pytest`), verified to work. |
| G5 | **Throughput unmeasured, and the published figures are stale** | TODO | `/comparisons` still carries a March 2026 Apple Silicon run this machine cannot reproduce (`hey` is not installed). Upstream has already de-linked that page from the home page pending re-benchmarking. Needs matched hardware and its own spec — `comparison-testing/readme.md` deliberately excludes throughput. |
| G6 | **Repeat the section rewrite for the other five languages** | TODO | PHP, Ruby, Node.js, JavaScript, Delphi. Python's shape is the template: landing = the argument, chapter 1 = the mechanics, quick reference = the finder. `BACKEND_GROUPS` already carries the `quick-reference` stem for all four backend languages. The comparison spec takes per-language comparatives (Laravel/Slim, Rails/Sinatra, Express/Nest). |

---

## Housekeeping

| # | Item | Status | Notes |
|---|---|---|---|
| F1 | Docker containers (`tina4_pg` + `tina4_rabbit`/`tina4_mongo`/`tina4_kafka`) + `tina4 serve` (7146) | TODO | **Docker recovered 2026-07-02: `tina4_pg` up (healthy).** The 3 brokers + serve are down (only needed for Ch12 broker-gated tests / live mocks — start on demand). At EOD stop the 3 brokers + serve if started; leave `tina4_pg`. Native PG fallback (`Start-Service postgresql-x64-18`) needs admin. |

---

## Notes
- Standing constraints (read-only framework, doc-only, no test rigging, find-don't-fix, certainty-over-cause, no "we", file at EOD, coverage ledger per chapter) live in `documentation-testing/readme.md` + auto-memory — not repeated here.
- Completed work is recorded in `findings-log.md` (findings, chapter progress, Maintenance & Audit Log) + the per-chapter `coverage-ledger/` files. DONE rows are not kept here.
