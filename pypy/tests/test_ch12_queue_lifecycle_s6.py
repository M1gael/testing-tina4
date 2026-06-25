# QA-audit test — Chapter 12 Queues, S6 "Job Lifecycle".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S6 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
# File backend (the documented default) throughout — S6 documents no per-backend
# caveat, so the file backend IS the reference behaviour.
#
# Most claims hold on the file backend (green). One DIVERGENCE found while
# implementing S6 verbatim is captured as a labelled sentinel (asserts the actual
# behaviour + cites the contradicted line; flips when the framework converges):
#   * PY-12-05 — job.retry() re-queues to pending but leaves the dead-letter copy,
#     so the same job ends up in BOTH pending and dead (duplicate delivery).
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"


@pytest.fixture
def tmp_queue_path(monkeypatch):
    """Isolate the file backend in a throwaway dir so each test is independent
    and never pollutes the workspace data/queue tree."""
    d = tempfile.mkdtemp(prefix="ch12_s6_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---- complete(): terminal -----------------------------------------------------

def test_complete_is_terminal_job_removed(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "job.complete() -- mark the job as done. Terminal: the job
    is removed and never comes back."
    """
    queue = Queue(topic="emails")
    queue.push({"job": "a"})

    job = queue.pop()
    job.complete()

    assert queue.size() == 0, "completed job is removed"
    assert queue.pop() is None, "it never comes back"


# ---- fail(): increments attempts, re-enqueues --------------------------------

def test_fail_increments_attempts_and_reenqueues(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "job.fail(reason) -- record a failed attempt. Increments
    attempts and either re-enqueues the job or dead-letters it."
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"job": "a"})

    queue.pop().fail("boom")
    assert queue.size() == 1, "a failed job under the retry limit is re-enqueued"

    job = queue.pop()
    assert job.attempts == 1, "fail() incremented attempts"


# ---- reject(): alias for fail ------------------------------------------------

def test_reject_is_alias_for_fail(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "job.reject(reason) -- alias for fail."
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"job": "a"})

    queue.pop().reject("nope")
    assert queue.size() == 1, "reject() re-enqueues like fail() under the limit"
    assert queue.pop().attempts == 1, "reject() increments attempts like fail()"


# ---- retry(): manual re-queue, bypasses the retry limit ----------------------

def test_job_retry_requeues_bypassing_limit(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "job.retry(delay_seconds=0) -- manually re-queue the job,
    optionally after a delay. Bypasses the retry limit."

    A job that has exhausted max_retries (dead-lettered) is manually re-queued by
    calling job.retry() on it — it returns to pending despite the limit.
    """
    queue = Queue(topic="emails", max_retries=1)
    queue.push({"job": "a"})
    queue.pop().fail("boom")  # max_retries=1 -> dead-lettered on the first fail
    assert queue.size() == 0 and len(queue.dead_letters()) == 1

    dead = queue.dead_letters()[0]
    dead.retry()  # bypasses the retry limit
    assert queue.size() == 1, "the dead job is manually re-queued to pending"


# ---- payload / id / attempts / error fields ----------------------------------

def test_job_exposes_payload_id_attempts_error(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "Read the payload with job.payload. The fields job.id,
    job.attempts, and job.error are also available."
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"to": "a@b.com"})

    queue.pop().fail("smtp down")
    job = queue.pop()

    assert job.payload == {"to": "a@b.com"}, "job.payload round-trips"
    assert isinstance(job.id, str) and job.id, "job.id is available"
    assert job.attempts == 1, "job.attempts is available"
    assert job.error == "smtp down", "job.error carries the last failure reason"


# ---- claimed-on-pop: neither complete nor fail -> not retried -----------------

def test_pop_without_ack_is_not_retried(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "Always call complete() or fail(). If you call neither, the
    job has already left the queue (it was claimed on pop) and will not be
    retried."
    """
    queue = Queue(topic="emails")
    queue.push({"job": "a"})

    job = queue.pop()
    assert job is not None
    # deliberately call neither complete() nor fail()

    assert queue.size() == 0, "the job already left the queue (claimed on pop)"
    assert queue.pop() is None, "it will not be retried"


# ---- DIVERGENCE sentinel: PY-12-05 job.retry() duplicates --------------------

def test_job_retry_leaves_duplicate_in_dead_PY_12_05(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S6 Job Methods): "job.retry(delay_seconds=0) -- manually re-queue the job".

    DIVERGENCE (PY-12-05): on the file backend, calling job.retry() on a
    dead-letter Job re-queues it to pending but does NOT remove the dead-letter
    copy — the SAME job id then exists in BOTH pending and dead_letters(), so it
    will be delivered again from pending while still counted dead. "Re-queue"
    implies a move, not a copy. Sentinel asserts the duplicate; it flips when
    job.retry() removes the dead-letter entry.
    """
    queue = Queue(topic="emails", max_retries=1)
    queue.push({"job": "dup"})
    queue.pop().fail("boom")  # dead-lettered

    dead = queue.dead_letters()[0]
    dead_id = dead.id
    dead.retry()

    revived = queue.pop()
    still_dead_ids = [j.id for j in queue.dead_letters()]
    # Documented intent: re-queued (move). Actual: duplicated (pending AND dead).
    assert revived is not None and revived.id == dead_id
    assert dead_id in still_dead_ids, "PY-12-05: dead-letter copy was NOT removed"
