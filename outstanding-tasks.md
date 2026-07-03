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

## Housekeeping

| # | Item | Status | Notes |
|---|---|---|---|
| F1 | Docker containers (`tina4_pg` + `tina4_rabbit`/`tina4_mongo`/`tina4_kafka`) + `tina4 serve` (7146) | TODO | **Docker recovered 2026-07-02: `tina4_pg` up (healthy).** The 3 brokers + serve are down (only needed for Ch12 broker-gated tests / live mocks — start on demand). At EOD stop the 3 brokers + serve if started; leave `tina4_pg`. Native PG fallback (`Start-Service postgresql-x64-18`) needs admin. |

---

## Notes
- Standing constraints (read-only framework, doc-only, no test rigging, find-don't-fix, certainty-over-cause, no "we", file at EOD, coverage ledger per chapter) live in `readme.md` + auto-memory — not repeated here.
- Completed work is recorded in `findings-log.md` (findings, chapter progress, Maintenance & Audit Log) + the per-chapter `coverage-ledger/` files. DONE rows are not kept here.
