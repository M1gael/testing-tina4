# QA-audit test — Chapter 12 Queues, S9 "Switching Backends via .env".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S9, lines 382-422)
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S9 is config-level (no HTTP
# routes); the served path is exercised by the live mock (GET /chapter/12).
#
# Closes A2. S9's claim is "Switching backends is a config change, not a code
# change" + the env-var table. These assert that the SAME `Queue(topic="emails")`
# call selects each documented backend purely from the env var, that the file
# env-vars (PATH) are honoured, and that TINA4_KAFKA_BROKERS is the kafka knob.
# This is backend SELECTION (which adapter is constructed) — NOT message delivery
# (no broker is running here); the matrix covers delivery per backend.
import os
import shutil
import tempfile

import pytest

from tina4_python.queue import Queue


@pytest.fixture
def clean_queue_env(monkeypatch):
    """Strip every queue env var so each case sets exactly what it tests."""
    for var in ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_QUEUE_PATH",
                "TINA4_KAFKA_BROKERS"):
        monkeypatch.delenv(var, raising=False)
    yield monkeypatch


# ---- the env-var table: TINA4_QUEUE_BACKEND selects the adapter --------------

@pytest.mark.parametrize("backend_env, expected_cls", [
    (None, "LiteBackend"),          # "file (default)"
    ("file", "LiteBackend"),
    ("rabbitmq", "RabbitMQBackend"),
    ("kafka", "KafkaBackend"),
    ("mongodb", "MongoBackend"),
])
def test_backend_selected_purely_by_env_var(clean_queue_env, backend_env, expected_cls):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S9 Environment variables the queue reads): "`TINA4_QUEUE_BACKEND` | all |
    Selects the backend: `file` (default), `rabbitmq`, `kafka`, `mongodb`" and
    "Your queue code does not change at all."

    The identical constructor call `Queue(topic="emails")` yields the documented
    backend for each env value — selection is config-only, no code change.
    """
    if backend_env is not None:
        clean_queue_env.setenv("TINA4_QUEUE_BACKEND", backend_env)
    d = tempfile.mkdtemp(prefix="ch12_s9_")
    clean_queue_env.setenv("TINA4_QUEUE_PATH", d)  # harmless for non-file
    try:
        queue = Queue(topic="emails")  # SAME call for every backend
        assert type(queue._backend).__name__ == expected_cls
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- TINA4_QUEUE_PATH controls the file backend storage dir ------------------

def test_queue_path_env_redirects_file_storage(clean_queue_env):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S9 Environment variables the queue reads): "`TINA4_QUEUE_PATH` | file |
    Storage directory for the file backend (default: `data/queue`)".
    """
    d = tempfile.mkdtemp(prefix="ch12_s9path_")
    clean_queue_env.setenv("TINA4_QUEUE_PATH", d)
    try:
        Queue(topic="emails").push({"to": "a@b.com", "subject": "s", "body": "b"})
        assert os.path.isdir(os.path.join(d, "emails")), (
            "TINA4_QUEUE_PATH redirects the file backend's storage directory"
        )
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- TINA4_KAFKA_BROKERS is the kafka broker-list knob -----------------------

def test_kafka_brokers_env_is_accepted_for_kafka(clean_queue_env):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S9 Environment variables the queue reads): "`TINA4_KAFKA_BROKERS` | kafka |
    Comma-separated broker list (overrides `TINA4_QUEUE_URL`)" and (S9 High-Scale
    Production: Kafka) `TINA4_KAFKA_BROKERS=kafka-1:9092,kafka-2:9092,kafka-3:9092`.

    Selecting kafka with a comma-separated broker list constructs the Kafka
    adapter with no code change (selection only — no broker contacted here).
    """
    clean_queue_env.setenv("TINA4_QUEUE_BACKEND", "kafka")
    clean_queue_env.setenv("TINA4_KAFKA_BROKERS", "kafka-1:9092,kafka-2:9092,kafka-3:9092")
    queue = Queue(topic="emails")
    assert type(queue._backend).__name__ == "KafkaBackend", (
        "kafka is selected via env with a multi-broker TINA4_KAFKA_BROKERS list"
    )


# ---- TINA4_QUEUE_URL is the broker connection knob (audit gap AUD-12-L) -------

def test_queue_url_env_is_the_broker_connection_knob(clean_queue_env):
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S9 Environment variables the queue reads): "`TINA4_QUEUE_URL` | rabbitmq,
    mongodb, kafka | Connection URL for the broker" and (S9 Production:
    RabbitMQ) `TINA4_QUEUE_URL=amqp://user:pass@rabbitmq.internal:5672`.

    The rabbitmq adapter is constructed FROM the URL's parts (host/port/
    credentials) — TINA4_QUEUE_URL is honoured as its own knob, not ignored.
    Selection/config only — no broker contacted (construction is lazy); real
    delivery over TINA4_QUEUE_URL is covered by the broker-gated parity tests.
    White-box like the rest of this file: asserts the constructed adapter's
    connection fields, disclosed as selection-not-delivery.
    """
    clean_queue_env.setenv("TINA4_QUEUE_BACKEND", "rabbitmq")
    clean_queue_env.setenv("TINA4_QUEUE_URL", "amqp://user:pass@rabbitmq.internal:5672")

    queue = Queue(topic="emails")

    assert type(queue._backend).__name__ == "RabbitMQBackend"
    connector = queue._backend._backend
    assert connector._host == "rabbitmq.internal", "host taken from TINA4_QUEUE_URL"
    assert connector._port == 5672, "port taken from TINA4_QUEUE_URL"
    assert connector._username == "user", "credentials taken from TINA4_QUEUE_URL"
