# Outstanding Tasks

Running backlog of work asked-for-but-not-yet-done. Mutable. When an item lands,
move it to the relevant record (`findings-log.md` / `coverage-ledger/`) and delete the row
here. `findings-log.md` holds confirmed findings + chapter progress; THIS file holds the
to-do list across sessions so nothing the user asked for gets dropped.

Status legend: `TODO` not started · `WIP` in progress · `BLOCKED` waiting on something.

---

## Chapter 12 — Queues (active chapter)

### A. Implement remaining documented sections (verbatim, served, traced)
| # | Item | Status | Notes |
|---|---|---|---|
| A1 | **S8 Queue in Route Handlers** — implement verbatim under `tina4 serve`; push/produce from real route handlers (`@post`), traced tests | TODO | next up; uses the documented `@post("/api/orders")` pattern (12-queues.md S8) |
| A2 | **S9 Switching Backends via .env** — verify backend selection purely via `.env` (no code change), the env-var table (S9), under `tina4 serve` | TODO | pairs with A1 |
| A3 | **S10 Produce and Consume Across Topics** — file-backend verbatim section impl (ops already exercised at backend level via the matrix, but not the verbatim S10 impl) | TODO | |
| A4 | **S11 Exercise: Build an Email Queue** — the 4 documented endpoints + consumer + dead-letter flow | TODO | |
| A5 | **S12 Solution** — implement `src/routes/email_queue.py` + `src/workers/email_worker.py` verbatim | TODO | |
| A6 | **S13 Gotchas** — exercise each gotcha's behavioural claim | TODO | |

### B. Close section-thoroughness audit gaps (from 2026-06-25 16-agent audit; S2 thorough, S3–S7 minor-gaps)
| # | Item | Status |
|---|---|---|
| B1 | **S3** — assert `priority` defaults to `0` and `delay_seconds` defaults to `0` (the default VALUE, currently only relied on indirectly) | TODO |
| B2 | **S4** — continuous-poll `consume()` headline loop: sleeps-when-empty + picks up mid-stream arrivals (needs a threaded/timeout harness) | TODO |
| B3 | **S5** — priority-first via `consume()` (only `pop()` tested today); broker "stores the priority on each message" sub-claim (only delivery ORDER checked) | TODO |
| B4 | **S6** — `job.retry(delay_seconds=N)` — the delay arg is never passed (only no-arg re-queue tested) | TODO |
| B5 | **S7** — `purge("failed")` never called (named status, zero coverage); "consume retries on its own" snippet only proven via manual pop+fail, not a real `consume()` loop | TODO |

### C. Visual showcase
| # | Item | Status | Notes |
|---|---|---|---|
| C1 | Extend the section-by-section explorer (`src/routes/chapter_explorer.py`, `GET /chapter/12`) to cover **S8 + S9** (+ S10–S13 as they land) so every section is browsable with live pass/diverge | TODO | S2–S7 already covered; backend parity matrix at `/queue/backends` already covers 30 ops × 4 backends |

### D. Deferred probes (not average-user / undocumented — lower priority)
| # | Item | Status | Notes |
|---|---|---|---|
| D1 | `Queue(visibility_timeout=)` constructor param — reservation reclaim of unacked jobs; **may contradict S6:240** ("call neither complete()/fail() → claimed on pop, will not be retried"). Candidate for a real finding | TODO | undocumented in Ch12 |
| D2 | `max_retries=` override params on `dead_letters()`/`purge()`/`retry_failed()`; `produce(delay_until=)`; `retry(delay_seconds=)`; `job.to_hash()/to_array()` (aliases of covered `to_json()`) | TODO | edge API surface |

### E. Filing (USER files at EOD on tina4-book #144 — assistant only logs)
| # | Item | Status | Notes |
|---|---|---|---|
| E1 | File the unfiled Ch12 findings on **#144**: PY-12-01, PY-12-03, PY-12-04, PY-12-05, PY-12-06, PY-12-07 | TODO | PY-12-02, BH-50, BH-51, BH-52 already filed |
| E2 | Mongo `retry()`-doesn't-revive divergence (PY-12-03 point c) — write the standalone report for #144 | TODO | pending since early session |
| E3 | All 9 doc-fidelity findings adversarially confirmed REAL (2026-06-25) — ready to file as-is | DONE-input | feeds E1 |

### F. Housekeeping
| # | Item | Status | Notes |
|---|---|---|---|
| F1 | Stop brokers + serve at end of day: `docker stop tina4_rabbit tina4_mongo tina4_kafka`; kill `tina4 serve` (port 7146) | TODO | serve currently left running for browsing |

### G. Final deliverable
| # | Item | Status | Notes |
|---|---|---|---|
| G1 | **Summarise standing on everything the user asked** (findings-real verification ✓done, S2–S7 thoroughness parity ✓done, S8/S9 impl A1/A2, full section-by-section showcase C1) — give the user a clear status picture | TODO | the LAST step, after A/B/C land |

### Already completed (this turn / prior) — for the status picture, not action items
- ✅ Verified all 9 doc-fidelity findings are REAL (16-agent adversarial workflow, 2026-06-25) — not doc-misreads/artifacts.
- ✅ Audited per-section thoroughness parity for S2–S7 (S2 thorough; S3–S7 gaps captured as B1–B5 above).

---

## Notes
- Standing constraints (read-only framework, doc-only, no test rigging, find-don't-fix, certainty-over-cause, no "we", file at EOD) live in `readme.md` + auto-memory — not repeated here.
- When picking up: resume order the user set was **close audit gaps (B) → implement S8/S9 (A1/A2) → showcase (C1) → summary**.
