# Probe — covers PY-12-02 / PY-12-03: the FULL documented queue API surface a
# Chapter-12 reader would typically use (priority, delay, cross-topic, the
# fail/retry/dead-letter lifecycle, size/purge by status) exercised against EACH
# live backend. Each test encodes the ACTUAL per-backend outcome in an expectation
# map and cites the doc line it verifies; a map entry flips if the framework changes.
#
# Backends here: file / RabbitMQ / MongoDB (deterministic). Kafka is excluded from the
# lifecycle asserts because its consumer-group delivery latency makes them non-
# deterministic — Kafka is covered in test_ch12_queue_kafka_semantics.py (size()==0,
# drain-once empty) and the basic round-trip in test_ch12_queue_backend_parity.py.
#
# Broker-gated: a backend whose broker is unreachable is SKIPPED (a logged blocker per
# Protocol rule 9 — not rigged green). DOCUMENTED divergences (priority/delay on
# brokers, per S5:208 / S3:107) are asserted as such; UNDOCUMENTED divergences are
# asserted as sentinels tagged with the finding ID.
import os
import socket
import sys

import pytest

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"

_COUNTER = [0]


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

ALL = list(BACKENDS)


def _uid() -> str:
    _COUNTER[0] += 1
    return f"{os.getpid()}_{_COUNTER[0]}"


def _queue(name: str, **kw):
    """Build a Queue on `name`'s backend, skipping if its broker is down."""
    gate, env = BACKENDS[name]
    if not gate():
        pytest.skip(f"{name} broker unreachable — logged blocker per rule 9")
    for k in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS", "TINA4_QUEUE_PATH"):
        os.environ.pop(k, None)
    env = dict(env)
    if name == "file":
        import tempfile  # noqa: PLC0415
        env["TINA4_QUEUE_PATH"] = tempfile.mkdtemp(prefix="life_")
    os.environ.update(env)
    for m in [m for m in list(sys.modules) if m.startswith("tina4_python.queue")]:
        del sys.modules[m]
    import tina4_python.queue as q  # noqa: PLC0415
    return q.Queue(**kw)


# ── S5 priority — DOCUMENTED that brokers follow their own semantics ────────────
# file/MongoDB honor highest-priority-first; RabbitMQ is FIFO (default queue).
PRIORITY_FIRST = {"file": "urgent", "mongodb": "urgent", "rabbitmq": "normal"}


@pytest.mark.parametrize("name", ALL)
def test_priority_ordering(name):
    """DOC S5 (12-queues.md:201): pop returns "urgent" first (highest priority).
    S5 (:208) explicitly states external brokers "store the priority on each message
    but follow their own delivery semantics" — so RabbitMQ returning insert-order
    ("normal") is a DOCUMENTED divergence, not a bug; MongoDB happens to honor it."""
    q = _queue(name, topic=f"life_prio_{name}_{_uid()}")
    q.purge("pending")
    q.push({"l": "normal"})
    q.push({"l": "urgent"}, priority=10)
    q.push({"l": "also"})
    first = q.pop()
    val = first.payload["l"]
    first.complete()
    assert val == PRIORITY_FIRST[name]


# ── S3 delay_seconds — DOCUMENTED that brokers manage their own timing ──────────
DELAY_FIRST = {"file": "ready", "mongodb": "later", "rabbitmq": "later"}


@pytest.mark.parametrize("name", ALL)
def test_delay_seconds_hidden(name):
    """DOC S3 (:101-102): a job pushed with delay_seconds is held. S3 (:107):
    "External brokers (RabbitMQ, Kafka, MongoDB) manage their own delivery timing."
    So only the file backend hides the delayed job; brokers deliver it immediately —
    a DOCUMENTED divergence."""
    q = _queue(name, topic=f"life_delay_{name}_{_uid()}")
    q.purge("pending")
    q.push({"l": "later"}, delay_seconds=60)
    q.push({"l": "ready"})
    first = q.pop()
    val = first.payload["l"]
    first.complete()
    assert val == DELAY_FIRST[name]


# ── S10 cross-topic produce/consume — works on all three ───────────────────────
@pytest.mark.parametrize("name", ALL)
def test_cross_topic_produce_consume(name):
    """DOC S10 (:433-442): the SAME queue produces onto one topic and consumes from
    it — `queue.produce("emails", {...})` then `for job in queue.consume("emails")`.
    Works on file / RabbitMQ / MongoDB (one instance, matching the doc example)."""
    q = _queue(name, topic=f"life_main_{name}_{_uid()}")
    other = f"life_other_{name}_{_uid()}"
    q.produce(other, {"x": 1})
    drained = []
    for job in q.consume(other, poll_interval=0):  # S4 drain-once form
        drained.append(job.payload["x"])
        job.complete()
        if len(drained) >= 3:
            break
    assert drained == [1]


# ── S7 fail -> retry -> dead-letter — DIVERGES on RabbitMQ (PY-12-03) ───────────
# file/MongoDB: a job failed up to max_retries lands in dead_letters(). RabbitMQ:
# fail() requeues the ORIGINAL message body, so attempts never accumulate and the
# job NEVER dead-letters (dead_letters() stays empty / loops forever).
DEAD_AFTER_RETRIES = {"file": 1, "mongodb": 1, "rabbitmq": 0}


