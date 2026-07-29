# QA-audit test — Chapter 12 Queues, S12 "Solution" — the email worker's logic.
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S12, lines 552-583)
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. The verbatim worker
# (`src/workers/_email_worker.py`) is a top-level INFINITE consume() loop and
# cannot be imported/run directly (it never returns; see PY-12-09). This test runs
# the worker's documented LOGIC under a bounded drain harness — the ONLY changes
# from the verbatim body are: poll_interval=0 + a safety counter so the loop
# terminates, and the illustrative print()/time.sleep(1) "simulate sending" lines
# dropped (non-functional to the retry/dead-letter claim under test). The
# fail-on-bad@example.com branch is verbatim.
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    d = tempfile.mkdtemp(prefix="ch12_s12_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_worker_dead_letters_bad_address_after_three_attempts(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S12 Solution, closing paragraph): "The consumer loop retries on its own. A
    job to `bad@example.com` fails, gets re-enqueued, and is retried. After three
    attempts `queue.dead_letters()` returns it and the `/api/emails/dead`
    endpoint shows it." with the worker's verbatim failure branch
    `if payload["to"] == "bad@example.com": raise Exception("SMTP connection refused")`.
    """
    queue = Queue(topic="emails", max_retries=3)  # verbatim worker constructor
    queue.push({"to": "alice@example.com", "subject": "Welcome", "body": "hi"})
    queue.push({"to": "bad@example.com", "subject": "Welcome", "body": "hi"})

    sent, guard = [], 0
    # Verbatim worker loop body (bounded drain; print/sleep omitted):
    for job in queue.consume("emails", poll_interval=0):
        payload = job.payload
        try:
            if payload["to"] == "bad@example.com":
                raise Exception("SMTP connection refused")
            sent.append(payload["to"])
            job.complete()
        except Exception as e:
            job.fail(str(e))
        guard += 1
        if guard >= 10:  # safety bound (test harness only)
            break

    assert sent == ["alice@example.com"], "the good email was sent and completed"
    dead = queue.dead_letters()
    assert len(dead) == 1, "the bad address ends up in dead letters"
    assert dead[0].payload["to"] == "bad@example.com"
    assert dead[0].attempts == 3, "after three attempts it is dead-lettered"
    assert dead[0].error == "SMTP connection refused"
    assert queue.size() == 0, "nothing left pending (the /api/emails/queue count is 0)"
