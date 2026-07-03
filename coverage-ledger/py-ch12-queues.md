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
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51 · (first exercised 2026-06-23 · 3.13.39) · B1 gap closed 2026-06-26 · 3.13.47 · CLI 3.8.52

- create queue + `push()` returns a message id — `✓` `test_ch12_queue_create_push.py::test_push_returns_a_message_id`
- "the `topic` argument names the queue" — `✓` `::test_topic_argument_names_the_queue`
- "the payload is any dictionary that can be serialized to JSON" — `✓` `::test_payload_is_any_json_serializable_dict`
- `produce()` pushes to a named topic — `✓` `::test_produce_pushes_to_a_named_topic`
- `size()` reflects pending count — `✓` `::test_size_reflects_pending_count`
- `push(priority=)` — `✓` (via S5 `test_priority_then_oldest_first`)
- `push(delay_seconds=)` — `✓` (via S5 `test_delayed_high_priority_job_stays_hidden`)
- "`priority` defaults to `0`" (default VALUE) — `✓` `test_ch12_queue_defaults_s3.py::test_priority_defaults_to_zero_value` + `::test_noarg_priority_equals_explicit_zero` (B1, 2026-06-26 · 3.13.47)
- "`delay_seconds` defaults to `0`" (default VALUE) — `✓` `::test_delay_seconds_defaults_to_zero_value` + `::test_noarg_delay_is_immediately_poppable` (B1, 2026-06-26 · 3.13.47)
- blockquote: backend "selected via environment variables, not constructor parameters" — `✓` **divergence PY-12-01** `::test_s2_backend_is_a_constructor_param_py_12_01`
- blockquote: kafka/mongo as env-selected backend values — `✓` exercised in S2 backend-parity (`test_ch12_queue_backend_parity.py` + `test_ch12_queue_kafka_semantics.py`)

## S4 — Consuming Messages
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51

- `consume(poll_interval=0)` drains once and stops — `✓` `test_ch12_queue_consume.py::test_consume_poll_interval_zero_drains_once_and_stops`
- `consume(iterations=N)` stops after N jobs — `✓` `::test_consume_iterations_stops_after_n`
- `consume(job_id=)` yields one job once, then returns — `✓` `::test_consume_job_id_yields_that_job_once`
- `pop()` returns the highest-priority job, or `None` when empty — `✓` `::test_pop_returns_a_job_then_none_when_empty`
- `job.complete()` removes / `job.fail()` re-enqueues under the retry limit — `✓` `::test_complete_removes_fail_reenqueues`
- continuous-poll headline `consume()` (default `poll_interval`, sleeps-when-empty, never returns) — `✓` `test_ch12_queue_continuous_poll_s4.py::test_consume_runs_forever_sleeps_empty_picks_up_arrivals` (threaded/timeout harness, B2, 2026-06-26 · 3.13.47)

## S5 — Priority Ordering
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51 · B3 gap closed 2026-06-26 · 3.13.47 · CLI 3.8.52

- highest-priority first; ties break oldest-first (verbatim example) — `✓` `test_ch12_queue_priority.py::test_priority_then_oldest_first`
- "pop AND consume return highest-priority first" — consume() half — `✓` `::test_consume_returns_highest_priority_first` (B3, 2026-06-26 · 3.13.47)
- a delayed job stays hidden until its time arrives, regardless of priority — `✓` `::test_delayed_high_priority_job_stays_hidden`
- "priority ordering is enforced by the file backend" — `✓` (covered by the tests above, file backend)
- "external brokers … follow their own delivery semantics" — `✓` exercised in the backend matrix below (RabbitMQ = FIFO, MongoDB honors priority — both consistent with the disclaimer)
- "external brokers store the priority on each message" (line 208) — `✓` **VERIFIED 2026-06-29 · 3.13.47 · CLI 3.8.53 (D3 closed, live Docker brokers)**: push `priority=7` + `priority=0` → each message carries its priority. RabbitMQ + MongoDB round-trip `job.priority` via `pop()`; Kafka stores it on the raw record (`{"payload":…,"priority":7,…}`, read directly since PY-12-02 delays framework delivery). `test_ch12_queue_broker_priority_s5.py` (3 pass). Delivery ORDER not asserted (doc disclaims it). FAITHFUL — no finding.

