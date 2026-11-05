# Kafka `latest` offset reset is ignored by the raw-protocol consumers

Ledger row: `f-queue-01`. Run 2026-11-02 against py `8fbc2254`, php `b367197f`, rb `50c5d2b`,
nd `44d433c` (each origin/v3, release 3.13.156), on real brokers apache/kafka 3.8.0 and 4.1.0
(single-node KRaft, podman).

## Issue

3.13.156 added `TINA4_KAFKA_AUTO_OFFSET_RESET` (then `KAFKA_AUTO_OFFSET_RESET`, default
`earliest`) so a new consumer can start at `latest` instead of replaying the retained backlog.
Only the paths that hand it to a real client library honour it. The zero-dependency
raw-protocol consumers resolve it and then start every topic at offset 0 anyway.

## Mechanism

- py raw fallback: `tina4_python/queue_backends/kafka_backend.py:165`
  `offset = self._offsets.get(topic, 0)`; the docstring at `:18-21` says so.
- php: `Tina4/Queue/KafkaBackend.php:258` `$offset = $this->offsets[$topic] ?? 0;`; the comment at
  `:103` says so.
- nd: `packages/core/src/queueBackends/kafkaBackend.ts:491` `buildFetchRequest(topic, 0)` in the child
  script: **every** `pop()` fetches offset 0 and returns the same first record forever. That is
  the ADR-0022 holding position: `Queue` refuses `backend: "kafka"` in Node (`queue.ts:258`), so
  only direct `KafkaBackend` use reaches it. Not fixed here; `latest` cannot mean anything until
  the backend keeps a position.
- py with confluent-kafka and rb (rdkafka) pass it to librdkafka and honour it.

Neither raw consumer commits group offsets, so for them every topic is "new" on its first
dequeue in a process. The fix: on that first dequeue, `latest` sends ListOffsets v1
(timestamp -1) and starts at the log end; `earliest` keeps the old start of 0 with no extra
request. A just-auto-created topic answers ListOffsets with 3 for ~100ms, so 3/5 is retried
(10 x 200ms, as produce does); without that, the first record produced onto a new topic was
skipped. Python also exempts `<topic>.dead_letter`, because its `dead_letters()`/`retry_job()`
enumerate the DLQ through `dequeue()`; php's `deadLetters()` sets its own position first.

## Probes

Each takes `<framework src root> <latest|earliest>` and reads `TINA4_KAFKA_BROKERS`.

| probe | what |
|---|---|
| `probe_py.py`, `probe_php.php`, `probe_rb.rb`, `probe_nd.mjs` | 3 old records, new consumer, 1 new record: does `latest` skip the old ones |
| `probe_py_deadletters.py` | a job already on the DLQ; does `dead_letters()` list it under `latest` |
| `probe_py_fresh_topic.py`, `probe_php_attacks.php` (A) | consumer starts before the topic exists; is the first record seen |
| `probe_php_attacks.php` (B) | php `deadLetters()` under `latest` |
| `probe_py_fresh_topic_confluent.py` | reference run of the fresh-topic case on confluent |

Python raw runs use a venv without confluent-kafka; confluent runs use one with it (2.16.1).

## Results, stock (origin/v3)

```
py[raw]       reset=latest   seen=['old-0','old-1','old-2','new']  FAIL (replayed backlog)
py[confluent] reset=latest   seen=[None,'new']                     PASS
php[raw]      reset=latest   seen=["old-0","old-1","old-2","new"]  FAIL (replayed backlog)
rb[rdkafka]   reset=latest   seen=[nil,"new"]                      PASS
nd[raw]       reset=latest   seen=["old-0" x7]                     FAIL (and earliest: also "old-0" x7, never advances)
py[confluent] reset=latest   dead_letters ids=[]                   FAIL (new sibling finding, see below)
earliest: PASS everywhere except nd.
```

## Results, fixed (fix/kafka-offset-reset-raw-path)

```
py[raw]  latest seen=[None,'new'] PASS   earliest seen=['old-0','old-1','old-2','new'] PASS
php[raw] latest seen=[null,"new"] PASS   earliest seen=["old-0","old-1","old-2","new"] PASS
py[raw]  latest fresh topic: list_offsets answers=[None, 0] seen=[None,'first'] PASS
         (first fix attempt, no retry: answers=[None, 1] seen=[None x5] FAIL)
php      latest fresh topic seen=[null,"first"] PASS; deadLetters=["dead-1"] PASS
py[raw]  latest dead_letters ids=['dead-1'] PASS
```

Same verdicts on Kafka 4.1.0 (stock still FAILs there).

## Sibling finding, not fixed here

py confluent path with `latest`: `Queue.dead_letters()` returns `[]` for a job already on the
dead-letter topic (stock, run). It reads the DLQ through the same consumer group, so `latest`
applies to the DLQ too. Ruby is immune: its `dead_letters` uses a reader group pinned to
`earliest`.
