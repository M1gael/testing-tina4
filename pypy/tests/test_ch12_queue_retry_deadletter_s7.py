# QA-audit test — Chapter 12 Queues, S7 "Automatic Retry and Dead Letters".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S7 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
# File backend (the documented default) throughout — S7's only per-backend caveat
# is that retry_backoff "applies to the file backend", so the file backend IS the
# reference for everything else here.
#
# The documented happy path holds on the file backend (green). Two DIVERGENCES
# found while implementing S7 verbatim are captured as labelled sentinels (assert
# the actual behaviour + cite the contradicted line; flip when the framework
# converges):
#   * PY-12-04 — queue.retry() (no arg) re-queues only ONE dead-letter job, not
#     "every" one as documented.
#   * PY-12-06 — size("failed") returns 0 even while failed() lists a still-
#     retrying job, contradicting "size accepts a status: pending, failed, dead".
import shutil
import tempfile
import time

import pytest

from tina4_python.queue import Queue

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"


@pytest.fixture
def tmp_queue_path(monkeypatch):
    d = tempfile.mkdtemp(prefix="ch12_s7_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _fail_until_gone(queue, topic="emails", limit=10):
    """Pop+fail until the queue stops re-enqueuing (dead-lettered). Bounded so a
    backend that never dead-letters can't loop forever."""
    fails = 0
    for _ in range(limit):
        job = queue.pop()
        if job is None:
            break
        job.fail("boom")
        fails += 1
    return fails


# ---- How retry works: max_retries=3 -> 3 attempts -> dead letter -------------

def test_max_retries_three_then_dead_letter(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 How Retry Works): "With max_retries=3, a job that keeps failing is
    attempted 3 times. On the third failure it lands in dead letters."
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"job": "flaky"})

    fails = _fail_until_gone(queue)
    assert fails == 3, "attempted 3 times"
    assert len(queue.dead_letters()) == 1, "lands in dead letters"
    assert queue.size() == 0, "no longer pending"


def test_default_max_retries_is_three(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Configuring Max Retries): "The Queue constructor accepts max_retries
    (default: 3)."
    """
    queue = Queue(topic="emails")  # no max_retries -> default 3
    queue.push({"job": "x"})

    assert _fail_until_gone(queue) == 3, "default max_retries is 3"


# ---- Inspecting failed (retrying) jobs ---------------------------------------

def test_failed_returns_retrying_jobs_as_dicts(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Inspecting Failed and Dead Jobs): "Jobs that failed at least once but are
    still being retried (0 < attempts < max_retries) ... retrying = queue.failed()"
    and "failed() returns plain dicts."
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"job": "a"})

    queue.pop().fail("boom")  # attempts 1, 0 < 1 < 3 -> still retrying

    retrying = queue.failed()
    assert isinstance(retrying, list) and len(retrying) == 1
    assert isinstance(retrying[0], dict), "failed() returns plain dicts"


# ---- Inspecting dead jobs (Job objects + fields) -----------------------------

def test_dead_letters_returns_job_objects_with_fields(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Inspecting Failed and Dead Jobs): "dead_letters() returns Job objects, so
    you can iterate them like any other job" and the loop reads job.id /
    job.payload / job.attempts / job.error.
    """
    queue = Queue(topic="emails", max_retries=1)
    queue.push({"to": "bad@example.com"})

    queue.pop().fail("SMTP connection refused")  # max_retries=1 -> dead

    dead = queue.dead_letters()
    assert len(dead) == 1
    job = dead[0]
    assert job.payload == {"to": "bad@example.com"}
    assert isinstance(job.id, str) and job.id
    assert job.attempts >= 1
    assert job.error == "SMTP connection refused"


# ---- Reviving by id ----------------------------------------------------------

