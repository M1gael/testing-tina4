# QA-audit impl — Chapter 12 Queues, S8 "Queue in Route Handlers".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S8, lines 335-378)
# Framework      : tina4_python.queue + core.router (READ-ONLY — never modified)
#
# Implemented VERBATIM as a new reader would copy it from S8: the @post("/api/orders")
# handler pushes an order-confirmation onto "emails" and produces onto two other
# topics ("invoices", "warehouse_sync"), then returns an instant 201. Nothing in
# the snippet is changed. Served under `tina4 serve`; the served-path behaviour is
# recorded in findings-log.md / coverage-ledger. (The chapter's snippet carries no
# auth note — the empirical served result of POSTing without a token is recorded
# there too.)

from tina4_python.core.router import get, post
from tina4_python.queue import Queue

queue = Queue(topic="emails")


@post("/api/orders")
async def create_order(request, response):
    body = request.body

    # Create the order in the database
    order_id = 101  # Simulated

    # Send confirmation email
    queue.push({
        "type": "order_confirmation",
        "to": body["email"],
        "order_id": order_id,
        "total": body["total"]
    })

    # Generate invoice on a different topic
    queue.produce("invoices", {
        "order_id": order_id,
        "format": "pdf"
    })

    # Sync with warehouse on a different topic
    queue.produce("warehouse_sync", {
        "order_id": order_id,
        "items": body["items"]
    })

    return response.json({
        "message": "Order created",
        "order_id": order_id
    }, 201)