## S6 — Job Lifecycle
> Signed off: 2026-06-25 · tina4-python 3.13.47 · CLI 3.8.51 · file backend (S6 documents no per-backend caveat). Tests: `test_ch12_queue_lifecycle_s6.py`. · B4 gap closed 2026-06-26 · 3.13.47 · CLI 3.8.52 · AUD-12-L retry()-default gap closed 2026-07-02 · 3.13.48 · CLI 3.8.53

- `job.complete()` terminal — removed, never comes back — `✓` `::test_complete_is_terminal_job_removed`
- `job.fail(reason)` increments `attempts` + re-enqueues under the limit — `✓` `::test_fail_increments_attempts_and_reenqueues`
- `job.reject(reason)` is an alias for `fail()` — `✓` `::test_reject_is_alias_for_fail`
- `job.retry(delay_seconds=0)` manually re-queues, bypassing the retry limit — `✓` (re-queue itself) `::test_job_retry_requeues_bypassing_limit`
- `job.retry(delay_seconds=N)` — the "optionally after a delay" arg holds then releases — `✓` `::test_job_retry_delay_seconds_holds_then_releases` (B4, 2026-06-26 · 3.13.47)
- `job.retry()` default `delay_seconds=0` — no hold, immediately poppable — `✓` `::test_job_retry_default_no_delay_is_immediately_poppable` (AUD-12-L, 2026-07-02 · 3.13.48)
- `job.payload` / `job.id` / `job.attempts` / `job.error` available — `✓` `::test_job_exposes_payload_id_attempts_error`
- "call neither complete()/fail() → claimed on pop, not retried" — `✓` `::test_pop_without_ack_is_not_retried`
- `job.retry()` leaves a dead-letter **duplicate** (same id in pending AND dead) — `⚠` **divergence PY-12-05** `::test_job_retry_leaves_duplicate_in_dead_PY_12_05`
- status diagram (push→PENDING→complete/fail→dead-letter) — `n/a` (prose; mechanism covered by the fail/dead-letter tests in S7)

