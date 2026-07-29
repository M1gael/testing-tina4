# Probe — covers PY-12-02 (Kafka half). Chapter 12's S2/S9 "work identically" claim
# does NOT hold for Kafka. These sentinels assert the ACTUAL divergent behavior and
# cite the doc lines they contradict; each flips red if Kafka ever converges to the
# documented behavior (regression guard, per PY-12-01 precedent).
# Broker-gated: skipped when no Kafka broker is reachable (a logged blocker, not rigged).
#
# Re-verified on tina4-python 3.13.47 (2026-06-25): the maintainer's 3.13.44 Kafka
# connector fix (queue_backends/kafka_backend.py dequeue assignment-wait, bounded by
# TINA4_KAFKA_ASSIGN_TIMEOUT, default 15s) changed the SYMPTOM (dequeue now blocks for
# the assignment window instead of failing fast) but NOT the outcome: a freshly-pushed
# message still drains to [] because a fresh consumer joins at the latest offset, after
# the push. Verified deterministic 5/5 across independent processes on a unique topic.
# size() is still hardcoded 0. Both halves of PY-12-02 still reproduce.
#
# The drain sentinel uses a UNIQUE topic per run + a short assign timeout: on a SHARED
# fixed topic it was flaky (old retained messages from prior runs + a warmed consumer
# occasionally got assigned and read them, so drain returned non-empty) — that was a
# test artifact, not a fix. A unique topic isolates the documented push-then-drain.
import os
import socket
import sys

import pytest

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable("localhost", 9092),
    reason="Kafka broker unreachable — logged blocker per rule 9, not run here",
)


@pytest.fixture(autouse=True)
def _restore_env():
    """Restore os.environ after each test so the kafka backend vars never leak into
    other ch12 tests (the file/config sentinels assume a clean env)."""
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)


_COUNTER = [0]


def _uid() -> str:
    _COUNTER[0] += 1
    return f"{os.getpid()}_{_COUNTER[0]}"


def _kafka_queue(topic: str):
    for m in [m for m in list(sys.modules) if m.startswith("tina4_python.queue")]:
        del sys.modules[m]
    for k in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS",
              "TINA4_QUEUE_PATH", "TINA4_KAFKA_ASSIGN_TIMEOUT"):
        os.environ.pop(k, None)
    # Short assign timeout only for test speed — the drain-once outcome ([]) is identical
    # at the 15s default (verified 5/5 on 3.13.47); this just avoids a 15s wait per run.
    os.environ.update({"TINA4_QUEUE_BACKEND": "kafka", "TINA4_KAFKA_BROKERS": "localhost:9092",
                       "TINA4_KAFKA_ASSIGN_TIMEOUT": "3"})
    import tina4_python.queue as q  # noqa: PLC0415
    return q.Queue(topic=topic)


def test_kafka_size_always_zero_contradicts_s3():
    """DOC S3 (12-queues.md:120-124): "Check how many pending messages are in the queue:
    count = queue.size()". DIVERGENCE (PY-12-02): on Kafka, size() is hardcoded to
    return 0 (queue_backends/kafka_backend.py:123-126 — Kafka has no queue-depth
    concept), so it never reflects pending messages. Asserts the divergence; flips if
    Kafka size() becomes real."""
    q = _kafka_queue("kafka_size_probe")
    q.push({"n": 1})
    q.push({"n": 2})
    q.push({"n": 3})
    # Documented to report the pending count (3); actual is a hardcoded 0.
    assert q.size() == 0


def test_kafka_drain_once_delivers_nothing_contradicts_s2_s4():
    """DOC S2 (:70) "push, pop, and consume work identically" + S4 (:147-153)
    consume(poll_interval=0) "To drain the queue once and stop when it is empty".
    DIVERGENCE (PY-12-02): a Kafka consumer joins its group at the latest offset, so a
    message pushed BEFORE the consumer is assigned is never delivered to it — drain-once
    yields nothing. On 3.13.47 the connector waits out the assignment window (default 15s)
    before returning, but the result is still []. Asserts drain-once is empty on Kafka;
    flips if it starts draining like the file/RabbitMQ/MongoDB backends.
    Unique topic per run so old retained messages can't leak in (see file header)."""
    topic = f"kafka_drain_probe_{_uid()}"
    q = _kafka_queue(topic)
    q.push({"n": 1})
    drained = [j.payload for j in q.consume(topic, poll_interval=0)]
    # Documented to drain [{"n": 1}]; actual is [] because the consumer isn't ready yet.
    assert drained == []


# NOTE — Kafka is NOT broken, only its IMMEDIATE pop/drain semantics diverge: a
# patient long-running consumer DOES eventually receive the message (manually verified
# 2026-06-24 on 3.13.43 — first delivery on poll attempt ~16, ~16s after push). That
# scoping fact lives in the PY-12-02 finding note; it is deliberately NOT a persistent
# test because the delivery latency (consumer-group join + earliest-offset rebalance)
# is non-deterministic and would make a timing-bound assertion flaky under suite load.
