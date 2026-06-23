# Verbatim-impl test — Chapter 12 Queues, sections 1-2, implemented as an
# ignorant new reader following the page literally.
#
# S1 "Not Everything Should Happen Right Now" is conceptual prose — it shows
# NO code, so there is nothing to exercise; it is covered by definition. The
# tests below cover every empirically-testable claim in S2 "Queue
# Configuration".
#
# S2 has no HTTP routes (routes first appear in S7/S11), so these run as
# library-level pytest sentinels rather than under `tina4 serve`. The served
# path is exercised when the route sections land.
#
# Sentinels:
#   PY-12-01 — S3 blockquote claims the backend is "selected via environment
#              variables, not constructor parameters", but the `Queue`
#              constructor accepts a `backend=` kwarg that DOES select the
#              backend. Discovered while implementing S2 config. Flips if the
#              framework is ever aligned to the doc.
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
    """Doc S2: "Tina4 Python includes a built-in queue that requires zero
    additional setup. The default backend is file-based." -> with no
    TINA4_QUEUE_BACKEND set, constructing a Queue and pushing works."""
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
    """Doc S2: "The first time you push a message, Tina4 automatically creates
    the queue storage." + S3 note: default path is data/queue. Use a unique
    topic and clean it up so the default-path tree is asserted without env
    overrides."""
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
    """Doc S3 config note (governs S2): TINA4_QUEUE_PATH controls the storage
    directory. Pushing lands files under the overridden path."""
    q = Queue(topic="overridden")
    q.push({"x": 1})
    assert os.path.isdir(os.path.join(tmp_queue_path, "overridden")), (
        "TINA4_QUEUE_PATH should redirect file-backend storage"
    )


# ---- PY-12-01 — backend IS a constructor parameter ---------------------

def test_s2_backend_is_a_constructor_param_py_12_01(tmp_queue_path):
    """Doc S3 blockquote: "The queue backend is selected via environment
    variables, not constructor parameters."

    Reality: `Queue(..., backend=...)` is an accepted constructor parameter
    and selects the backend. Default/`file` -> LiteBackend; `rabbitmq` ->
    RabbitMQBackend (constructed lazily, no broker connection at init).

    Sentinel asserts the divergence; flips if the constructor param is ever
    removed to match the doc.
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
