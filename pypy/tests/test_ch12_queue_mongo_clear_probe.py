# Probe — covers BH-52. MongoDB Queue.clear() crashes on a fresh (never-connected)
# queue: MongoBackend.clear() touches self._backend._collection before any operation
# has connected, so _collection is still None. Broker-gated (skips without MongoDB).
import os
import socket
import sys

import pytest


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable("localhost", 27017),
    reason="MongoDB broker unreachable — logged blocker per rule 9",
)


@pytest.fixture(autouse=True)
def _restore_env():
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)


def _mongo_queue(topic: str):
    for m in [m for m in list(sys.modules) if m.startswith("tina4_python.queue")]:
        del sys.modules[m]
    for k in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS", "TINA4_QUEUE_PATH"):
        os.environ.pop(k, None)
    os.environ.update({"TINA4_QUEUE_BACKEND": "mongodb",
                       "TINA4_QUEUE_URL": "mongodb://localhost:27017/tina4"})
    import tina4_python.queue as q  # noqa: PLC0415
    return q.Queue(topic=topic)


def test_mongo_clear_on_fresh_queue_raises_attributeerror():
    """BH-52: Queue.clear() on a freshly constructed MongoDB-backed queue raises
    AttributeError. MongoBackend.clear() (queue/mongo_backend.py:127-131) calls
    self._backend._collection.delete_many(...) WITHOUT first calling
    _ensure_connected(), so _collection is still None on a never-used queue.
    Every other MongoBackend method guards with _ensure_connected() — clear() is the
    odd one out. Sentinel asserts the crash; it flips (the AttributeError stops being
    raised) once the framework adds the missing _ensure_connected() call."""
    q = _mongo_queue("bh52_clear_probe")
    with pytest.raises(AttributeError):
        q.clear()
