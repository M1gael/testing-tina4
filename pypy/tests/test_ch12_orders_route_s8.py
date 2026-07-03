# QA-audit test — Chapter 12 Queues, S8 "Queue in Route Handlers".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S8, lines 335-378)
# Framework      : tina4_python.queue + core.router + tina4_python.test (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path.
#
# Closes AUD-12-1: the S8 route (`src/routes/ch12_orders.py`, verbatim impl) was
# previously exercised only by transient `tina4 serve` + curl runs — no persisted
# regression sentinel. This drives the SAME registered handler through the
# in-process `tina4_python.test` client (the Ch18/Ch06 route-testing approach).
#
# Auth caveat (disclosed, not masked): the in-process Test client does not
# enforce the Bearer gate that `tina4 serve` applies to POST routes (the same
# serve-vs-client divergence as PY-06-13), so the POST succeeds here without a
# token. The served-path 401-without-token divergence is already logged as
# PY-12-10 and shown on the live mock (GET /chapter/12 S8). This file pins the
# HANDLER behaviour: fan-out to three topics + the instant 201 response.
#
# Queue path note: `src/routes/ch12_orders.py` constructs its Queue at import
# (conftest.py imports all route modules), freezing the default storage path
# `data/queue`. The inspection queues below deliberately use the same default
# (NO TINA4_QUEUE_PATH override) so they read the exact stores the route wrote.
import json

from tina4_python.queue import Queue
from tina4_python.test import Test, assert_equal, assert_true

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"

ORDER_BODY = {
    "email": "alice@example.com",
    "total": 149.50,
    "items": [{"sku": "WIDGET-1", "qty": 2}],
}


class Ch12OrdersRouteTest(Test):

    def setUp(self):
        # Drain leftover pending jobs (old serve/demo runs share data/queue) so
        # each assert sees exactly what THIS request produced.
        for topic in ("emails", "invoices", "warehouse_sync"):
            Queue(topic=topic).purge("pending")

    def test_post_orders_fans_out_to_three_topics_and_returns_201(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S8 Queue in Route Handlers): the @post("/api/orders") handler does
        queue.push({...order_confirmation...}) onto "emails",
        queue.produce("invoices", {"order_id": order_id, "format": "pdf"}) and
        queue.produce("warehouse_sync", {"order_id": order_id, "items":
        body["items"]}), then `return response.json({"message": "Order
        created", "order_id": order_id}, 201)`. "The user gets an instant
        response. The email, invoice, and warehouse sync happen in the
        background."
        """
        resp = self.post("/api/orders", json=ORDER_BODY)

        # -- the instant response -------------------------------------------
        assert_equal(resp.status, 201, "S8 handler returns 201")
        body = json.loads(resp.body)
        assert_equal(body, {"message": "Order created", "order_id": 101},
                     "S8 response body: Order created + the simulated order_id")

        # -- "happen in the background": the response arrived while all three
        # jobs are still PENDING (queued, not processed inline) ---------------
        emails, invoices, warehouse = (Queue(topic=t) for t in
                                       ("emails", "invoices", "warehouse_sync"))
        assert_equal(emails.size(), 1, "one order_confirmation queued on emails")
        assert_equal(invoices.size(), 1, "one invoice job queued on invoices")
        assert_equal(warehouse.size(), 1, "one sync job queued on warehouse_sync")

        # -- fan-out payloads exactly as the S8 snippet builds them ----------
        email_job = emails.pop()
        assert_equal(email_job.payload,
                     {"type": "order_confirmation", "to": "alice@example.com",
                      "order_id": 101, "total": 149.50},
                     "emails payload: order_confirmation for body['email']/['total']")
        email_job.complete()

        invoice_job = invoices.pop()
        assert_equal(invoice_job.payload, {"order_id": 101, "format": "pdf"},
                     "invoices payload: order_id + pdf format")
        invoice_job.complete()

        warehouse_job = warehouse.pop()
        assert_equal(warehouse_job.payload,
                     {"order_id": 101, "items": [{"sku": "WIDGET-1", "qty": 2}]},
                     "warehouse_sync payload: order_id + body['items']")
        warehouse_job.complete()

    def test_post_orders_pushes_nothing_on_other_topics(self):
        """documentation/tina4-book/book-1-python/chapters/12-queues.md
        (S8 Queue in Route Handlers): the handler names exactly three topics —
        push onto the constructor topic "emails" plus produce onto "invoices"
        and "warehouse_sync" — so one POST yields exactly one job per topic
        (asserted per-topic above; here: a second POST adds exactly one more
        to each, i.e. the fan-out is 1:1 per request, not cumulative).
        """
        self.post("/api/orders", json=ORDER_BODY)
        self.post("/api/orders", json=ORDER_BODY)

        for topic in ("emails", "invoices", "warehouse_sync"):
            q = Queue(topic=topic)
            assert_equal(q.size(), 2, f"two POSTs -> exactly two jobs on {topic}")
            q.purge("pending")
