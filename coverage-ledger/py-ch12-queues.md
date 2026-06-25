# Coverage Ledger — Python · Chapter 12: Queues

Per-section proof-of-coverage for the chapter evaluation. A section is never "complete" —
only **ledger-complete**: every snippet AND every named option marked `✓ tested` /
`⛔ blocked` / `⏸ deferred` / `n/a`, and **every sign-off stamped with the date + the tina4
versions it was verified on**. See [`readme.md`](../readme.md) → Workflow step 7. The
Evaluation Progress table in [`findings-log.md`](../findings-log.md) links here.

- **Doc:** `documentation/tina4-book/book-1-python/chapters/12-queues.md` (13 sections; rewritten 2026-06-24)
- **Framework under test (READ-ONLY):** `pypy/.venv/Lib/site-packages/tina4_python/`
- **Tests:** `pypy/tests/test_ch12_queue_*.py` · **Live mock:** `GET /chapter/12`

Legend: `✓` tested · `⚠` diverges (logged finding) · `⛔` blocked (can't stand up here) · `⏸` deferred (USER) · `n/a` (no testable claim)

> **Re-verification sweep — 2026-06-25 · tina4-python 3.13.47 · CLI 3.8.51** (bumped from 3.13.43; doc blob unchanged vs upstream). Maintainer shipped independent queue work in .44–.47 (Kafka dequeue assignment-wait + RabbitMQ connector size/handshake fixes — the fix commit predates the #144 comments, not a reply). Full ch12 queue suite re-run against live Docker brokers: **all 5 findings still reproduce — none fixed** (PY-12-02, PY-12-03, BH-50, BH-51, BH-52). Only change: Kafka drain-once now blocks for the 15s assignment window but still returns `[]` (latest-offset). The drain sentinel was de-flaked (unique topic + short assign timeout); suite 27 passed ×3 deterministic. Section sign-offs below remain at their 3.13.43 stamp where behaviour is unchanged.

---

## S1 — Not Everything Should Happen Right Now
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51

- concept prose, no code — `n/a` (nothing to exercise)

## S2 — Queue Configuration
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51 · backend-parity exercised with live brokers (Docker rabbitmq:3 / mongo:7 / apache/kafka:3.7.0) · (file backend first exercised 2026-06-23 · 3.13.39)

- file backend is the zero-config default — `✓` `test_ch12_queue_config.py::test_s2_file_is_default_backend`
- first push auto-creates storage at default `data/queue/<topic>` — `✓` `::test_s2_first_push_autocreates_storage_at_default_path`
- `TINA4_QUEUE_PATH` controls the storage dir — `✓` `::test_s2_queue_path_env_controls_dir`
- rabbitmq backend selectable — `✓` (`backend="rabbitmq"` → RabbitMQBackend, lazy) `::test_s2_backend_is_a_constructor_param_py_12_01`
- rabbitmq real push/pop/consume/size round-trip — `✓` `test_ch12_queue_backend_parity.py::test_backend_round_trip_matches_doc[rabbitmq]` (Docker `rabbitmq:3`; `pika` installed — note the connector also has a raw-AMQP fallback so it works without `pika`)
- mongodb real push/pop/consume/size round-trip — `✓` `::test_backend_round_trip_matches_doc[mongodb]` (Docker `mongo:7`; `pymongo` installed — *required*: `MongoConnector.__init__` raises `ImportError` without it; mongo also honors priority via a DESC sort)
- kafka real round-trip — `⚠` **diverges (PY-12-02)**: a patient long-running `consume()` delivers (~16 s, manually verified), but immediate `pop()` / `consume(poll_interval=0)` yield nothing and `size()` is hardcoded `0` — `test_ch12_queue_kafka_semantics.py` (Docker `apache/kafka:3.7.0`; `confluent-kafka` installed — also has a raw-protocol fallback). **Correction to the prior ledger note:** kafka *can* be selected without `confluent-kafka` (the `import` is `try/except pass`); only mongodb hard-requires its driver at construction.
- `uv add pika / confluent-kafka / pymongo` — `✓` installed per S2 (`pika` 1.4.1, `pymongo` 4.17.0, `confluent-kafka` 2.14.2)
- "your code stays the same … work identically" across the 4 backends — `⚠` **holds for file / RabbitMQ / MongoDB (identical push/pop/consume/size), FALSE for Kafka** (PY-12-02)

## S3 — Creating a Queue and Pushing Messages
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51 · (first exercised 2026-06-23 · 3.13.39)

- create queue + `push()` returns a message id — `✓` `test_ch12_queue_create_push.py::test_push_returns_a_message_id`
- "the `topic` argument names the queue" — `✓` `::test_topic_argument_names_the_queue`
- "the payload is any dictionary that can be serialized to JSON" — `✓` `::test_payload_is_any_json_serializable_dict`
- `produce()` pushes to a named topic — `✓` `::test_produce_pushes_to_a_named_topic`
- `size()` reflects pending count — `✓` `::test_size_reflects_pending_count`
- `push(priority=)` — `✓` (via S5 `test_priority_then_oldest_first`)
- `push(delay_seconds=)` — `✓` (via S5 `test_delayed_high_priority_job_stays_hidden`)
- blockquote: backend "selected via environment variables, not constructor parameters" — `✓` **divergence PY-12-01** `::test_s2_backend_is_a_constructor_param_py_12_01`
- blockquote: kafka/mongo as env-selected backend values — `✓` exercised in S2 backend-parity (`test_ch12_queue_backend_parity.py` + `test_ch12_queue_kafka_semantics.py`)

## S4 — Consuming Messages
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51

- `consume(poll_interval=0)` drains once and stops — `✓` `test_ch12_queue_consume.py::test_consume_poll_interval_zero_drains_once_and_stops`
- `consume(iterations=N)` stops after N jobs — `✓` `::test_consume_iterations_stops_after_n`
- `consume(job_id=)` yields one job once, then returns — `✓` `::test_consume_job_id_yields_that_job_once`
- `pop()` returns the highest-priority job, or `None` when empty — `✓` `::test_pop_returns_a_job_then_none_when_empty`
- `job.complete()` removes / `job.fail()` re-enqueues under the retry limit — `✓` `::test_complete_removes_fail_reenqueues`
- continuous-poll headline `consume()` (default `poll_interval`, sleeps-when-empty, never returns) — `⛔` untested (non-terminating; needs a threaded/timeout harness)

## S5 — Priority Ordering
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51

- highest-priority first; ties break oldest-first (verbatim example) — `✓` `test_ch12_queue_priority.py::test_priority_then_oldest_first`
- a delayed job stays hidden until its time arrives, regardless of priority — `✓` `::test_delayed_high_priority_job_stays_hidden`
- "priority ordering is enforced by the file backend" — `✓` (covered by the two tests above, file backend)
- "external brokers … follow their own delivery semantics" — `✓` exercised in the backend matrix below (RabbitMQ = FIFO, MongoDB honors priority — both consistent with the disclaimer)

## S6 — Job Lifecycle
> Signed off: 2026-06-25 · tina4-python 3.13.47 · CLI 3.8.51 · file backend (S6 documents no per-backend caveat). Tests: `test_ch12_queue_lifecycle_s6.py`.

- `job.complete()` terminal — removed, never comes back — `✓` `::test_complete_is_terminal_job_removed`
- `job.fail(reason)` increments `attempts` + re-enqueues under the limit — `✓` `::test_fail_increments_attempts_and_reenqueues`
- `job.reject(reason)` is an alias for `fail()` — `✓` `::test_reject_is_alias_for_fail`
- `job.retry(delay_seconds=0)` manually re-queues, bypassing the retry limit — `✓` (re-queue itself) `::test_job_retry_requeues_bypassing_limit`
- `job.payload` / `job.id` / `job.attempts` / `job.error` available — `✓` `::test_job_exposes_payload_id_attempts_error`
- "call neither complete()/fail() → claimed on pop, not retried" — `✓` `::test_pop_without_ack_is_not_retried`
- `job.retry()` leaves a dead-letter **duplicate** (same id in pending AND dead) — `⚠` **divergence PY-12-05** `::test_job_retry_leaves_duplicate_in_dead_PY_12_05`
- status diagram (push→PENDING→complete/fail→dead-letter) — `n/a` (prose; mechanism covered by the fail/dead-letter tests in S7)

## S7 — Automatic Retry and Dead Letters
> Signed off: 2026-06-25 · tina4-python 3.13.47 · CLI 3.8.51 · file backend (S7's only per-backend caveat: `retry_backoff` "applies to the file backend"). Tests: `test_ch12_queue_retry_deadletter_s7.py`.

- `max_retries=3` → attempted 3 times → dead-letter — `✓` `::test_max_retries_three_then_dead_letter`
- `max_retries` default is 3 — `✓` `::test_default_max_retries_is_three`
- `failed()` lists still-retrying jobs as plain dicts (0 < attempts < max) — `✓` `::test_failed_returns_retrying_jobs_as_dicts`
- `dead_letters()` returns Job objects with id/payload/attempts/error — `✓` `::test_dead_letters_returns_job_objects_with_fields`
- `retry(job_id)` re-queues one specific dead job — `✓` `::test_retry_by_id_requeues_one_specific`
- `retry_failed()` callable, returns a count — `✓` `::test_retry_failed_is_callable_and_returns_count`
- `retry_backoff` holds the re-enqueued job, then releases (file backend) — `✓` `::test_retry_backoff_holds_then_releases`
- `size("pending")` / `purge("pending")` — `✓` `::test_size_and_purge_pending`
- `size("dead")` / `purge("dead")` — `✓` `::test_size_and_purge_dead`
- `retry()` (no arg) re-queues only ONE, not "every" dead-letter job — `⚠` **divergence PY-12-04** `::test_retry_noarg_requeues_only_one_not_every_PY_12_04`
- `size("failed")` returns 0 while `failed()` lists the job — `⚠` **divergence PY-12-06** `::test_size_failed_zero_while_failed_lists_it_PY_12_06`

> Note: S6/S7 here are the **file-backend verbatim section impl** (the documented default/reference). The broker behaviour for the same ops is in the backend coverage matrix below (PY-12-03). New file-backend divergences PY-12-04/05/06 are distinct from the broker findings.

---

## Backend coverage matrix — documented ops × backend
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51 · live Docker brokers (`rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`). Re-confirmed 2026-06-25 · 3.13.47 via the live showcase below.

> **Live browser showcase (USER-requested) — `GET /queue/backends`** (`src/routes/queue_backend_matrix.py`, linked from the Chapter-12 page). Runs **30 operations — almost the entire public Queue+Job API surface an average user would touch** — against ALL FOUR live backends on each load and renders a per-claim grid (works / documented-diff / diverges / blocked). Documented (S3–S10) ops: push, pop+complete, produce/consume, drain(poll_interval=0), iterations, **continuous consume() worker loop**, **consume(job_id)**, priority, delay, size('pending'/'dead'/'failed'), purge('pending'/'dead'), fail→retry→dead-letter, failed(), dead_letters(), retry()/retry-all/retry(job_id), retry_backoff, reject(), job.retry(). Extended public API (not shown in Ch12) ops: **process(handler)**, **pop_batch()**, **pop_by_id()**, **consume(batch_size=)**, **clear()**, **get_topic()**, **job.to_json()**. **Kafka included exhaustively** (the deterministic pytest matrix excludes it for flakiness; the showcase runs it live with per-op daemon-thread timeouts so its non-delivery shows honestly rather than hanging). Verified 2026-06-25 · 3.13.47 with all 4 brokers up — tallies: **file 27 pass / 3 diverge** (PY-12-04 retry-not-every, PY-12-05 job.retry duplicate, PY-12-06 size('failed')), **RabbitMQ 16 pass / 3 doc-diff / 10 diverge / 1 n-a**, **MongoDB 18 pass / 1 doc-diff / 11 diverge** (incl. `clear()` on a fresh queue → AttributeError, BH-52), **Kafka 4 pass / 26 diverge**. New finding this pass: **PY-12-07** — `consume(job_id=)` (documented S4) yields nothing on any broker because `pop_by_id()` is hardcoded file-only. This grid is the visual proof of the S2 "work identically" claim per backend.

> **Deferred (not average-user, undocumented):** the `Queue(visibility_timeout=)` constructor param (reservation reclaim of unacked jobs) is NOT exercised — it is absent from Chapter 12 and is an advanced setting a doc-following user would not reach for. It is a candidate for a separate probe because it may interact with S6:240 ("call neither complete()/fail() → claimed on pop, will not be retried"). Also not exercised: the `max_retries=` override params on `dead_letters()/purge()/retry_failed()`, `produce(delay_until=)`, `retry(delay_seconds=)`, and `job.to_hash()/to_array()` (aliases of the covered `to_json()`).

Every documented operation a Chapter-12 reader would typically reach for, exercised
against each live backend. `✓` works as documented · `≈` works (documented broker
difference) · `✗` diverges (logged finding) · `~` partial. Tests:
`test_ch12_queue_backend_parity.py`, `test_ch12_queue_backend_lifecycle.py`,
`test_ch12_queue_kafka_semantics.py`.

| Operation (doc) | file | RabbitMQ | MongoDB | Kafka |
|---|---|---|---|---|
| push / pop / `complete()` (S3/S4) | `✓` | `✓` | `✓` | `~` patient consumer only (PY-12-02) |
| `consume(poll_interval=0)` drain (S4) | `✓` | `✓` | `✓` | `✗` empty — consumer not joined (PY-12-02) |
| `consume(iterations=N)` (S4) | `✓` | `✓` | `✓` | `✓` (long-poll, patient by nature) |
| cross-topic `produce()`/`consume()` (S10) | `✓` | `✓` | `✓` | `✗` timing |
| priority ordering (S5) | `✓` | `≈` FIFO (S5:208 disclaimer) | `✓` honors it | `✗` timing |
| `delay_seconds` hidden (S3) | `✓` | `≈` not honored (S3:107) | `≈` not honored (S3:107) | `≈` not honored |
| `size("pending")` (S3) | `✓` | `✓` (after settle) | `✓` | `✗` always 0 (PY-12-02) |
| fail → retry → dead-letter (S7) | `✓` | `✗` never dead-letters (PY-12-03) | `✓` | `✗` timing |
| `size("dead"/"failed")` (S7) | `✓` | `✗` always 0 (PY-12-03) | `✗` always 0 (PY-12-03) | `✗` always 0 |
| `dead_letters()` (S7) | `✓` | `✗` empty (attempts filter, PY-12-03) | `✓` | `✗` |
| `retry()` revive dead (S7) | `✓` | `✗` (PY-12-03) | `✗` (PY-12-03) | `✗` |
| `purge("pending")` returns count (S7) | `✓` | `~` returns `None` | `~` returns `None` | `~` returns `None` |
| `job.reject()` / `job.retry()` exist (S6) | `✓` | `✓` | `✓` | `✓` |

Net: file is the only backend that satisfies the full S3–S7 API as documented.
MongoDB is close (misses `size(status)`/`retry()`-revive). RabbitMQ transports fine
but its retry/dead-letter bookkeeping is broken (PY-12-03). Kafka diverges broadly
(PY-12-02). Drivers installed per S2: `pika` 1.4.1, `pymongo` 4.17.0,
`confluent-kafka` 2.14.2.

---

## Sections not yet started
S8 Queue in Route Handlers · S9 Switching Backends via .env · S10 Produce and Consume
Across Topics · S11 Exercise · S12 Solution · S13 Gotchas

> Note: the S10 *operations* are already exercised at the backend level (see the backend
> coverage matrix above — PY-12-03), but the file-backend **verbatim section impl** for
> the route-handler sections (S8) and the email-queue exercise/solution (S11/S12) is still
> pending. S6/S7 verbatim file-backend impl is now DONE (2026-06-25 · 3.13.47).

## Resolved items
- **S2 backend-parity** — DONE 2026-06-24 · 3.13.43. Stood up live Docker brokers (`rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`), installed `pika`/`pymongo`/`confluent-kafka` per S2, ran the identical documented code path against each. file / RabbitMQ / MongoDB satisfy the "work identically" claim; Kafka diverges (`size()`==0, immediate pop/drain empty) → **PY-12-02**. Tests: `test_ch12_queue_backend_parity.py` (3), `test_ch12_queue_kafka_semantics.py` (2).

## Open items
- **S4 continuous-poll** — the non-terminating `consume()` headline loop (sleep-when-empty + pick up mid-stream arrivals); needs a threaded/timeout harness.
- **Audit gaps (from the 2026-06-25 thoroughness audit; S2 thorough, S3–S7 minor-gaps):**
  - S3 — `priority` / `delay_seconds` "defaults to 0" (lines 105/107): default VALUE never asserted (only relied on indirectly).
  - S5 — priority-first via `consume()` never tested (only `pop()`); broker "stores the priority on each message" (line 208) sub-claim not verified (only delivery order checked).
  - S6 — `job.retry(delay_seconds=N)` arg never passed (only no-arg re-queue tested).
  - S7 — `purge("failed")` never called (named status, zero coverage); the "consume retries on its own" snippet (lines 250-261) only proven via manual pop+fail, never a real `consume()` loop.
- **Findings verification:** all 9 doc-fidelity findings adversarially confirmed REAL (16-agent workflow 2026-06-25); BH-52 confirmed correctly out-of-doc-scope (code bug, not doc divergence).