@pytest.mark.parametrize("name", ALL)
def test_fail_accumulates_to_dead_letter(name):
    """DOC S7 (:248): "Once attempts reaches max_retries, the job moves to the
    dead-letter store." + S7 (:299) dead_letters() yields the dead Job. DIVERGENCE
    (PY-12-03): RabbitMQ's job.fail() requeues the original body (attempts stay 0),
    so the job never reaches max_retries and never dead-letters — dead_letters()==0.
    file/MongoDB honor the documented mechanism."""
    q = _queue(name, topic=f"life_dead_{name}_{_uid()}", max_retries=2)
    q.purge("pending")
    q.push({"job": "flaky"})
    for _ in range(5):  # bounded — RabbitMQ would loop forever otherwise
        j = q.pop()
        if j is None:
            break
        j.fail("boom")
    assert len(q.dead_letters()) == DEAD_AFTER_RETRIES[name]
    q.purge("pending")  # drop RabbitMQ's perpetually-requeued job


# ── S7 size(status) — only the file backend supports non-pending statuses ───────
SIZE_DEAD = {"file": 1, "mongodb": 0, "rabbitmq": 0}


@pytest.mark.parametrize("name", ALL)
def test_size_by_status_dead(name):
    """DOC S7 (:323-326): size accepts a status — size("pending"), size("dead").
    DIVERGENCE (PY-12-03): RabbitMQ/MongoDB (and Kafka) implement size() for
    "pending" only and return 0 for "dead"/"failed", even when a dead letter exists
    (MongoDB's dead_letters() shows it but size("dead") is 0). Only the file backend
    counts by status."""
    q = _queue(name, topic=f"life_size_{name}_{_uid()}", max_retries=1)
    q.purge("pending")
    q.push({"x": 1})
    j = q.pop()
    if j:
        j.fail("boom")  # max_retries=1 -> first failure dead-letters
    assert q.size("dead") == SIZE_DEAD[name]


# ── S7 retry() revive — DIVERGES on RabbitMQ + MongoDB (PY-12-03) ──────────────
REVIVED_PENDING = {"file": 1, "mongodb": 0, "rabbitmq": 0}


@pytest.mark.parametrize("name", ALL)
def test_retry_revives_dead_letters(name):
    """DOC S7 (:310-312): queue.retry() "Re-queue every dead-letter job". DIVERGENCE
    (PY-12-03): only the file backend revives. MongoDB's retry_job() looks for
    status="failed" in the main topic, but dead letters live in a separate
    .dead_letter collection (status "dead") -> revives nothing; RabbitMQ's
    dead_letters() is empty (attempts filter) -> nothing to revive."""
    q = _queue(name, topic=f"life_revive_{name}_{_uid()}", max_retries=1)
    q.purge("pending")
    q.push({"x": 1})
    j = q.pop()
    if j:
        j.fail("boom")
    q.retry()  # documented to re-queue dead letters
    assert q.size("pending") == REVIVED_PENDING[name]
    q.purge("pending")


# ── S7 purge("pending") — return value differs (minor) ─────────────────────────
PURGE_RET = {"file": 2, "mongodb": None, "rabbitmq": None}


@pytest.mark.parametrize("name", ALL)
def test_purge_pending(name):
    """DOC S7 (:329): queue.purge("pending") "drop everything still waiting". All
    backends clear the queue (size()->0); only the file backend returns the count
    removed — brokers return None (minor; the doc shows no return value)."""
    q = _queue(name, topic=f"life_purge_{name}_{_uid()}")
    q.purge("pending")
    q.push({"x": 1})
    q.push({"x": 2})
    ret = q.purge("pending")
    assert ret == PURGE_RET[name]
    assert q.size() == 0


# ── S4 consume(job_id) — file-only via pop_by_id (PY-12-07) ─────────────────
# file yields the target job; every broker yields nothing because pop_by_id() is
# hardcoded LiteBackend-only.
CONSUME_BYID_YIELD = {"file": [{"pick": "me"}], "mongodb": [], "rabbitmq": []}


@pytest.mark.parametrize("name", ALL)
def test_consume_job_id_file_only(name):
    """DOC S4 (12-queues.md:163-171) "Consume a Single Job by ID ... Pass job_id
    to process one specific job. It yields that job once, then returns" — shown
    with NO backend caveat. DIVERGENCE (PY-12-07): consume(job_id=) routes through
    Queue.pop_by_id(), which is hardcoded file-only (`if not isinstance(
    self._backend, LiteBackend): return None`), so on every broker consume(job_id=)
    yields nothing. Sentinel: file yields the job, brokers yield []; flips when a
    broker delivers the targeted job."""
    q = _queue(name, topic=f"life_byid_{name}_{_uid()}")
    q.purge("pending")
    mid = q.push({"pick": "me"})
    q.push({"pick": "no"})
    got = [j.payload for j in q.consume(q.get_topic(), job_id=mid)]
    assert got == CONSUME_BYID_YIELD[name]
    q.purge("pending")
