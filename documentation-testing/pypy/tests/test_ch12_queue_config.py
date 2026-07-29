# QA-audit test — Chapter 12 Queues, S2 "Queue Configuration".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test below opens with the
# EXACT quoted claim it verifies plus that doc file path. S1 "Not Everything
# Should Happen Right Now" is conceptual prose with no code, so there is nothing
# to exercise. S2 shows no HTTP routes (routes first appear in S8/S11), so these
# run as library-level sentinels; the served path is exercised by the live mock
# (GET /chapter/12).
import os
import glob
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def tmp_queue_path(monkeypatch):
    """Point the file backend at a throwaway dir so a test does not depend on
    or pollute the workspace data/queue tree."""
    d = tempfile.mkdtemp(prefix="ch12_q_")
    monkeypatch.setenv("TINA4_QUEUE_PATH", d)
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---- S2: file is the zero-config default -------------------------------

def test_s2_file_is_default_backend(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S2 Queue Configuration): "Tina4 Python includes a built-in queue that
    requires zero additional setup. The default backend is file-based."

    With no TINA4_QUEUE_BACKEND set, constructing a Queue and pushing works.
    """
    assert os.environ.get("TINA4_QUEUE_BACKEND") is None
    q = Queue(topic="emails")
    mid = q.push({
        "to": "alice@example.com",
        "subject": "Order Confirmation",
        "body": "Your order #1234 has been confirmed.",
    })
    assert mid, "push() should return a message id with the default file backend"
    assert q.size() == 1


def test_s2_first_push_autocreates_storage_at_default_path(monkeypatch):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S2 Queue Configuration): "The first time you push a message, Tina4 creates
    the queue storage."
    Default path is data/queue per the S3 blockquote: "the `TINA4_QUEUE_PATH`
    environment variable controls the storage directory (default: data/queue)."

    Use a unique topic and clean it up so the default-path tree is asserted
    without env overrides.
    """
    monkeypatch.delenv("TINA4_QUEUE_BACKEND", raising=False)
    monkeypatch.delenv("TINA4_QUEUE_PATH", raising=False)
    topic = "ch12_autocreate_probe"
    target = os.path.join("data", "queue", topic)
    shutil.rmtree(target, ignore_errors=True)
    try:
        q = Queue(topic=topic)
        q.push({"hello": "world"})
        assert os.path.isdir(target), (
            f"first push should auto-create storage at default path {target}"
        )
        files = glob.glob(os.path.join(target, "*.queue-data"))
        assert files, "the pushed message should be persisted under data/queue/<topic>"
    finally:
        shutil.rmtree(target, ignore_errors=True)


def test_s2_queue_path_env_controls_dir(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 blockquote, governs the S2 file backend): "For the file backend, the
    `TINA4_QUEUE_PATH` environment variable controls the storage directory
    (default: data/queue)."

    Pushing lands files under the overridden path.
    """
    q = Queue(topic="overridden")
    q.push({"x": 1})
    assert os.path.isdir(os.path.join(tmp_queue_path, "overridden")), (
        "TINA4_QUEUE_PATH should redirect file-backend storage"
    )


# ---- PY-12-01 — backend IS a constructor parameter ---------------------

def test_s2_backend_is_a_constructor_param_py_12_01(tmp_queue_path):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S3 blockquote): "The queue backend is selected via environment variables,
    not constructor parameters."

    Reality (PY-12-01 divergence): `Queue(..., backend=...)` is an accepted
    constructor parameter and selects the backend. Default/`file` -> LiteBackend;
    `rabbitmq` -> RabbitMQBackend (constructed lazily, no broker at init). This
    test asserts the divergence so it flips if the framework is ever aligned to
    the doc — it is NOT rigged to the doc's (false) claim.
    """
    file_q = Queue(topic="t", backend="file")
    rabbit_q = Queue(topic="t", backend="rabbitmq")

    file_backend = type(file_q._backend).__name__
    rabbit_backend = type(rabbit_q._backend).__name__

    assert file_backend == "LiteBackend", file_backend
    assert rabbit_backend == "RabbitMQBackend", rabbit_backend
    # The kwarg measurably changes the selected backend -> it is NOT ignored,
    # contradicting "not constructor parameters".
    assert file_backend != rabbit_backend
