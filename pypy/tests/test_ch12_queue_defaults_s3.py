# QA-audit test — Chapter 12 Queues, S3 "Priority and Delay" default VALUES.
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S3 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
#
# Closes audit gap B1: the existing S3/S5 tests only RELY on the priority/delay
# defaults indirectly. These assert the default VALUE itself — that an omitted
# `priority` is stored as 0, and an omitted `delay_seconds` produces an
# immediately-available job (no positive delay offset) — by reading the stored
# job file and by behaviour, and by proving the no-arg push is identical to the
# explicit `=0` push.
import glob
import json
import os
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    """Isolate the file backend in a throwaway dir so each test is independent
    and never pollutes the workspace data/queue tree."""
    d = tempfile.mkdtemp(prefix="ch12_s3def_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _only_stored_job(tmp_queue_path, topic):
    """Read the single persisted job dict for a topic (peeked at the stored file,
    not via the consume API)."""
    files = glob.glob(os.path.join(tmp_queue_path, topic, "*.queue-data"))
    assert len(files) == 1, "exactly one job should be persisted"
    return json.loads(open(files[0], encoding="utf-8").read())


# ---- priority defaults to 0 -------------------------------------------------

def test_priority_defaults_to_zero_value(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Priority and Delay): "`priority` defaults to `0`."

    A push with no priority argument stores priority == 0 (the default VALUE,
    read straight off the persisted job).
    """
    Queue(topic="emails").push({"to": "a@b.com"})
    stored = _only_stored_job(tmp_queue_path, "emails")
    assert stored["priority"] == 0, "omitted priority is stored as the default 0"


def test_noarg_priority_equals_explicit_zero(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Priority and Delay): "`priority` defaults to `0`." + (S5) ties break
    oldest-first.

    A no-arg push and an explicit priority=0 push must be indistinguishable: at
    equal priority they come out oldest-first, so the no-arg (pushed first) wins.
    Proves the omitted argument IS priority 0, not some other implicit level.
    """
    queue = Queue(topic="tasks")
    queue.push({"label": "implicit"})                 # no arg -> default
    queue.push({"label": "explicit"}, priority=0)     # explicit 0

    assert queue.pop().payload["label"] == "implicit", (
        "no-arg push ties with explicit priority=0 and wins on oldest-first"
    )
    assert queue.pop().payload["label"] == "explicit"


# ---- delay_seconds defaults to 0 --------------------------------------------

def test_delay_seconds_defaults_to_zero_value(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Priority and Delay): "`delay_seconds` defaults to `0`."

    With the default delay the stored job's available_at is not in the future
    relative to its created_at (no positive offset), i.e. the job is available
    immediately. (push computes available_at before created_at when delay==0, so
    available_at <= created_at; a positive delay would push available_at after.)
    """
    Queue(topic="emails").push({"to": "a@b.com"})
    stored = _only_stored_job(tmp_queue_path, "emails")
    assert stored["available_at"] <= stored["created_at"], (
        "omitted delay_seconds must leave the job available immediately (no delay)"
    )


def test_noarg_delay_is_immediately_poppable(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Priority and Delay): "`delay_seconds` defaults to `0`." with (S3) "The
    file backend honors the delay; the job stays hidden until the time arrives."

    The behavioural proof of delay 0: a no-arg push is poppable straight away,
    exactly like an explicit delay_seconds=0 push.
    """
    queue = Queue(topic="emails")
    queue.push({"to": "implicit@b.com"})                    # no arg -> default 0
    job = queue.pop()
    assert job is not None and job.payload["to"] == "implicit@b.com", (
        "default delay makes the job available immediately"
    )
    job.complete()

    queue.push({"to": "explicit@b.com"}, delay_seconds=0)   # explicit 0
    job = queue.pop()
    assert job is not None and job.payload["to"] == "explicit@b.com", (
        "explicit delay_seconds=0 behaves identically to the default"
    )
