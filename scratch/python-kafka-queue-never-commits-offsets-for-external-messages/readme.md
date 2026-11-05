# Python Kafka `Queue` never commits offsets for records it did not produce

Ledger row: `f-queue-05`. Upstream issue tina4-python #274. Run 2026-11-03 against py `ba84f43c`
(origin/v3, release 3.13.157), real broker apache/kafka 3.8.0 (single-node KRaft, podman, port 39092),
confluent-kafka 2.16.1. The raw-socket case used a venv without confluent-kafka.

## Issue

With confluent-kafka installed, a `Queue(backend="kafka")` consumer commits only when `job.complete()`,
`fail()`, `reject()` or `retry()` names a record it can find. It looks the record up by the payload's
top-level `id`. A record produced outside Tina4 (CDC, another service) has no `id`. It is popped as
job id `"unknown"` and never committed, so the group never advances and every restart replays the
topic. Two in-flight records that share a payload id use one slot, so acknowledging the first commits
past the second while it is still being processed.

## Mechanism

- `tina4_python/queue_backends/kafka_backend.py:160`: `dequeue()` stores the polled message in
  `_in_flight` only `if message.get("id") is not None`, keyed by that id.
- `:175`: `acknowledge()` pops `_in_flight[message_id]`. On a miss it commits nothing and raises
  nothing.
- `tina4_python/queue/kafka_backend.py:65`: `pop()` sets `job_id = result.get("id", "unknown")`, and
  every ack passes `str(job.id)`.

Sufficiency check (run): the same external producer, with a unique `id` added to each value,
commits 3 of 3. The id alone decides it.

Other ports: php's Kafka backend is raw protocol only and keeps offsets in process; it never commits
a group offset for any record. Ruby commits the consumer position whatever the payload. Node's
`Queue` refuses Kafka. None has this bug (read).

## Fix (`~/.cache/tina4-worktrees/q274-tina4-python.fix.patch`)

- The connector gets `dequeue_record(topic)`, which returns `(message, "topic:partition:offset")` and
  tracks the record under that key in `_in_flight_records`, whatever the payload holds.
- `acknowledge()` looks up the record key first, then the legacy payload id.
- `Queue` `pop()` uses `dequeue_record()`. The job id is the payload id when present, otherwise
  the record key (no more shared `"unknown"`). Every ack passes the record key, held on the job as
  `_kafka_record`.
- Public `dequeue()` is unchanged (payload-id tracking), so direct connector users and
  `dead_letters()`/`retry_job()` scans behave as before and add nothing to `_in_flight_records`.

## Probes

| probe | what |
|---|---|
| `probe.py` | A external complete x3, B Tina4 push complete x3 (control), C external fail, D two records with one payload id, ack only the first. Prints the group's committed offset |
| `probe_dlq.py` | external record reject()/fail() past max: dead-letter id, retry_job |
| `probe_raw.py` | raw-socket path: job ids of external records |
| `probe_pop_after_dead_letters.py` | separate defect, see below |

`stock.log` and `fixed.log` hold the output. On stock: A committed=-1001 (nothing), C -1001, D 2 (wants 1),
ids `unknown`. With the fix: A 3, C 1, D 1, ids `topic:0:N`. B passes on both.

## Regression tests (tests/test_queue_backends.py, TestKafkaJobLifecycleLive)

- `test_kafka_complete_commits_a_record_with_no_payload_id`
- `test_kafka_records_sharing_a_payload_id_commit_separately`

Both fail on stock and pass with the fix. Each piece gates on its own: the call site, record tracking
and the ack lookup each fail both tests; the job-id fallback fails the first; the `_record()` helper
fails the second. `tests/test_queue*.py`: same single failure on stock and fixed
(`test_the_guard_still_accepts_every_documented_backend_name`, pre-existing), in both venvs.

## Found along the way (separate row)

`probe_pop_after_dead_letters.py`: after `queue.dead_letters()` (or `retry(job_id)`), `pop()` no longer
reads the main topic. confluent `subscribe([dl_topic])` replaces the subscription, and the main
topic is still in `_subscribed_topics`, so it is never re-subscribed. Stock: `after_dead_letters=None`.
