# Probe — covers PY-12-02 (Kafka half). Chapter 12's S2/S9 "work identically" claim
# does NOT hold for Kafka on tina4-python 3.13.43. These sentinels assert the ACTUAL
# divergent behavior and cite the doc lines they contradict; each flips red if Kafka
# ever converges to the documented behavior (regression guard, per PY-12-01 precedent).
# Broker-gated: skipped when no Kafka broker is reachable (a logged blocker, not rigged).
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


def _kafka_queue(topic: str):
    for m in [m for m in list(sys.modules) if m.startswith("tina4_python.queue")]:
        del sys.modules[m]
    for k in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS", "TINA4_QUEUE_PATH"):
        os.environ.pop(k, None)
    os.environ.update({"TINA4_QUEUE_BACKEND": "kafka", "TINA4_KAFKA_BROKERS": "localhost:9092"})
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
    DIVERGENCE (PY-12-02): a Kafka consumer must join its group and be assigned the
    partition before poll() returns, which does not happen within the single poll a
    drain-once does — so an immediate drain yields nothing (first delivery is ~16s
    later via a long-running consume()). Asserts drain-once is empty on Kafka; flips
    if it starts draining like the file/RabbitMQ/MongoDB backends."""
    q = _kafka_queue("kafka_drain_probe")
    q.push({"n": 1})
    drained = [j.payload for j in q.consume("kafka_drain_probe", poll_interval=0)]
    # Documented to drain [{"n": 1}]; actual is [] because the consumer isn't ready yet.
    assert drained == []


# NOTE — Kafka is NOT broken, only its IMMEDIATE pop/drain semantics diverge: a
# patient long-running consumer DOES eventually receive the message (manually verified
# 2026-06-24 on 3.13.43 — first delivery on poll attempt ~16, ~16s after push). That
# scoping fact lives in the PY-12-02 finding note; it is deliberately NOT a persistent
# test because the delivery latency (consumer-group join + earliest-offset rebalance)
# is non-deterministic and would make a timing-bound assertion flaky under suite load.
