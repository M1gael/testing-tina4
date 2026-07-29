# QA-audit test — Chapter 12 Queues, S10 "Produce and Consume Across Topics".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S10, lines 426-444)
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S10 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
# File backend (the documented default). Closes A3.
import shutil
import tempfile
import threading
import time

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    d = tempfile.mkdtemp(prefix="ch12_s10_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_produce_onto_a_topic_then_consume_it(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S10 Produce and Consume Across Topics): the verbatim example —
    `queue = Queue(topic="default")`, `queue.produce("emails", {...})`, then
    `for job in queue.consume("emails"): process(job); job.complete()` — plus
    "The `produce()` method pushes a job onto any named topic. The `consume()`
    method yields available jobs from a topic as a generator."
    """
    queue = Queue(topic="default")
    queue.produce("emails", {"to": "alice@example.com", "subject": "Hello"})

    seen = []
    for job in queue.consume("emails", poll_interval=0):  # drain-once
        seen.append(job.payload)
        job.complete()

    assert seen == [{"to": "alice@example.com", "subject": "Hello"}], (
        "produce() lands the job on the named topic and consume() yields it"
    )


def test_produced_job_does_not_land_on_the_construction_topic(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S10): "The `produce()` method pushes a job onto any named topic."

    Cross-topic isolation: producing onto "emails" must not enqueue anything on
    the queue's own "default" topic.
    """
    queue = Queue(topic="default")
    queue.produce("emails", {"to": "alice@example.com", "subject": "Hello"})

    assert queue.size() == 0, "the default topic stays empty"
    assert Queue(topic="emails").size() == 1, "the job is on the emails topic"


def test_consume_targets_the_named_topic_only(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S10): "The `consume()` method yields available jobs from a topic."

    Producing onto two topics and consuming one drains only that topic.
    """
    queue = Queue(topic="default")
    queue.produce("emails", {"n": 1})
    queue.produce("reports", {"n": 2})

    drained = []
    for job in queue.consume("emails", poll_interval=0):
        drained.append(job.payload["n"])
        job.complete()

    assert drained == [1], "only the emails topic was consumed"
    assert Queue(topic="reports").size() == 1, "the reports topic is untouched"


# ---- DIVERGENCE sentinel: PY-12-11 verbatim snippet hangs --------------------
# The three tests above use `poll_interval=0` (a drain-once adaptation) so they
# can assert and terminate. That kwarg is NOT in the S10 snippet — the verbatim
# example omits it, and with the default poll_interval=1.0 the loop never returns.
# This sentinel records that divergence honestly instead of letting poll_interval=0
# silently mask it.

def test_verbatim_s10_consume_snippet_does_not_terminate_PY_12_11(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S10 Produce and Consume Across Topics): the verbatim example
    `for job in queue.consume("emails"): process(job); job.complete()` — NO
    poll_interval.

    DIVERGENCE (PY-12-11): consume() defaults to poll_interval=1.0, a long-running
    generator that never returns once the topic empties. The verbatim S10 snippet
    therefore processes the produced job and then hangs forever — a reader who
    copies it into a script never gets control back. S4 (lines 147-153) teaches
    poll_interval=0 to "drain the queue once and stop"; S10 omits it. Sentinel runs
    the verbatim snippet in a daemon thread and asserts it does NOT terminate after
    draining; it flips when S10 shows poll_interval=0 (or the snippet otherwise
    stops).
    """
    queue = Queue(topic="default")
    queue.produce("emails", {"to": "alice@example.com", "subject": "Hello"})

    seen = []
    returned = threading.Event()

    def worker():
        for job in queue.consume("emails"):  # verbatim S10 — no poll_interval
            seen.append(job.payload)
            job.complete()
        returned.set()  # only reached if the generator actually returns

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    time.sleep(2.0)  # drain the one job, then spin past a full poll cycle (1.0s)

    assert seen == [{"to": "alice@example.com", "subject": "Hello"}], (
        "the produced job is consumed"
    )
    assert not returned.is_set(), (
        "PY-12-11: the verbatim consume() snippet did NOT terminate after draining"
    )
    assert t.is_alive(), "PY-12-11: the loop is still running (it hangs a reader script)"
