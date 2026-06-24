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

---

## Backend coverage matrix — documented ops × backend
> Signed off: 2026-06-24 · tina4-python 3.13.43 · CLI 3.8.51 · live Docker brokers (`rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`)

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
S6 Job Lifecycle · S7 Automatic Retry and Dead Letters · S8 Queue in Route Handlers ·
S9 Switching Backends via .env · S10 Produce and Consume Across Topics · S11 Exercise ·
S12 Solution · S13 Gotchas

> Note: the S6/S7/S10 *operations* are already exercised at the backend level (see the
> backend coverage matrix above — PY-12-03), but their file-backend **verbatim section
> impl** (route handlers, the email-queue exercise/solution) is still pending.

## Resolved items
- **S2 backend-parity** — DONE 2026-06-24 · 3.13.43. Stood up live Docker brokers (`rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`), installed `pika`/`pymongo`/`confluent-kafka` per S2, ran the identical documented code path against each. file / RabbitMQ / MongoDB satisfy the "work identically" claim; Kafka diverges (`size()`==0, immediate pop/drain empty) → **PY-12-02**. Tests: `test_ch12_queue_backend_parity.py` (3), `test_ch12_queue_kafka_semantics.py` (2).

## Open items
- **S4 continuous-poll** — the non-terminating `consume()` headline loop; needs a threaded/timeout harness.
