# QA-audit test — Chapter 12 Queues, S11 "Exercise: Build an Email Queue" +
# S12 "Solution" — the four HTTP endpoints.
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S11 lines 449-485, S12 lines 489-550)
# Framework      : tina4_python.queue + core.router + tina4_python.test (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path.
#
# Closes AUD-12-2: the S12 solution routes (`src/routes/email_queue.py`,
# verbatim impl) were previously exercised only by transient served curls; the
# 400-validation branch had zero coverage. This drives the SAME registered
# handlers through the in-process `tina4_python.test` client.
#
# Auth caveat (disclosed, not masked): the in-process Test client does not
# enforce the Bearer gate `tina4 serve` applies to POST routes (PY-06-13
# mechanics); the served-path 401 divergence for these endpoints is PY-12-10.
# This file pins the HANDLER behaviour per the S11 endpoint table + S12 code.
#
# Revive-extent caveat: POST /api/emails/retry calls queue.retry() (no arg),
# which the doc says re-queues EVERY dead-letter job but actually revives ONE
# per call — that divergence is already sentineled as PY-12-04 in
# test_ch12_queue_retry_deadletter_s7.py. Here the retry test constructs
# exactly ONE dead job, where the endpoint's documented outcome and the actual
# behaviour coincide — the endpoint claim is pinned without duplicating the
# PY-12-04 sentinel.
#
# Queue path note: `src/routes/email_queue.py` constructs Queue(topic="emails",
# max_retries=3) at import (conftest.py imports route modules), freezing the
# default storage path `data/queue`. Inspection queues below use the same
# default (NO TINA4_QUEUE_PATH override) so they read the store the routes use.
# Inspection queues that construct dead letters use max_retries=3 to match the
# route queue's limit (dead_letters() filters attempts >= the caller's limit).
import json

from tina4_python.queue import Queue
from tina4_python.test import Test, assert_equal, assert_true

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"

# The S11 "Test with" curl payload, verbatim.
DOC_EMAIL = {"to": "alice@example.com", "subject": "Welcome!",
             "body": "Thanks for signing up."}


def _make_dead_email(payload, error="SMTP connection refused"):
    """Drive one job to the dead-letter store at attempts == 3 (the route
    queue's max_retries), per the S12 narrative: a job that keeps failing 'After
    three attempts queue.dead_letters() returns it'."""
    q = Queue(topic="emails", max_retries=3)
    q.push(payload)
    for _ in range(3):
        job = q.pop()
        job.fail(error)
    return q


