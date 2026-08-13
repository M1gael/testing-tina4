# Unverified leads — `agent-testing/`

Observations surfaced while **building apps with AI agents**, not while walking documented
chapters. They carry **no quoted-documented-claim trace**, so per
`documentation-testing/readme.md` rules 11–12 they are **ineligible for the Known Issues
Log** in `findings-log.md` as written.

**Promotion path:** re-test the claim inside `documentation-testing/pypy/` against a quoted
claim from a real chapter → earn a `PY-NN-NN` ID → move the row to `findings-log.md`. Or
file upstream and track as `BH-<n>`. Nothing is promoted on an agent run alone.

Status: `lead` untested · `dup` already covered by a KI row · `promoted` moved out.

---

## Origin: `task-manager` agent-built app (recovered 2026-08-03)

Five observations recorded by an agent building a task-manager app against tina4-python.
The app itself was deleted; this file is the surviving record. Wording is the original
author's, reorganised and triaged — the technical claims are **unverified by this harness**.

> **Still a triage queue, not an issue log.** Nothing here was migrated into
> [`known-issues/ledger.md`](../known-issues/ledger.md) on 2026-08-13: `L1` and `L3` are
> duplicates of rows already in it, and the rest have no quoted documented claim behind them.
> A lead earns a ledger row only once it has been reproduced.

| # | Claim | Status | Triage |
|---|---|---|---|
| L1 | ORM query (`User().find()`) raises `RuntimeError: No database bound` unless `TINA4_DATABASE_URL` is set or `bind_database()` called | **dup** | Covered three times over: **PY-06-01** (filed [#142](https://github.com/tina4stack/tina4-book/issues/142)), **PY-18-07b**, **PY-18-13b**. No new information. |
| L1a | `tina4 generate model` scaffolds the model file with **no comment or hint** that a DB connection is a prerequisite; auto-discovery is implicit with no explicit wiring in `app.py` | **lead** | *Novel angle.* The existing rows are all doc-fidelity defects in book chapters. This one targets **CLI scaffolding output** — a surface no current row covers. Testable: run `tina4 generate model`, read the emitted file. |
| L2 | Query Builder and ORM return **structurally different** results: `Database.fetch()` returns a `DatabaseResult` (data via `.records` / `.to_dict()`), `Task().find()` returns a raw `list` of ORM objects. Forces defensive `hasattr(result, 'to_dict')` in generic handlers | **lead** | *Novel* — zero `DatabaseResult` mentions in `findings-log.md`. API-symmetry complaint, so promotion needs a chapter that **documents both** return contracts; if neither chapter states a contract, this is a doc-completeness gap, not a divergence. Ch05 (database) + Ch07 (querybuilder) are the places to look. |
| L3 | `@noauth()` is not prominently documented for the most common case — a public `POST /api/login`. Developers must read framework source to find how to bypass the token gate | **dup** | Same defect class as **PY-06-07**, **PY-12-10**, **PY-10-02** — writes are Bearer-gated by default and the chapters never say so. The login-endpoint framing is new but the underlying claim is logged and filed ([#144](https://github.com/tina4stack/tina4-python/issues/144)). |
| L4 | `python3 -m tina4_python` fails: `No module named tina4_python.__main__`. Package ships no `__main__.py`, breaking standard Python conventions for executable packages | **lead** | *Novel.* Cheap to verify. Caveat: promotion requires a **documented claim** that the module is runnable that way — Tina4 documents the Rust `tina4` CLI as the entry point, so if no chapter promises `python -m`, this is a convention gripe with no doc trace and stays here. |
| L5 | `python3 app.py` prints an error and exits, demanding `tina4 serve`. Override is `TINA4_OVERRIDE_CLIENT=true`, which reads as a hack rather than a supported config — complicates Docker / custom WSGI-ASGI deployment | **lead** | *Novel* — zero `OVERRIDE_CLIENT` mentions in `findings-log.md`. Strongest promotion candidate: check the **deployment chapter**. If it documents Docker or a custom ASGI server without mentioning the interception or the override, that is a real documented-path gap with a quotable claim. |

### Suggested order if these get worked

1. **L5** — most likely to yield a filable doc gap (deployment chapter vs. execution interception).
2. **L2** — real API-symmetry question; needs Ch05 + Ch07 read first to find the quotable contract.
3. **L1a** — narrow but concrete, and tests a surface (CLI scaffolding) nothing else covers.
4. **L4** — verify in one command, but likely has no doc claim to trace to.

L1 and L3 need no work — fold nothing, they are already logged and filed.

### Provenance caveat

These claims were written by the agent that built the app, not produced by this harness.
Two independent reasons to distrust them: an agent reports its own blockers, so severity is
inflated toward whatever obstructed it; and none were adversarially checked the way
`findings-log.md` rows are. **Re-verify from scratch before filing anything upstream.**
