# Probe — covers the S5 broker priority-storage claim (closes audit gap D3).
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S5, line 208)
#   "Priority ordering is enforced by the file backend. External brokers store the
#    priority on each message but follow their own delivery semantics."
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# The claim has two halves: (a) the file backend ENFORCES priority ordering — already
# covered by test_ch12_queue_priority.py; (b) external brokers STORE the priority on
# each message (delivery ORDER is explicitly NOT guaranteed — "their own delivery
# semantics"). This file verifies (b): push priority=7 and priority=0 to each broker
# and confirm the priority value is carried on each stored/delivered message.
#
# RabbitMQ / MongoDB: the framework round-trips priority — pop() and read job.priority.
# Kafka: the framework's drain-once does not deliver a freshly-pushed message (PY-12-02,
#   latest-offset + consumer-group join), so we read the RAW stored Kafka record directly
#   — which is exactly what "store the priority on each message" asserts.
#
# Broker-gated: a backend whose broker is unreachable is SKIPPED (logged blocker per
# Protocol rule 9 — not rigged green). Order is never asserted (the doc disclaims it).
import json
import os
import socket
import sys
import time

import pytest

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"


@pytest.fixture(autouse=True)
def _restore_env():
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
    for m in [m for m in list(sys.modules) if m.startswith("tina4_python.queue")]:
        del sys.modules[m]
    import tina4_python.queue as q  # noqa: PLC0415
    return q.Queue


def _set_env(env: dict):
    for k in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS", "TINA4_QUEUE_PATH"):
        os.environ.pop(k, None)
    os.environ.update(env)


# Framework-round-trip backends (immediate delivery): pop() exposes job.priority.
ROUNDTRIP_BACKENDS = {
    "rabbitmq": (
        lambda: _reachable("localhost", 5672),
        {"TINA4_QUEUE_BACKEND": "rabbitmq", "TINA4_QUEUE_URL": "amqp://guest:guest@localhost:5672"},
    ),
    "mongodb": (
        lambda: _reachable("localhost", 27017),
        {"TINA4_QUEUE_BACKEND": "mongodb", "TINA4_QUEUE_URL": "mongodb://localhost:27017/tina4"},
    ),
}


@pytest.mark.parametrize("name", list(ROUNDTRIP_BACKENDS))
def test_broker_stores_priority_on_each_message_roundtrip(name):
    """12-queues.md (S5, line 208): "External brokers store the priority on each
    message but follow their own delivery semantics."

    Push two messages with distinct priorities (7 and 0) and confirm each delivered
    message carries the priority it was pushed with. Delivery ORDER is NOT asserted —
    the doc says brokers "follow their own delivery semantics". Flips red if a broker
    drops the priority (job.priority would default to 0 for the priority=7 message).
    """
    gate, env = ROUNDTRIP_BACKENDS[name]
    if not gate():
        pytest.skip(f"{name} broker unreachable — logged blocker per rule 9, not run here")
    _set_env(env)
    Queue = _fresh_queue()

    topic = f"prio_s5_{name}_{os.getpid()}"
    q = Queue(topic=topic)
    try:
        q.purge("pending")
    except Exception:
        pass

    q.push({"label": "urgent"}, priority=7)
    q.push({"label": "normal"}, priority=0)

    # Drain both, mapping each delivered payload to the priority it carries.
    seen = {}
    deadline = time.time() + 15
    while len(seen) < 2 and time.time() < deadline:
        job = q.pop()
        if job is None:
            time.sleep(0.3)
            continue
        seen[job.payload["label"]] = job.priority
        job.complete()

    assert seen.get("urgent") == 7, (
        f"{name}: priority=7 not stored on the message (got {seen.get('urgent')!r})"
    )
    assert seen.get("normal") == 0, (
        f"{name}: priority=0 not stored on the message (got {seen.get('normal')!r})"
    )


def test_kafka_stores_priority_on_each_message_raw_record():
    """12-queues.md (S5, line 208): "External brokers store the priority on each
    message but follow their own delivery semantics."

    Kafka: the framework's drain-once does not deliver a just-pushed message (PY-12-02,
    latest-offset + consumer-group join), so the priority round-trip can't be observed
    via the framework here. Read the RAW stored record off the topic instead — "store
    the priority on each message" is precisely a claim about the stored record. A fresh
    unique topic is used so only this run's two records are read (no stale accumulation).
    """
    if not _reachable("localhost", 9092):
        pytest.skip("kafka broker unreachable — logged blocker per rule 9, not run here")
    pytest.importorskip("confluent_kafka", reason="confluent-kafka not installed")
    from confluent_kafka import Consumer

    _set_env({"TINA4_QUEUE_BACKEND": "kafka", "TINA4_KAFKA_BROKERS": "localhost:9092"})
    Queue = _fresh_queue()

    topic = f"prio_s5_kafka_{os.getpid()}_{int(time.time())}"
    q = Queue(topic=topic)
    q.push({"label": "urgent"}, priority=7)
    q.push({"label": "normal"}, priority=0)

    consumer = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": f"prio_s5_raw_{topic}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([topic])
    seen = {}
    deadline = time.time() + 30
    try:
        while len(seen) < 2 and time.time() < deadline:
            m = consumer.poll(1.0)
            if m is None or m.error():
                continue
            body = json.loads(m.value().decode("utf-8"))
            seen[body["payload"]["label"]] = body.get("priority")
    finally:
        consumer.close()

    assert seen.get("urgent") == 7, (
        f"kafka: priority=7 not stored on the raw record (got {seen.get('urgent')!r}); seen={seen}"
    )
    assert seen.get("normal") == 0, (
        f"kafka: priority=0 not stored on the raw record (got {seen.get('normal')!r}); seen={seen}"
    )