def test_retry_by_id_requeues_one_specific(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Reviving Dead Letters): "queue.retry(job_id) -- Re-queue one specific job
    by ID."
    """
    queue = Queue(topic="emails", max_retries=1)
    queue.push({"n": 1})
    queue.push({"n": 2})
    for _ in range(2):
        queue.pop().fail("boom")  # both dead

    target = queue.dead_letters()[0].id
    queue.retry(target)

    assert queue.size() == 1, "exactly one job revived to pending"
    assert len(queue.dead_letters()) == 1, "the other stays dead"


def test_retry_failed_is_callable_and_returns_count(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Reviving Dead Letters): "queue.retry_failed() -- Re-queue dead jobs that
    are still under the retry limit."

    The method exists and runs; it returns a count of jobs re-queued (0 when no
    dead-under-limit jobs exist — a failed-under-limit job is already pending via
    auto-retry).
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"job": "a"})
    queue.pop().fail("boom")  # failed, under the limit (already auto-re-enqueued)

    result = queue.retry_failed()
    assert isinstance(result, int), "retry_failed() returns a count"


# ---- Retry backoff holds the job ---------------------------------------------

def test_retry_backoff_holds_then_releases(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Retry Backoff): "each automatic re-enqueue holds the job for N seconds
    before it becomes available again. retry_backoff applies to the file backend."

    Verbatim example uses retry_backoff=30; the held-then-released SEMANTIC is
    identical at a shorter value, used here so the test is runnable.
    """
    queue = Queue(topic="emails", max_retries=5, retry_backoff=2)
    queue.push({"job": "a"})

    queue.pop().fail("boom")
    assert queue.pop() is None, "the re-enqueued job is held during the backoff"

    time.sleep(2.3)
    job = queue.pop()
    assert job is not None, "after the backoff the job becomes available again"


# ---- Counting and purging by status ------------------------------------------

def test_size_and_purge_pending(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Counting and Purging by Status): "queue.size("pending") # jobs waiting to
    be processed" and "queue.purge("pending") # drop everything still waiting".
    """
    queue = Queue(topic="emails")
    queue.push({"n": 1})
    queue.push({"n": 2})

    assert queue.size("pending") == 2
    queue.purge("pending")
    assert queue.size("pending") == 0, "purge('pending') drops waiting jobs"


def test_size_and_purge_dead(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Counting and Purging by Status): "queue.size("dead") # dead-letter jobs"
    and "queue.purge("dead") # clear the dead-letter store".
    """
    queue = Queue(topic="emails", max_retries=1)
    queue.push({"n": 1})
    queue.pop().fail("boom")  # dead

    assert queue.size("dead") == 1
    queue.purge("dead")
    assert queue.size("dead") == 0, "purge('dead') clears the dead-letter store"
    assert len(queue.dead_letters()) == 0


# ---- DIVERGENCE sentinel: PY-12-04 retry() revives only one ------------------

def test_retry_noarg_requeues_only_one_not_every_PY_12_04(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Reviving Dead Letters): "queue.retry() -- Re-queue every dead-letter job."

    DIVERGENCE (PY-12-04): on the file backend, the no-argument queue.retry()
    re-queues only ONE dead-letter job per call, leaving the rest dead — it does
    not re-queue "every" dead-letter job. Sentinel asserts only one is revived
    from three; it flips when retry() revives them all.
    """
    queue = Queue(topic="emails", max_retries=1)
    for n in range(3):
        queue.push({"n": n})
    for _ in range(3):
        queue.pop().fail("boom")  # 3 dead
    assert len(queue.dead_letters()) == 3

    queue.retry()  # documented: re-queue EVERY dead-letter job

    # Documented intent: pending 3, dead 0. Actual: only one revived.
    assert queue.size("pending") == 1, "PY-12-04: retry() revived only one"
    assert len(queue.dead_letters()) == 2, "PY-12-04: the other two stay dead"


# ---- DIVERGENCE sentinel: PY-12-06 size('failed') ----------------------------

def test_size_failed_zero_while_failed_lists_it_PY_12_06(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S7 Counting and Purging by Status): "size and purge accept a status:
    pending, failed, or dead." + (S7 Inspecting) failed() lists still-retrying
    jobs.

    DIVERGENCE (PY-12-06): on the file backend, after a fail under the retry
    limit, failed() returns the job (1) but size("failed") returns 0 — the
    documented "failed" status is not counted by size(), even though failed()
    reports it. Sentinel asserts the mismatch; it flips when size("failed")
    matches failed().
    """
    queue = Queue(topic="emails", max_retries=3)
    queue.push({"job": "a"})
    queue.pop().fail("boom")  # attempts 1, still retrying -> in failed()

    assert len(queue.failed()) == 1, "failed() lists the retrying job"
    assert queue.size("failed") == 0, "PY-12-06: size('failed') does not count it"
