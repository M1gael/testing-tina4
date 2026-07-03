# QA-audit test — Chapter 12 Queues, S13 "Gotchas".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S13, lines 587-635)
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. File backend (the documented
# default). Closes A6 — each gotcha's behavioural claim exercised. Gotcha 3
# (payload-too-large perf) and gotcha 5 (one-writer contention) are perf/concurrency
# advice with no deterministic unit test; their underlying MECHANISM is asserted
# and the perf claim is noted, not faked.
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    d = tempfile.mkdtemp(prefix="ch12_s13_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---- Gotcha 1: Always call complete or fail ---------------------------------

def test_gotcha1_pop_without_ack_is_neither_retried_nor_deadlettered(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S13 Gotcha 1 Always call complete or fail): "The job was claimed on pop, so
    it has already left the pending queue; without `fail()` it is neither retried
    nor dead-lettered."
    """
    queue = Queue(topic="emails")
    queue.push({"job": "a"})

    job = queue.pop()
    assert job is not None  # claimed on pop; deliberately no complete()/fail()

    assert queue.size() == 0, "left the pending queue"
    assert queue.pop() is None, "not retried"
    assert len(queue.dead_letters()) == 0, "not dead-lettered either"


# ---- Gotcha 2: Worker not picking up messages (topic mismatch) --------------

def test_gotcha2_topic_mismatch_yields_nothing_match_delivers(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S13 Gotcha 2 Worker not picking up messages): "Check that the topic name in
    `queue.push()` matches the topic name in `queue.consume()`."
    """
    Queue(topic="emails").push({"to": "a@b.com"})

    # Consuming a DIFFERENT topic yields nothing (the mismatch gotcha).
    wrong = [j for j in Queue(topic="reports").consume("reports", poll_interval=0)]
    assert wrong == [], "a mismatched topic name picks up nothing"

    # Consuming the MATCHING topic delivers it.
    seen = []
    for job in Queue(topic="emails").consume("emails", poll_interval=0):
        seen.append(job.payload["to"])
        job.complete()
    assert seen == ["a@b.com"], "the matching topic name delivers the job"


# ---- Gotcha 3: Payload too large (mechanism: JSON-serialized + stored) -------

def test_gotcha3_payload_is_json_serialized_and_stored(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S13 Gotcha 3 Payload too large): "The payload is serialized to JSON and
    stored in the backend. Very large payloads slow down the queue."

    The perf claim is not deterministically unit-testable; the MECHANISM is: a
    (large) payload is JSON-serialized, stored, and round-trips intact. Asserts
    the mechanism with a deliberately large payload.
    """
    big = {"blob": "x" * 200_000, "n": 7}
    queue = Queue(topic="emails")
    queue.push(big)

    job = queue.pop()
    assert job is not None
    assert job.payload == big, "the large payload is stored and round-trips via JSON"
    job.complete()


# ---- Gotcha 4: Dead letters pile up (monitor + clear) -----------------------

def test_gotcha4_dead_letters_are_monitorable_and_purgeable(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S13 Gotcha 4 Dead letters pile up): "Monitor dead letters with
    `queue.dead_letters()` or `queue.size("dead")`. ... call `queue.retry()` to
    revive them or `queue.purge("dead")` to clear them."

    Asserts the monitoring surface (`dead_letters()` and `size("dead")` both
    report the dead job) and that `purge("dead")` clears the store. (The
    `queue.retry()` revive path is the separate PY-12-04 divergence — revives only
    one of N — and is asserted in the S7 sentinel, not here.)
    """
    queue = Queue(topic="emails", max_retries=1)
    queue.push({"to": "bad@example.com"})
    queue.pop().fail("SMTP connection refused")  # -> dead

    assert len(queue.dead_letters()) == 1, "dead_letters() surfaces it"
    assert queue.size("dead") == 1, "size('dead') surfaces it"

    queue.purge("dead")
    assert queue.size("dead") == 0 and len(queue.dead_letters()) == 0, (
        "purge('dead') clears the dead-letter store"
    )


# ---- Gotcha 5: File backend for production (switch via env) -----------------

def test_gotcha5_switch_off_file_backend_via_env(tmp_queue_path, monkeypatch):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S13 Gotcha 5 File backend for production): "For production with multiple
    workers, switch to RabbitMQ, Kafka, or MongoDB via the
    `TINA4_QUEUE_BACKEND` environment variable."

    The "one writer at a time" contention is a concurrency property with no
    deterministic unit test; the documented REMEDY is the env switch — assert it
    selects a non-file backend with no code change. (Selection only — no broker
    contacted; delivery is in the matrix.)
    """
    assert type(Queue(topic="emails")._backend).__name__ == "LiteBackend"
    monkeypatch.setenv("TINA4_QUEUE_BACKEND", "rabbitmq")
    assert type(Queue(topic="emails")._backend).__name__ == "RabbitMQBackend", (
        "TINA4_QUEUE_BACKEND switches off the file backend for production"
    )


# ---- Gotcha 6: Environment-specific topic collision (prefix isolates) -------

def test_gotcha6_topic_prefix_isolates_environments(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S13 Gotcha 6 Environment-specific topic collision): "prefix topic names with
    the environment: `Queue(topic="dev_emails")`."

    A prefixed topic is an isolated store — a job on `dev_emails` is invisible to
    `emails` (and vice-versa), so two environments do not process each other's
    messages.
    """
    Queue(topic="dev_emails").push({"env": "dev"})
    Queue(topic="emails").push({"env": "prod"})

    assert Queue(topic="dev_emails").size() == 1
    assert Queue(topic="emails").size() == 1

    dev = [j.payload["env"] for j in Queue(topic="dev_emails").consume("dev_emails", poll_interval=0)]
    assert dev == ["dev"], "the dev-prefixed topic only yields dev jobs"
