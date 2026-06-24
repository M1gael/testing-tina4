# QA-audit test — Chapter 12 Queues, S4 "Consuming Messages".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S4 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    """Isolate the file backend in a throwaway dir so each test is independent
    and never pollutes the workspace data/queue tree."""
    d = tempfile.mkdtemp(prefix="ch12_s4_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---- consume: drain once with poll_interval=0 -------------------------------

def test_consume_poll_interval_zero_drains_once_and_stops(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S4 Consuming Messages): "To drain the queue once and stop when it is empty,
    pass `poll_interval=0`:"

    The generator must terminate, not loop forever.
    """
    queue = Queue(topic="emails")
    for i in range(3):
        queue.push({"to": f"u{i}@x.com", "subject": "s", "body": "b"})

    seen = []
    for job in queue.consume("emails", poll_interval=0):
        seen.append(job.payload["to"])
        job.complete()

    assert len(seen) == 3, "drain-once should yield every pending job then stop"
    assert queue.size() == 0, "completed jobs are removed"


# ---- consume: iterations cap ------------------------------------------------

def test_consume_iterations_stops_after_n(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S4 Consuming Messages): "You can also stop after a fixed number of jobs with
    `iterations`:"
    """
    queue = Queue(topic="emails")
    for i in range(5):
        queue.push({"n": i})

    consumed = 0
    for job in queue.consume("emails", iterations=2):
        consumed += 1
        job.complete()

    assert consumed == 2, "iterations=2 must yield exactly two jobs"
    assert queue.size() == 3, "the remaining three stay pending"


# ---- consume: single job by id ----------------------------------------------

def test_consume_job_id_yields_that_job_once(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S4 Consume a Single Job by ID): "Pass `job_id` to process one specific job.
    It yields that job once, then returns:"
    """
    queue = Queue(topic="emails")
    target = queue.push({"pick": "me"})
    queue.push({"pick": "not me"})

    seen = []
    for job in queue.consume("emails", job_id=target):
        seen.append(job.payload)
        job.complete()

    assert seen == [{"pick": "me"}], "only the targeted job is yielded, once"
    assert queue.size() == 1, "the other job is untouched"


# ---- manual pop -------------------------------------------------------------

def test_pop_returns_a_job_then_none_when_empty(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S4 Manual Pop): "`pop` returns the highest-priority available job, or `None`
    when the queue is empty."
    """
    queue = Queue(topic="emails")
    queue.push({"to": "a@b.com", "subject": "hi"})

    job = queue.pop()
    assert job is not None
    assert job.payload["to"] == "a@b.com"
    job.complete()

    assert queue.pop() is None, "an empty queue pops None"


# ---- complete vs fail -------------------------------------------------------

def test_complete_removes_fail_reenqueues(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S4 Consuming Messages): "Each job must be explicitly completed or failed".
    Re-enqueue-on-fail is the S6 Job Lifecycle claim: "job.fail() -> attempts +=
    1 ... attempts < max_retries -> re-enqueued -> PENDING".

    complete() removes the job; fail() (default max_retries) puts it back as
    pending for retry.
    """
    queue = Queue(topic="emails")
    queue.push({"job": "a"})

    job = queue.pop()
    job.fail("boom")
    assert queue.size() == 1, "a failed job under the retry limit is re-enqueued"

    job = queue.pop()
    job.complete()
    assert queue.size() == 0, "a completed job is removed"
