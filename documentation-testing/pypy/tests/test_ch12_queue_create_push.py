# QA-audit test — Chapter 12 Queues, S3 "Creating a Queue and Pushing Messages".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S3 is library-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
import os
import glob
import json
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    """Isolate the file backend in a throwaway dir so each test is independent
    and never pollutes the workspace data/queue tree."""
    d = tempfile.mkdtemp(prefix="ch12_s3_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---- push -------------------------------------------------------------------

def test_push_returns_a_message_id(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Creating a Queue and Pushing Messages, code block): verbatim
    `message_id = queue.push({...})` — push returns a message id.
    """
    queue = Queue(topic="emails")
    message_id = queue.push({
        "to": "alice@example.com",
        "subject": "Order Confirmation",
        "body": "Your order #1234 has been confirmed.",
    })
    assert message_id, "push() should return a truthy message id"
    assert isinstance(message_id, str)


def test_topic_argument_names_the_queue(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Creating a Queue and Pushing Messages): "The `topic` argument names the
    queue."

    The named topic gets its own storage directory under the queue path.
    """
    Queue(topic="emails").push({"to": "a@b.com", "subject": "x", "body": "y"})
    assert os.path.isdir(os.path.join(tmp_queue_path, "emails")), (
        "the topic should name a per-topic storage dir"
    )


def test_payload_is_any_json_serializable_dict(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Creating a Queue and Pushing Messages): "The payload is any dictionary
    that can be serialized to JSON."

    A rich nested/typed payload pushes and persists faithfully (peeked at the
    stored job file — not via the consume API, which is S4).
    """
    payload = {
        "to": "alice@example.com",
        "order_id": 1234,
        "items": [{"sku": "A1", "qty": 2}, {"sku": "B7", "qty": 1}],
        "meta": {"priority": True, "tags": ["vip", "rush"]},
    }
    queue = Queue(topic="orders")
    queue.push(payload)

    files = glob.glob(os.path.join(tmp_queue_path, "orders", "*.queue-data"))
    assert len(files) == 1, "the pushed message should be persisted as one job file"
    stored = json.loads(open(files[0], encoding="utf-8").read())
    # The job wraps the payload; assert every payload value survived the
    # JSON round-trip somewhere in the stored job.
    blob = json.dumps(stored)
    assert "alice@example.com" in blob
    assert '"order_id": 1234' in blob or '"order_id":1234' in blob
    assert "vip" in blob and "rush" in blob


# ---- size -------------------------------------------------------------------

def test_size_reflects_pending_count(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Queue Size): "Check how many pending messages are in the queue:" with
    verbatim `count = queue.size()`.
    """
    queue = Queue(topic="emails")
    assert queue.size() == 0
    for i in range(3):
        queue.push({"to": f"user{i}@example.com", "subject": "s", "body": "b"})
    assert queue.size() == 3


# ---- produce ----------------------------------------------------------------

def test_produce_pushes_to_a_named_topic(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 Convenience Method: produce): "The `produce` method pushes to a specific
    topic without creating a separate Queue instance:"
    """
    queue = Queue(topic="emails")
    queue.produce("invoices", {"order_id": 101, "format": "pdf"})

    # The message landed on the invoices topic, not on emails.
    assert Queue(topic="invoices").size() == 1
    assert queue.size() == 0
    assert os.path.isdir(os.path.join(tmp_queue_path, "invoices"))
