# Probe — covers the S2/S9 "work identically" claim for file / RabbitMQ / MongoDB.
# Stands up real brokers (Docker: rabbitmq:3, mongo:7) and runs the IDENTICAL
# documented code path against each backend, asserting push/pop/consume/size behave
# as Chapter 12 documents. Broker-gated: a backend whose broker is unreachable is
# SKIPPED (a logged blocker per Protocol rule 9 — not rigged green). Kafka does NOT
# satisfy the claim — its divergence is in test_ch12_queue_kafka_semantics.py (PY-12-02).
import os
import socket
import sys
import tempfile

import pytest

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"


@pytest.fixture(autouse=True)
def _restore_env():
    """These tests mutate os.environ to switch backends; restore it afterward so the
    backend-selecting vars (TINA4_QUEUE_URL etc.) never leak into other ch12 tests."""
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _fresh_queue():
    """Reimport tina4_python.queue so the backend is re-resolved from the current env."""
    for m in [m for m in list(sys.modules) if m.startswith("tina4_python.queue")]:
        del sys.modules[m]
    import tina4_python.queue as q  # noqa: PLC0415
    return q.Queue


def _set_env(env: dict):
    for k in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS", "TINA4_QUEUE_PATH"):
        os.environ.pop(k, None)
    os.environ.update(env)


# name -> (is-the-broker-up?, backend env)
BACKENDS = {
    "file": (lambda: True, {"TINA4_QUEUE_BACKEND": "file"}),
    "rabbitmq": (
        lambda: _reachable("localhost", 5672),
        {"TINA4_QUEUE_BACKEND": "rabbitmq", "TINA4_QUEUE_URL": "amqp://guest:guest@localhost:5672"},
    ),
    "mongodb": (
        lambda: _reachable("localhost", 27017),
        {"TINA4_QUEUE_BACKEND": "mongodb", "TINA4_QUEUE_URL": "mongodb://localhost:27017/tina4"},
    ),
}


@pytest.mark.parametrize("name", list(BACKENDS))
def test_backend_round_trip_matches_doc(name):
    """DOC S2 (12-queues.md:70): "your code stays the same. The Queue class, push, pop,
    and consume work identically whether the backend is file, RabbitMQ, Kafka, or
    MongoDB." + S9 (:422): "The same queue.push() and queue.consume() calls work with
    every backend." Runs the identical documented code on each backend and asserts the
    same observable results. Verified for file / RabbitMQ / MongoDB (Kafka diverges —
    PY-12-02, see test_ch12_queue_kafka_semantics.py)."""
    gate, env = BACKENDS[name]
    if not gate():
        pytest.skip(f"{name} broker unreachable — logged blocker per rule 9, not run here")
    if name == "file":
        env = {**env, "TINA4_QUEUE_PATH": tempfile.mkdtemp(prefix="q_parity_")}
    _set_env(env)
    Queue = _fresh_queue()

    topic = f"parity_{name}"
    q = Queue(topic=topic)
    q.purge("pending")  # S7 (:329): queue.purge("pending") — start from a clean slate

    # S3 (:82-87): push returns a message id; payload is any JSON-serialisable dict.
    mid = q.push({"to": "alice@example.com", "subject": "Order Confirmation"})
    assert isinstance(mid, str) and mid, f"{name}: push did not return a message id"

    # S4 (:178): manual pop returns the highest-priority job; payload is the pushed dict.
    job = q.pop()
    assert job is not None, f"{name}: pop() returned None after a push"
    assert job.payload["to"] == "alice@example.com", f"{name}: payload not round-tripped"
    job.complete()

    # S4 (:150): consume(poll_interval=0) drains the queue once and stops when empty.
    q.produce(topic, {"n": 1})
    q.produce(topic, {"n": 2})
    drained = []
    for j in q.consume(topic, poll_interval=0):
        drained.append(j.payload["n"])
        j.complete()
        if len(drained) >= 5:
            break
    assert drained == [1, 2], f"{name}: drain-once did not yield the two produced jobs"

    # S3 (:120-124): size() reports how many pending messages remain — 0 after draining.
    assert q.size() == 0, f"{name}: size() not 0 after draining"