class Ch12EmailRoutesTest(Test):

    def setUp(self):
        # Empty both stores so each test sees only what it creates.
        q = Queue(topic="emails", max_retries=3)
        q.purge("pending")
        q.purge("dead")

    # ---- POST /api/emails/send — the 201 branch ---------------------------

    def test_send_valid_email_returns_201_with_message_id(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S11 endpoint table): "POST | /api/emails/send | Queue an email for
        sending" + (S12 Solution): `return response.json({"message": "Email
        queued for sending", "message_id": message_id}, 201)` where message_id
        is `queue.push({...})`'s return. Payload is the S11 curl example.
        """
        resp = self.post("/api/emails/send", json=DOC_EMAIL)

        assert_equal(resp.status, 201, "valid send returns 201")
        body = json.loads(resp.body)
        assert_equal(body["message"], "Email queued for sending", "S12 body message")
        assert_true(isinstance(body["message_id"], str) and body["message_id"],
                    "message_id is queue.push()'s non-empty id")

        # The email actually landed on the queue with the documented fields.
        q = Queue(topic="emails", max_retries=3)
        assert_equal(q.size(), 1, "exactly one email queued")
        job = q.pop()
        assert_equal(job.payload, DOC_EMAIL, "payload: to + subject + body as sent")
        assert_equal(job.id, body["message_id"], "message_id is the queued job's id")
        job.complete()

    # ---- POST /api/emails/send — the 400 validation branch ----------------

    def test_send_missing_one_field_returns_400_naming_it(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S11): "The email payload should include: `to` (required), `subject`
        (required), `body` (required)" + (S12 Solution): a missing field
        appends "'<field>' is required" and `return response.json({"errors":
        errors}, 400)`.
        """
        payload = {"to": "alice@example.com", "body": "Thanks for signing up."}
        resp = self.post("/api/emails/send", json=payload)

        assert_equal(resp.status, 400, "missing subject -> 400")
        body = json.loads(resp.body)
        assert_equal(body, {"errors": ["'subject' is required"]},
                     "exactly the one missing field is named")

        assert_equal(Queue(topic="emails", max_retries=3).size(), 0,
                     "nothing was queued on the 400 branch")

    def test_send_missing_all_fields_returns_400_with_all_three_errors(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S12 Solution): the handler collects an error per missing field —
        "'to' is required", "'subject' is required", "'body' is required" —
        before returning `{"errors": errors}` with 400.
        """
        resp = self.post("/api/emails/send", json={})

        assert_equal(resp.status, 400, "empty payload -> 400")
        body = json.loads(resp.body)
        assert_equal(body, {"errors": ["'to' is required",
                                       "'subject' is required",
                                       "'body' is required"]},
                     "all three required fields are named, in handler order")

    # ---- GET /api/emails/queue ---------------------------------------------

    def test_queue_endpoint_reports_pending_count(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S11 endpoint table): "GET | /api/emails/queue | List pending email
        count" + (S12 Solution): `return response.json({"pending": count})`
        where count is `queue.size()`.
        """
        resp = self.get("/api/emails/queue")
        assert_equal(json.loads(resp.body), {"pending": 0}, "empty queue -> 0")

        self.post("/api/emails/send", json=DOC_EMAIL)

        resp = self.get("/api/emails/queue")
        assert_equal(resp.status, 200, "queue endpoint returns 200")
        assert_equal(json.loads(resp.body), {"pending": 1},
                     "one queued email -> pending: 1")

    # ---- GET /api/emails/dead ----------------------------------------------

    def test_dead_endpoint_lists_dead_letters_with_fields(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S11 endpoint table): "GET | /api/emails/dead | List dead letter jobs"
        + (S12 Solution): each item carries {"id", "payload", "attempts",
        "error"} and the response is {"dead_letters": items, "count":
        len(items)}. (S12 narrative): "After three attempts
        queue.dead_letters() returns it and the /api/emails/dead endpoint
        shows it."
        """
        bad = {"to": "bad@example.com", "subject": "s", "body": "b"}
        _make_dead_email(bad)

        resp = self.get("/api/emails/dead")
        assert_equal(resp.status, 200, "dead endpoint returns 200")
        body = json.loads(resp.body)
        assert_equal(body["count"], 1, "the dead-lettered email is counted")
        item = body["dead_letters"][0]
        assert_equal(item["payload"], bad, "payload survives into dead letters")
        assert_equal(item["attempts"], 3, "dead after three attempts")
        assert_equal(item["error"], "SMTP connection refused", "last error kept")
        assert_true(isinstance(item["id"], str) and item["id"], "job id present")

    # ---- POST /api/emails/retry --------------------------------------------

    def test_retry_endpoint_revives_the_dead_letter(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S11 endpoint table): "POST | /api/emails/retry | Revive dead-letter
        jobs" + (S12 Solution): the handler calls `queue.retry()` and returns
        {"message": "Dead-letter emails re-queued"}. (S12 narrative): "You
        investigate, fix the address, and call /api/emails/retry to put it
        back on the queue."

        One dead job here — where retry()'s actual one-per-call revive
        (PY-12-04) and the documented outcome coincide; see the file header.
        """
        q = _make_dead_email({"to": "bad@example.com", "subject": "s", "body": "b"})
        assert_equal(len(q.dead_letters()), 1, "precondition: one dead letter")

        resp = self.post("/api/emails/retry")
        assert_equal(resp.status, 200, "retry endpoint returns 200")
        assert_equal(json.loads(resp.body),
                     {"message": "Dead-letter emails re-queued"}, "S12 body message")

        assert_equal(len(q.dead_letters()), 0, "the dead letter left the dead store")
        assert_equal(q.size(), 1, "it is back on the pending queue")
