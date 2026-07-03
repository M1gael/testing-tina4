# QA-audit impl — Chapter 12 Queues, S11/S12 "Exercise: Build an Email Queue" + "Solution".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S12, lines 489-550)
# Framework      : tina4_python.queue + core.router (READ-ONLY — never modified)
#
# Implemented VERBATIM from the S12 "Solution" — `src/routes/email_queue.py` exactly
# as printed (the four endpoints: POST /api/emails/send, GET /api/emails/queue,
# GET /api/emails/dead, POST /api/emails/retry). Nothing in the snippet is changed.
# The companion consumer is the S12 worker (kept at src/workers/_email_worker.py;
# see that file's header for why the leading underscore is required — PY-12-09).
# Served under `tina4 serve`; served-path behaviour recorded in findings-log.md.

from tina4_python.core.router import get, post
from tina4_python.queue import Queue

queue = Queue(topic="emails", max_retries=3)


@post("/api/emails/send")
async def queue_email(request, response):
    body = request.body

    errors = []
    if not body.get("to"):
        errors.append("'to' is required")
    if not body.get("subject"):
        errors.append("'subject' is required")
    if not body.get("body"):
        errors.append("'body' is required")

    if errors:
        return response.json({"errors": errors}, 400)

    message_id = queue.push({
        "to": body["to"],
        "subject": body["subject"],
        "body": body["body"]
    })

    return response.json({
        "message": "Email queued for sending",
        "message_id": message_id
    }, 201)


@get("/api/emails/queue")
async def email_queue_size(request, response):
    count = queue.size()
    return response.json({"pending": count})


@get("/api/emails/dead")
async def email_dead_letters(request, response):
    items = []
    for job in queue.dead_letters():
        items.append({
            "id": job.id,
            "payload": job.payload,
            "attempts": job.attempts,
            "error": job.error
        })
    return response.json({"dead_letters": items, "count": len(items)})


@post("/api/emails/retry")
async def retry_dead_emails(request, response):
    queue.retry()
    return response.json({"message": "Dead-letter emails re-queued"})
