# Chapter 12 queue — interactive write API for the live chapter explorer
# (GET /chapter/12, also reachable at the back-compat /queue). The per-section
# demos and the page itself live in chapter_explorer.py; this file only provides
# the hands-on "push a message" endpoint + a storage-tree readout, which write to
# / read from the REAL data/queue so you watch persistence in the browser.
#
# POST is @noauth() so the browser can call it without a Bearer token (write
# routes are gated by default — PY-06-07).
import os

from tina4_python.core.router import get, post, noauth
from tina4_python.queue import Queue


def _queue_path():
    return os.environ.get("TINA4_QUEUE_PATH") or os.path.join("data", "queue")


def _topics():
    base = _queue_path()
    out = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            d = os.path.join(base, name)
            if not os.path.isdir(d):
                continue
            try:
                pending = Queue(topic=name).size()
            except Exception:
                pending = None
            try:
                files = len([f for f in os.listdir(d) if f.endswith(".queue-data")])
            except Exception:
                files = 0
            out.append({"topic": name, "pending": pending, "files": files})
    return out


@get("/api/queue/topics")
async def queue_topics(request, response):
    return response({"path": _queue_path(), "topics": _topics()})


@noauth()
@post("/api/queue/push")
async def queue_push(request, response):
    body = request.body or {}
    topic = body.get("topic") or "emails"
    payload = body.get("payload")
    if payload is None:
        payload = {k: v for k, v in body.items() if k != "topic"}
    if not isinstance(payload, dict) or not payload:
        return response({"error": "payload must be a non-empty JSON object"}, 400)
    q = Queue(topic=topic)
    message_id = q.push(payload)
    return response({
        "message_id": message_id,
        "topic": topic,
        "pending": q.size(),
        "storage_created": os.path.isdir(os.path.join(_queue_path(), topic)),
    }, 201)
