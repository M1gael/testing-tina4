# Verbatim-impl test — Chapter 12 Queues, S3 "Creating a Queue and Pushing
# Messages", implemented as an ignorant new reader following the page literally.
#
# S3 is library-level (the Queue API); it shows no HTTP routes (routes first
# appear at S7/S11), so these run as pytest sentinels. The served path for the
# same snippets is exercised live by src/routes/queue_explorer.py under
# `tina4 serve` (GET /queue).
#
# Doc claims under test (12-queues.md S3):
#   - `Queue(topic="emails")` — "The topic argument names the queue."
#   - `message_id = queue.push({...})` — returns a message id; "The payload is
#     any dictionary that can be serialized to JSON."
#   - `queue.produce("invoices", {...})` — "pushes to a specific topic without
#     creating a separate Queue instance."
#   - `count = queue.size()` — "how many pending messages are in the queue".
#
# PY-12-01 (S3 blockquote: backend "selected via environment variables, not
# constructor parameters") is covered by test_ch12_queue_config.py.
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
    """Verbatim S3: message_id = queue.push({...})."""
    queue = Queue(topic="emails")
    message_id = queue.push({
        "to": "alice@example.com",
        "subject": "Order Confirmation",
        "body": "Your order #1234 has been confirmed.",
    })
    assert message_id, "push() should return a truthy message id"
    assert isinstance(message_id, str)


def test_topic_argument_names_the_queue(tmp_queue_path):
    """Doc S3: "The topic argument names the queue." — the named topic gets its
    own storage directory under the queue path."""
    Queue(topic="emails").push({"to": "a@b.com", "subject": "x", "body": "y"})
    assert os.path.isdir(os.path.join(tmp_queue_path, "emails")), (
        "the topic should name a per-topic storage dir"
    )


def test_payload_is_any_json_serializable_dict(tmp_queue_path):
    """Doc S3: "The payload is any dictionary that can be serialized to JSON."
    A rich nested/typed payload pushes and persists faithfully (peeked at the
    stored job file — not via the consume API, which is S4)."""
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
    """Doc S3: count = queue.size() — pending message count."""
    queue = Queue(topic="emails")
    assert queue.size() == 0
    for i in range(3):
        queue.push({"to": f"user{i}@example.com", "subject": "s", "body": "b"})
    assert queue.size() == 3


# ---- produce ----------------------------------------------------------------

def test_produce_pushes_to_a_named_topic(tmp_queue_path):
    """Verbatim S3: queue.produce("invoices", {...}) pushes to another topic
    without constructing a separate Queue."""
    queue = Queue(topic="emails")
    queue.produce("invoices", {"order_id": 101, "format": "pdf"})

    # The message landed on the invoices topic, not on emails.
    assert Queue(topic="invoices").size() == 1
    assert queue.size() == 0
    assert os.path.isdir(os.path.join(tmp_queue_path, "invoices"))
