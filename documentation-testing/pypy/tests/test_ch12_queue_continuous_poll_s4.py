# QA-audit test — Chapter 12 Queues, S4 the continuous-poll headline loop.
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S4 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
#
# Closes audit gap B2: the existing S4 tests cover poll_interval=0 (drain),
# iterations=, job_id= and pop(). They do NOT exercise the HEADLINE loop —
# `for job in queue.consume("emails"):` with no arguments — whose documented
# contract is "It polls the queue continuously and sleeps when empty, so you need
# no outer loop" and "This loop runs forever, processing jobs as they arrive."
# That requires a threaded/timeout harness: run the forever-loop in a thread,
# prove it (a) does not terminate or busy-yield while the queue is empty, and
# (b) picks up jobs pushed AFTER it started. The loop is stopped from outside via
# a sentinel "stop" job so the test never hangs. The default poll_interval is 1.0
# (verified in queue/__init__.py consume()), so waits below are sized around it.
import shutil
import tempfile
import threading
import time

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    d = tempfile.mkdtemp(prefix="ch12_s4poll_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _wait_until(predicate, timeout, interval=0.05):
    """Poll predicate() until true or timeout (seconds). Returns the final bool."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_consume_runs_forever_sleeps_empty_picks_up_arrivals(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S4 The consume Pattern): "It polls the queue continuously and sleeps when
    empty, so you need no outer loop." and "This loop runs forever, processing
    jobs as they arrive."

    Harness: the verbatim headline loop `for job in queue.consume("emails"):`
    runs in a background thread. While the queue is empty it must stay alive and
    yield nothing (sleeps when empty — it neither returns nor spins out a job).
    Jobs pushed after it started must be delivered (processed as they arrive). A
    sentinel "stop" job breaks the loop so the thread terminates cleanly.
    """
    queue = Queue(topic="emails")
    seen = []
    error = []

    def worker():
        try:
            # Verbatim headline loop — no poll_interval/iterations (default poll).
            for job in queue.consume("emails"):
                payload = job.payload
                job.complete()
                if payload.get("stop"):
                    break
                seen.append(payload["to"])
        except Exception as exc:  # surface a worker crash to the test thread
            error.append(repr(exc))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    # (a) Empty queue: the loop must keep running and yield nothing. Wait past a
    # full default poll cycle (1.0s) so a busy-spin or premature return surfaces.
    time.sleep(1.5)
    assert t.is_alive(), "consume() must run forever, not return on an empty queue"
    assert seen == [], "nothing pushed yet -> the loop slept when empty, no yields"

    # (b) Push a job AFTER the consumer started — it must be picked up.
    queue.push({"to": "first@x.com"})
    assert _wait_until(lambda: "first@x.com" in seen, timeout=3.0), (
        "a job pushed mid-stream is processed as it arrives"
    )

    # (b cont.) A second mid-stream arrival is also picked up by the same loop.
    queue.push({"to": "second@x.com"})
    assert _wait_until(lambda: "second@x.com" in seen, timeout=3.0), (
        "the loop keeps processing further arrivals without an outer loop"
    )

    # Stop the forever-loop from outside and confirm it terminates.
    queue.push({"stop": True})
    t.join(timeout=3.0)
    assert not t.is_alive(), "the loop exits once the sentinel stop job is handled"
    assert error == [], f"consumer thread raised: {error}"
    assert seen == ["first@x.com", "second@x.com"], "every mid-stream job seen, in order"
