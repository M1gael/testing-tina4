# QA-audit test — Chapter 12 Queues, S5 "Priority Ordering".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S5 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    d = tempfile.mkdtemp(prefix="ch12_s5_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---- the verbatim worked example --------------------------------------------

def test_priority_then_oldest_first(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S5 Priority Ordering): "They return the **highest-priority** available job
    first. When two jobs share the same priority, the **older** one wins." The
    verbatim worked example pops "urgent" -> "normal" -> "also normal"; the
    `priority=` argument is the S3 "Priority and Delay" claim: "`push` accepts
    two optional arguments ... `priority` defaults to `0`."
    """
    queue = Queue(topic="tasks")

    queue.push({"label": "normal"})                  # priority 0
    queue.push({"label": "urgent"}, priority=10)     # priority 10
    queue.push({"label": "also normal"})             # priority 0

    assert queue.pop().payload["label"] == "urgent"        # highest priority
    assert queue.pop().payload["label"] == "normal"        # oldest of the 0 pair
    assert queue.pop().payload["label"] == "also normal"


# ---- delayed jobs stay hidden regardless of priority ------------------------

def test_delayed_high_priority_job_stays_hidden(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S5 Priority Ordering): "A delayed job (pushed with `delay_seconds`) stays
    hidden until its time arrives, regardless of priority."

    A far-future, high-priority delayed job must not jump ahead of an
    immediately-available normal job — and must not be returned at all yet.
    """
    queue = Queue(topic="tasks")

    queue.push({"label": "delayed-vip"}, priority=99, delay_seconds=60)
    queue.push({"label": "ready"})  # priority 0, immediately available

    first = queue.pop()
    assert first is not None
    assert first.payload["label"] == "ready", (
        "the delayed high-priority job must stay hidden behind the ready one"
    )

    assert queue.pop() is None, "the delayed job is still hidden, so nothing left"
    assert queue.size() == 1, "the delayed job is still pending, just not visible yet"
