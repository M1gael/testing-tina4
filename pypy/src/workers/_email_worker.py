# QA-audit impl — Chapter 12 Queues, S12 "Solution" consumer (`email_worker.py`).
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S12, lines 552-583)
# Framework      : tina4_python.queue (READ-ONLY — never modified)
#
# The BODY below is the S12 worker VERBATIM. The ONLY deviation from the doc is the
# leading underscore in the FILENAME: the doc says create `src/workers/email_worker.py`,
# but `tina4 serve` auto-discovers and imports EVERY `src/**/*.py` at startup
# (server.py `_auto_discover` -> `root.rglob("*.py")`, skipping only
# {public,templates,scss,locales,icons} and `_`-prefixed paths). Importing this
# module runs its top-level `for job in queue.consume("emails"):` loop, which polls
# forever (default poll_interval=1.0, sleeps when empty) and NEVER returns — so a
# worker at the documented path `src/workers/email_worker.py` HANGS the server at
# boot. The `_` prefix is the minimum change that lets the verbatim worker live in
# the repo without breaking serve. This mismatch is finding PY-12-09; the doc treats
# the worker as a separately-run script ("run separately") yet places it inside the
# auto-discovered src/ tree.
#
# NOTE: do not import this module from the live app or a test — it blocks forever by
# design. The worker LOGIC is exercised bounded in
# tests/test_ch12_email_worker_s12.py, and the boot-hang is proven in
# tests/test_ch12_worker_autodiscover_probe.py.

from tina4_python.queue import Queue
import time

queue = Queue(topic="emails", max_retries=3)

for job in queue.consume("emails"):
    payload = job.payload

    print(f"Sending email to {payload['to']}...")
    print(f"  Subject: {payload['subject']}")
    print(f"  Body: {payload['body'][:50]}...")

    try:
        # Simulate sending (replace with real email logic)
        time.sleep(1)

        # Simulate failure for a specific address
        if payload["to"] == "bad@example.com":
            raise Exception("SMTP connection refused")

        print(f"  Email sent to {payload['to']} successfully!")
        job.complete()

    except Exception as e:
        print(f"  Failed: {e}")
        job.fail(str(e))