## S7 — Automatic Retry and Dead Letters
> Signed off: 2026-06-25 · tina4-python 3.13.47 · CLI 3.8.51 · file backend (S7's only per-backend caveat: `retry_backoff` "applies to the file backend"). Tests: `test_ch12_queue_retry_deadletter_s7.py`. · B5 gap closed 2026-06-26 · 3.13.47 · CLI 3.8.52 (new finding PY-12-08) · AUD-12-3 + AUD-12-L gaps closed 2026-07-02 · 3.13.48 · CLI 3.8.53 (no new findings)

- `max_retries=3` → attempted 3 times → dead-letter — `✓` `::test_max_retries_three_then_dead_letter`
- `max_retries` default is 3 — `✓` `::test_default_max_retries_is_three`
- `failed()` lists still-retrying jobs as plain dicts (0 < attempts < max) — `✓` `::test_failed_returns_retrying_jobs_as_dicts`
- `dead_letters()` returns Job objects with id/payload/attempts/error — `✓` `::test_dead_letters_returns_job_objects_with_fields`
- `retry(job_id)` re-queues one specific dead job — `✓` `::test_retry_by_id_requeues_one_specific`
- `retry_failed()` callable, returns a count — `✓` `::test_retry_failed_is_callable_and_returns_count`
- `retry_failed()` REAL re-queue behaviour — `✓` **FAITHFUL** `::test_retry_failed_requeues_dead_job_under_the_limit` + `::test_retry_failed_leaves_dead_jobs_at_the_limit` (AUD-12-3 closed 2026-07-02 · 3.13.48). The "dead AND still under the retry limit" state IS constructable — a job dead-letters under `max_retries=1`, then the queue is re-constructed with `max_retries=3` (operator raises the limit after investigating): `retry_failed()` re-queues it (count 1, back to pending, out of dead) and leaves at-limit jobs dead (count 0). No doc-claim ambiguity after all — the earlier tautology concern is resolved.
- `failed()` range `0 < attempts < max_retries` — BOTH exclusive bounds (attempts=0 not listed; attempts=max dead, not listed) — `✓` `::test_failed_excludes_both_range_boundaries` (AUD-12-L, 2026-07-02 · 3.13.48)
- "the next pop() … picks it up again" — same-job IDENTITY via pop() (not just count) — `✓` `::test_pop_redelivers_the_same_job_after_fail` (AUD-12-L, 2026-07-02 · 3.13.48)
- `retry_backoff` holds the re-enqueued job, then releases (file backend) — `✓` `::test_retry_backoff_holds_then_releases`
- `size("pending")` / `purge("pending")` — `✓` `::test_size_and_purge_pending`
- `size("dead")` / `purge("dead")` — `✓` `::test_size_and_purge_dead`
- "a normal consume loop retries failed jobs on its own. No manual retry_failed() needed" (lines 250-261) — real `consume()` loop, file backend — `✓` `::test_consume_loop_auto_retries_until_dead` (B5, 2026-06-26 · 3.13.47)
- `retry()` (no arg) re-queues only ONE, not "every" dead-letter job — `⚠` **divergence PY-12-04** `::test_retry_noarg_requeues_only_one_not_every_PY_12_04`
- `size("failed")` returns 0 while `failed()` lists the job — `⚠` **divergence PY-12-06** `::test_size_failed_zero_while_failed_lists_it_PY_12_06`
- `purge("failed")` clears the dead-letter store, not the `failed()` jobs — `⚠` **divergence PY-12-08** `::test_purge_failed_targets_dead_store_not_failed_jobs_PY_12_08` (B5, 2026-06-26 · 3.13.47)

> Note: S6/S7 here are the **file-backend verbatim section impl** (the documented default/reference). The broker behaviour for the same ops is in the backend coverage matrix below (PY-12-03). New file-backend divergences PY-12-04/05/06 are distinct from the broker findings.

## S8 — Queue in Route Handlers
> Signed off: 2026-06-26 · tina4-python 3.13.47 · CLI 3.8.52 · implemented + SERVED (`tina4 serve`, port 7146). Impl: `src/routes/ch12_orders.py` (verbatim). Served `curl` runs recorded this session. · AUD-12-1 closed 2026-07-02 · 3.13.48 · CLI 3.8.53 (persisted in-process route sentinel)

- `@post("/api/orders")` pushes order_confirmation onto "emails" — `✓` served: POST→201, emails topic grew by 1
- `queue.produce("invoices", {...})` onto a different topic — `✓` served: `data/queue/invoices` job = `{order_id:101, format:pdf}`
- `queue.produce("warehouse_sync", {...})` onto a different topic — `✓` served: job = `{order_id:101, items:[…]}`
- "the user gets an instant response" — returns `{"message":"Order created","order_id":101}`, 201 — `✓` served
- POST route reachable without auth — `⚠` **divergence PY-12-10** served: 401 without a Bearer token; 201 with one (handler correct, chapter shows no token). Live demo: `GET /chapter/12` S8.
- persisted route sentinel — `✓` `test_ch12_orders_route_s8.py` (2 tests, AUD-12-1 closed 2026-07-02 · 3.13.48): in-process `tina4_python.test` client drives the registered handler — exact fan-out payloads on all 3 topics, instant-201 body while all jobs still PENDING, 1:1 fan-out per request. (Client bypasses the Bearer gate — PY-06-13 mechanics — so this pins the HANDLER; the served 401 stays PY-12-10.)

## S9 — Switching Backends via .env
> Signed off: 2026-06-26 · tina4-python 3.13.47 · CLI 3.8.52. Impl/test: `test_ch12_queue_env_backends_s9.py`. Selection only (no broker contacted).

- `TINA4_QUEUE_BACKEND` selects file→LiteBackend, rabbitmq→RabbitMQBackend, kafka→KafkaBackend, mongodb→MongoBackend (same `Queue()` call, no code change) — `✓` `::test_backend_selected_purely_by_env_var` (5 params)
- `TINA4_QUEUE_PATH` redirects the file backend storage dir — `✓` `::test_queue_path_env_redirects_file_storage`
- `TINA4_KAFKA_BROKERS` (comma-separated) is the kafka knob — `✓` `::test_kafka_brokers_env_is_accepted_for_kafka`
- `TINA4_QUEUE_URL` is its own knob (rabbitmq adapter constructed FROM the URL's host/port/credentials; selection-not-delivery, disclosed white-box) — `✓` `::test_queue_url_env_is_the_broker_connection_knob` (AUD-12-L, 2026-07-02 · 3.13.48)
- env-var table rendered live — `✓` `GET /chapter/12` S9 (all 4 mappings execute)

## S10 — Produce and Consume Across Topics
> Signed off: 2026-06-26 · tina4-python 3.13.47 · CLI 3.8.52 · file backend. Impl/test: `test_ch12_queue_cross_topic_s10.py`.

- `Queue(topic="default").produce("emails", …)` then `consume("emails")` yields it — `✓` `::test_produce_onto_a_topic_then_consume_it`
- produced job does not land on the construction topic — `✓` `::test_produced_job_does_not_land_on_the_construction_topic`
- `consume()` targets the named topic only — `✓` `::test_consume_targets_the_named_topic_only`
- verbatim S10 snippet (`for job in queue.consume("emails")`, no `poll_interval`) terminates — `⚠` **divergence PY-12-11** `::test_verbatim_s10_consume_snippet_does_not_terminate_PY_12_11` (default `poll_interval=1.0` → never returns; hangs a reader script; the 3 tests above use `poll_interval=0` drain-adaptation, now disclosed not masked)
- live demo — `✓` `GET /chapter/12` S10

## S11/S12 — Exercise: Build an Email Queue + Solution
> Signed off: 2026-06-26 · tina4-python 3.13.47 · CLI 3.8.52 · implemented + SERVED. Impl: `src/routes/email_queue.py` (verbatim 4 endpoints) + `src/workers/_email_worker.py` (verbatim body; `_`-prefixed — see PY-12-09). Worker logic test: `test_ch12_email_worker_s12.py`. · AUD-12-2 closed 2026-07-02 · 3.13.48 · CLI 3.8.53 (persisted endpoint sentinels incl. the 400 branch)

- `POST /api/emails/send` validates to/subject/body, queues, returns 201 + message_id — `✓` served: 201 `{message_id}`; missing fields → 400 `{"errors":[…]}`
- `GET /api/emails/queue` returns pending count — `✓` served: `{"pending":N}` 200
- `GET /api/emails/dead` lists dead letters — `✓` served: `{"dead_letters":[…],"count":N}` 200
- `POST /api/emails/retry` revives dead letters — `✓` served: 200 (revive extent is PY-12-04)
- persisted endpoint sentinels — `✓` `test_ch12_email_routes_s12.py` (6 tests, AUD-12-2 closed 2026-07-02 · 3.13.48): 201 + `message_id` == queued job id; 400 branch BOTH ways (one missing field → exactly that error; empty payload → all three, handler order); `{"pending": N}` count; dead item carries id/payload/attempts=3/error; retry endpoint revives the (single) dead letter — constructed with exactly 1 dead so the documented outcome and retry()'s one-per-call actual (PY-12-04) coincide, disclosed not masked.
- worker: good mail completed, `bad@example.com` dead-lettered after 3 attempts — `✓` `::test_worker_dead_letters_bad_address_after_three_attempts`
- worker at the documented `src/workers/email_worker.py` path — `⚠` **divergence PY-12-09** auto-discover imports its infinite consume loop → `tina4 serve` hangs at boot. Probe `test_ch12_worker_autodiscover_probe.py` (2).
- S8/S11/S12 POST routes + S11 `curl` block need auth — `⚠` **divergence PY-12-10** (see S8)
- live demo — `✓` `GET /chapter/12` S12 (worker logic; surfaces PY-12-09/PY-12-10 notes)

## S13 — Gotchas
> Signed off: 2026-06-26 · tina4-python 3.13.47 · CLI 3.8.52 · file backend. Test: `test_ch12_gotchas_s13.py`.

- Gotcha 1 — claimed-on-pop without ack is neither retried nor dead-lettered — `✓` `::test_gotcha1_pop_without_ack_is_neither_retried_nor_deadlettered`
- Gotcha 2 — push topic must match consume topic — `✓` `::test_gotcha2_topic_mismatch_yields_nothing_match_delivers`
- Gotcha 3 — payload JSON-serialized + stored (mechanism; perf claim is prose) — `✓` `::test_gotcha3_payload_is_json_serialized_and_stored`
- Gotcha 4 — monitor (`dead_letters()`/`size("dead")`) + clear (`purge("dead")`) — `✓` `::test_gotcha4_dead_letters_are_monitorable_and_purgeable`
- Gotcha 5 — switch off the file backend via env (one-writer contention is prose) — `✓` `::test_gotcha5_switch_off_file_backend_via_env`
- Gotcha 6 — env-prefixed topics are isolated stores — `✓` `::test_gotcha6_topic_prefix_isolates_environments`
- live demos (gotchas 2/4/6) — `✓` `GET /chapter/12` S13

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

## Resolved items
- **S2 backend-parity** — DONE 2026-06-24 · 3.13.43. Stood up live Docker brokers (`rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`), installed `pika`/`pymongo`/`confluent-kafka` per S2, ran the identical documented code path against each. file / RabbitMQ / MongoDB satisfy the "work identically" claim; Kafka diverges (`size()`==0, immediate pop/drain empty) → **PY-12-02**. Tests: `test_ch12_queue_backend_parity.py` (3), `test_ch12_queue_kafka_semantics.py` (2).

## Open items
- **Audit gaps B1–B5 — CLOSED 2026-06-26 · 3.13.47 (file backend, pytest; 29 B-gap tests pass ×1):**
  - ✓ B1/S3 — `priority` / `delay_seconds` "defaults to 0" (lines 105/107) asserted by VALUE (stored job), by behaviour, and no-arg≡explicit-0 (`test_ch12_queue_defaults_s3.py`, 4 tests).
  - ✓ B2/S4 — the non-terminating headline `for job in queue.consume("emails"):` loop exercised in a threaded/timeout harness: stays alive + yields nothing while empty (sleeps), picks up mid-stream arrivals in order, stops on a sentinel job (`test_ch12_queue_continuous_poll_s4.py`, 1 test).
  - ✓ B3/S5 — priority-first via `consume()` (drain) asserted `urgent→normal→also normal` (`test_ch12_queue_priority.py::test_consume_returns_highest_priority_first`).
  - ✓ B4/S6 — `job.retry(delay_seconds=2)` held-then-released asserted (`test_ch12_queue_lifecycle_s6.py::test_job_retry_delay_seconds_holds_then_releases`).
  - ✓ B5/S7 — real `consume()` loop auto-retries the same job to dead-letter with no `retry_failed()` call (`::test_consume_loop_auto_retries_until_dead`); `purge("failed")` exercised → **new finding PY-12-08** (`::test_purge_failed_targets_dead_store_not_failed_jobs_PY_12_08`).
- **✓ D3 CLOSED 2026-06-29 · 3.13.47 · CLI 3.8.53 (live Docker brokers):** S5 broker "stores the priority on each message" (line 208) sub-claim — **VERIFIED FAITHFUL** on RabbitMQ + MongoDB + Kafka. Pushed `priority=7` and `priority=0`; each message carries its own priority — RabbitMQ/MongoDB via `job.priority` round-trip through `pop()`, Kafka via the raw stored record (`kafka_backend.py:29` serializes `{"payload","priority","attempts"}` into the message; confirmed by reading the topic directly, since PY-12-02 delays framework delivery). Delivery ORDER deliberately not asserted (doc disclaims it). `test_ch12_queue_broker_priority_s5.py` (3 pass). No finding — last open Ch12 coverage item is now closed.
- **Sections S8–S13 — DONE 2026-06-26 · 3.13.47 (implemented verbatim + served):** S8 route (`ch12_orders.py`), S9 env table, S10 cross-topic, S11/S12 email-queue endpoints + worker (`email_queue.py` + `_email_worker.py`), S13 gotchas. All sign-offs above. Full ch12 suite 71 passed / 23 skipped. Explorer extended to S8/S9/S10/S12/S13.
- **Findings verification:** 9 doc-fidelity findings adversarially confirmed REAL (16-agent workflow 2026-06-25); BH-52 confirmed correctly out-of-doc-scope (code bug, not doc divergence). **PY-12-08, PY-12-09, PY-12-10, PY-12-11 (all 2026-06-26) — FILED on #144 2026-06-26 (batched comment, with PY-12-01). PY-12-09 (conf 0.90) + PY-12-10 (conf 0.97) ADVERSARIALLY RE-CONFIRMED 2026-06-26 (workflow `ch12-s8-s13-reverify`, source+doc verified, not refuted); impls confirmed byte-verbatim, retest 71 passed/0 failed. PY-12-11 (S10 verbatim consume() hangs a reader script) NEWLY FOUND by that workflow's completeness critic — it also caught that the earlier S10 test masked the hang via `poll_interval=0`; fixed by adding the PY-12-11 sentinel. PY-12-08 sibling of PY-12-06 (status-taxonomy root). PY-12-03 FILED on #144 2026-07-02 (re-verified on 3.13.49 first, live brokers) — every Ch12 finding is now filed. Note (test fidelity): `test_ch12_queue_env_backends_s9.py` asserts internal `_backend` class names — defensible as a SELECTION check (no broker to test delivery; docstrings already scope it to selection-not-delivery), flagged by the workflow as white-box.**

### Audit coverage gaps — ✓ ALL CLOSED 2026-07-02 · tina4-python 3.13.48 · CLI 3.8.53 (from the 2026-06-30 fidelity audit; no new findings — every gap verified FAITHFUL)
- **✓ AUD-12-1** — S8 `POST /api/orders` fan-out + instant-201: persisted in-process route sentinel `test_ch12_orders_route_s8.py` (2 tests). Exact payloads on all 3 topics, 201 body while jobs still pending, 1:1 fan-out per request. (Test client bypasses the Bearer gate — served 401 stays PY-12-10.)
- **✓ AUD-12-2** — S11/S12 four email endpoints + 400 branch: persisted sentinels `test_ch12_email_routes_s12.py` (6 tests) — 201+`message_id`, 400 one-missing + all-missing, pending count, dead-item fields, retry revive (1-dead construction; extent divergence stays PY-12-04).
- **✓ AUD-12-3** — S7 `retry_failed()` real behaviour VERIFIED FAITHFUL: `::test_retry_failed_requeues_dead_job_under_the_limit` + `::test_retry_failed_leaves_dead_jobs_at_the_limit` in the S7 file. The "dead AND under the limit" state is constructable by re-constructing the queue with a raised `max_retries` — no doc-claim ambiguity; the tautology concern is resolved. The S7 ✓ no longer overstates.
- **✓ AUD-12-L** — all four LOW items: `failed()` both exclusive bounds (S7 file), pop()-path same-id re-delivery (S7 file), `job.retry()` default no-hold poppability (S6 file), `TINA4_QUEUE_URL` as its own knob (S9 file).
- Runs: new tests green ×2 (deterministic); full ch12 sweep 86 passed / 26 skipped (broker-gated skips — brokers down).
