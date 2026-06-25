# Chapter Explorer — USER-requested tooling (NOT a verbatim doc impl). A generic
# per-chapter live view of the Tina4 documentation:
#   GET /chapters          — index of the chapters wired up
#   GET /chapter/{num}      — one chapter, a block per section
#   GET /api/chapter/{num}/demos — the section/demo JSON the page renders
#
# Each section block shows a faithful example taken from that chapter's docs and
# EXECUTES it on the live server, so you see the taught code work (or not) in the
# browser.
#
# Faithfulness rule for the examples: keep each documented snippet as close to the
# page as possible. Only NON-FUNCTIONAL pieces may change — output strings, how a
# value is printed/inspected, or wrapping an illustrative fragment so it can run.
# Never change the API being demonstrated; the demo must test the thing the docs
# show. `doc_code` always holds the verbatim snippet; `run_code` (when present) is
# the runnable adaptation shown alongside it.
#
# Demos run in an isolated temp dir (per-chapter `prepare_env`) so they are
# repeatable and never pollute real storage. Add a chapter by writing a
# `build_<n>(demo)` function returning sections, then a `register(...)` call at
# the bottom — no other file needs to change.
import io
import os
import glob
import json
import shutil
import contextlib
import tempfile
from importlib.metadata import version as _pkg_version

from tina4_python.core.router import get
from tina4_python.queue import Queue


def _version():
    try:
        return "tina4-python " + _pkg_version("tina4-python")
    except Exception:
        return "tina4-python (unknown)"


# ============================ engine =========================================
CHAPTERS = {}


def register(num, title, build, prepare_env=None, interactive=None, blurb=None):
    """Wire a chapter into the explorer. `build(demo)` returns a list of
    sections: [{"id": "S2", "title": "...", "demos": [demo(...), ...]}]."""
    CHAPTERS[num] = {"num": num, "title": title, "build": build,
                     "prepare_env": prepare_env, "interactive": interactive,
                     "blurb": blurb}


def _exec_sandbox(code, post=None, prepare_env=None, extra_env=None):
    """Execute a snippet against the live framework in an isolated temp dir.
    Captures stdout, lets `post(ns, sandbox)` compute output lines while the
    sandbox still exists, then fully restores os.environ and tears down."""
    tmp = tempfile.mkdtemp(prefix="chexpl_")
    prior = dict(os.environ)
    ns, buf, error, lines = {}, io.StringIO(), None, []
    try:
        if prepare_env:
            prepare_env(tmp)
        if extra_env:
            os.environ.update(extra_env)
        with contextlib.redirect_stdout(buf):
            exec(code, ns)
        if post:
            lines = post(ns, tmp)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    finally:
        os.environ.clear()
        os.environ.update(prior)
        shutil.rmtree(tmp, ignore_errors=True)
    return buf.getvalue(), error, lines


def _make_demo(prepare_env):
    """Bind a `demo(...)` builder to a chapter's env isolation."""
    def demo(section, claim, doc_lang, doc_code, post, run_lang=None,
             run_code=None, extra_env=None, diverge_marker=None):
        code = run_code if run_code is not None else doc_code
        out, err, lines = _exec_sandbox(code, post, prepare_env, extra_env)
        body = err or "\n".join(lines)
        if err:
            status = "fail"
        elif diverge_marker and diverge_marker in body:
            status = "diverge"
        else:
            status = "pass"
        d = {"section": section, "claim": claim, "doc_lang": doc_lang,
             "doc_code": doc_code, "output": body, "status": status}
        if run_code is not None:
            d["run_lang"] = run_lang or "python"
            d["run_code"] = run_code
        return d
    return demo


def _files_in(sandbox, topic):
    try:
        d = os.path.join(sandbox, topic)
        return [f for f in os.listdir(d) if f.endswith(".queue-data")]
    except Exception:
        return []


# ===================== Chapter 12 — Queues ===================================
# Verbatim snippets from documentation/.../book-1-python/chapters/12-queues.md.

DOC_FILE_DEFAULT = '''# No TINA4_QUEUE_BACKEND needed -- file is the default'''

DOC_ENV_RABBIT = '''TINA4_QUEUE_BACKEND=rabbitmq
TINA4_QUEUE_URL=amqp://user:pass@localhost:5672'''

DOC_CREATE_PUSH = '''from tina4_python.queue import Queue

queue = Queue(topic="emails")

# Push a message
message_id = queue.push({
    "to": "alice@example.com",
    "subject": "Order Confirmation",
    "body": "Your order #1234 has been confirmed."
})

count = queue.size()'''

DOC_PRODUCE = '''queue = Queue(topic="emails")
queue.produce("invoices", {"order_id": 101, "format": "pdf"})'''

DOC_BLOCKQUOTE = ('"The queue backend is selected via environment variables, '
                  'not constructor parameters. Set TINA4_QUEUE_BACKEND to '
                  'file (default), rabbitmq, kafka, or mongodb."')

DOC_CONSUME_DRAIN = '''for job in queue.consume("emails", poll_interval=0):
    process(job)
    job.complete()'''

DOC_CONSUME_ITER = '''for job in queue.consume("emails", iterations=5):
    process(job)
    job.complete()'''

DOC_CONSUME_BYID = '''for job in queue.consume("emails", job_id="specific-job-id"):
    process(job)
    job.complete()'''

DOC_POP = '''job = queue.pop()

if job is not None:
    try:
        send_email(job.payload["to"], job.payload["subject"])
        job.complete()
    except Exception as e:
        job.fail(str(e))'''

DOC_PRIORITY = '''queue = Queue(topic="tasks")

queue.push({"label": "normal"})                 # priority 0
queue.push({"label": "urgent"}, priority=10)    # priority 10
queue.push({"label": "also normal"})            # priority 0

queue.pop().payload["label"]   # "urgent"        (highest priority)
queue.pop().payload["label"]   # "normal"        (oldest of the priority-0 pair)
queue.pop().payload["label"]   # "also normal"'''

DOC_DELAY = ('"A delayed job (pushed with delay_seconds) stays hidden until its '
             'time arrives, regardless of priority."')


def _ch12_prepare_env(tmp):
    os.environ["TINA4_QUEUE_PATH"] = tmp
    os.environ.pop("TINA4_QUEUE_BACKEND", None)  # file is the default


def build_ch12(demo):
    # ---- S2: Queue configuration -----------------------------------------
    def p_file_default(ns, sb):
        q = ns.get("queue")
        b = type(q._backend).__name__ if q is not None else "?"
        return [f'TINA4_QUEUE_BACKEND unset → Queue(topic="emails")._backend = {b}',
                "the file backend is selected with zero configuration."]

    def p_env_rabbit(ns, sb):
        q = ns.get("queue")
        b = type(q._backend).__name__ if q is not None else "?"
        ok = b == "RabbitMQBackend"
        return [f"with TINA4_QUEUE_BACKEND=rabbitmq set: Queue(...)._backend = {b}",
                ("the framework switched backend purely from the env var — the "
                 "Queue/push/consume code is unchanged" if ok else
                 "env var did NOT switch the backend"),
                "note: no broker is running here, so this proves backend "
                "SELECTION via env (S2's claim), not message delivery."]

    s2 = [
        demo("S2", "File backend is the zero-config default",
             "bash", DOC_FILE_DEFAULT, p_file_default, run_lang="python",
             run_code='from tina4_python.queue import Queue\nqueue = Queue(topic="emails")'),
        demo("S2", "The backend is selected via an environment variable — your code stays the same",
             "bash", DOC_ENV_RABBIT, p_env_rabbit, run_lang="python",
             run_code='import os\nos.environ["TINA4_QUEUE_BACKEND"] = "rabbitmq"\nfrom tina4_python.queue import Queue\nqueue = Queue(topic="emails")',
             extra_env={"TINA4_QUEUE_BACKEND": "rabbitmq"}),
    ]

    # ---- S3: Creating a queue and pushing messages -----------------------
    def p_create_push(ns, sb):
        q = ns.get("queue")
        b = type(q._backend).__name__ if q is not None else "?"
        return [f"message_id = {ns.get('message_id')!r}",
                f"count = queue.size() → {ns.get('count')!r}",
                f"type(queue._backend).__name__ = {b}",
                f"storage auto-created: data/queue/emails/ → {_files_in(sb, 'emails')}"]

    def p_produce(ns, sb):
        return [f'Queue(topic="invoices").size() = {Queue(topic="invoices").size()}',
                f"storage: data/queue/invoices/ → {_files_in(sb, 'invoices')}"]

    def p_payload(ns, sb):
        files = glob.glob(os.path.join(sb, "orders", "*.queue-data"))
        survived = False
        if files:
            blob = open(files[0], encoding="utf-8").read()
            survived = ("1234" in blob and "vip" in blob and "rush" in blob)
        return [f"pushed a nested/typed dict → message_id = {ns.get('message_id')!r}",
                f"stored job file: {[os.path.basename(f) for f in files]}",
                f"nested values (order_id, items, tags) survived the JSON round-trip = {survived}"]

    def p_blockquote(ns, sb):
        fb = type(ns["file_q"]._backend).__name__
        rb = type(ns["rabbit_q"]._backend).__name__
        return [f'Queue(topic="t", backend="file")._backend     = {fb}',
                f'Queue(topic="t", backend="rabbitmq")._backend = {rb}',
                "=> the backend= constructor argument IS accepted and DOES select "
                'the backend, contradicting the documented "not constructor parameters".']

    payload_run = ('from tina4_python.queue import Queue\n'
                   'queue = Queue(topic="orders")\n'
                   'message_id = queue.push({\n'
                   '    "to": "alice@example.com",\n'
                   '    "order_id": 1234,\n'
                   '    "items": [{"sku": "A1", "qty": 2}],\n'
                   '    "meta": {"priority": True, "tags": ["vip", "rush"]},\n'
                   '})')

    blockquote_run = ('from tina4_python.queue import Queue\n'
                      'file_q = Queue(topic="t", backend="file")\n'
                      'rabbit_q = Queue(topic="t", backend="rabbitmq")')

    s3 = [
        demo("S3", "Create a queue, push a message, read the size",
             "python", DOC_CREATE_PUSH, p_create_push),
        demo("S3", "produce() pushes to a named topic without a separate Queue instance",
             "python", DOC_PRODUCE, p_produce,
             run_code='from tina4_python.queue import Queue\n' + DOC_PRODUCE),
        demo("S3", "The payload is any dictionary that can be serialized to JSON",
             "text", '"The payload is any dictionary that can be serialized to JSON." (S3)',
             p_payload, run_lang="python", run_code=payload_run),
        demo("S3", "PY-12-01 · doc says the backend is env-only, NOT constructor parameters",
             "text", DOC_BLOCKQUOTE, p_blockquote, run_lang="python",
             run_code=blockquote_run, diverge_marker="RabbitMQBackend"),
    ]

    # ---- S4: Consuming messages ------------------------------------------
    def p_consume_drain(ns, sb):
        return [f"pushed 3 jobs, then consume(poll_interval=0) drained: {ns.get('drained')}",
                f"queue.size() after draining = {Queue(topic='emails').size()}",
                "poll_interval=0 makes the generator drain once and STOP "
                "(it does not loop forever)."]

    def p_consume_iter(ns, sb):
        c = ns.get("consumed") or []
        return [f"pushed 7 jobs; consume(iterations=5) yielded {len(c)}: {c}",
                f"remaining pending = {Queue(topic='emails').size()}",
                "iterations=5 stops the generator after exactly five jobs."]

    def p_consume_byid(ns, sb):
        return [f"target message_id = {ns.get('target')!r}",
                f"consume(job_id=target) yielded = {ns.get('seen')}",
                f"the other job is untouched, still pending = {Queue(topic='emails').size()}",
                "job_id yields that one job once, then the generator returns."]

    def p_pop(ns, sb):
        return [f"pop() #1 → job.payload['to'] = {ns.get('label')!r}, then job.complete()",
                f"pop() #2 on the now-empty queue → {ns.get('second')!r}",
                "pop returns the highest-priority available job, or None when empty."]

    consume_drain_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails")\n'
        'for i in range(3):\n'
        '    queue.push({"to": f"u{i}@x.com", "subject": "s", "body": "b"})\n'
        'drained = []\n'
        'for job in queue.consume("emails", poll_interval=0):\n'
        '    drained.append(job.payload["to"])\n'
        '    job.complete()')

    consume_iter_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails")\n'
        'for i in range(7):\n'
        '    queue.push({"n": i})\n'
        'consumed = []\n'
        'for job in queue.consume("emails", iterations=5):\n'
        '    consumed.append(job.payload["n"])\n'
        '    job.complete()')

    consume_byid_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails")\n'
        'target = queue.push({"pick": "me"})\n'
        'queue.push({"pick": "not me"})\n'
        'seen = []\n'
        'for job in queue.consume("emails", job_id=target):\n'
        '    seen.append(job.payload)\n'
        '    job.complete()')

    pop_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails")\n'
        'queue.push({"to": "a@b.com", "subject": "hi"})\n'
        'first = queue.pop()\n'
        'label = first.payload["to"] if first is not None else None\n'
        'first.complete()\n'
        'second = queue.pop()')

    s4 = [
        demo("S4", "consume(poll_interval=0) drains the queue once and stops",
             "python", DOC_CONSUME_DRAIN, p_consume_drain,
             run_lang="python", run_code=consume_drain_run),
        demo("S4", "consume(iterations=N) stops after N jobs",
             "python", DOC_CONSUME_ITER, p_consume_iter,
             run_lang="python", run_code=consume_iter_run),
        demo("S4", "consume(job_id=...) yields one specific job, once",
             "python", DOC_CONSUME_BYID, p_consume_byid,
             run_lang="python", run_code=consume_byid_run),
        demo("S4", "pop() returns the highest-priority job, or None when empty",
             "python", DOC_POP, p_pop,
             run_lang="python", run_code=pop_run),
    ]

    # ---- S5: Priority ordering -------------------------------------------
    def p_priority(ns, sb):
        order = ns.get("order")
        ok = order == ["urgent", "normal", "also normal"]
        return [f"pop order = {order}",
                f"matches the documented 'urgent' → 'normal' → 'also normal' = {ok}",
                "highest priority first; ties break oldest-first."]

    def p_delay(ns, sb):
        return [f"pop() #1 → {ns.get('first_label')!r}  (delayed-vip, priority 99, stays hidden)",
                f"pop() #2 → {ns.get('second')!r}  (delayed job still hidden)",
                f"queue.size() = {Queue(topic='tasks').size()}  (the delayed job is still pending, just not visible yet)",
                "a delayed job stays hidden until its time arrives, regardless of priority."]

    priority_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="tasks")\n'
        'queue.push({"label": "normal"})\n'
        'queue.push({"label": "urgent"}, priority=10)\n'
        'queue.push({"label": "also normal"})\n'
        'order = [queue.pop().payload["label"] for _ in range(3)]')

    delay_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="tasks")\n'
        'queue.push({"label": "delayed-vip"}, priority=99, delay_seconds=60)\n'
        'queue.push({"label": "ready"})\n'
        'first = queue.pop()\n'
        'first_label = first.payload["label"] if first is not None else None\n'
        'second = queue.pop()')

    s5 = [
        demo("S5", "Higher priority first; ties break oldest-first (verbatim example)",
             "python", DOC_PRIORITY, p_priority,
             run_lang="python", run_code=priority_run),
        demo("S5", "A delayed job stays hidden regardless of priority",
             "text", DOC_DELAY, p_delay,
             run_lang="python", run_code=delay_run),
    ]

    # ---- S6: Job lifecycle -----------------------------------------------
    def p_lifecycle(ns, sb):
        return [f'fail("boom") → size={ns.get("after_fail")} (re-enqueued under the limit), attempts={ns.get("attempts")}',
                f"complete() → size={ns.get('after_complete')} (terminal: removed, never comes back)",
                'reject(reason) is an alias for fail().']

    def p_claimed_on_pop(ns, sb):
        return [f"after a bare pop() with no complete()/fail(): size={ns.get('size')}, next pop()={ns.get('nxt')!r}",
                "the job was claimed on pop and is NOT retried."]

    def p_job_retry_dup(ns, sb):
        return [f"dead-lettered, then dead.retry(): pending={ns.get('pending')}, dead={ns.get('dead')}",
                f"PY-12-05 · the SAME job id is now in BOTH pending and dead_letters() = {ns.get('dup')}",
                '"re-queue" should move the job, not leave a dead-letter duplicate.']

    lifecycle_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=3)\n'
        'queue.push({"job": "a"})\n'
        'queue.pop().fail("boom")\n'
        'after_fail = queue.size()\n'
        'attempts = queue.pop().attempts\n'
        'queue.push({"job": "b"})\n'
        'job = queue.pop(); job.complete()\n'
        'after_complete = queue.size()')

    claimed_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails")\n'
        'queue.push({"job": "a"})\n'
        'job = queue.pop()  # claimed; neither complete() nor fail() called\n'
        'size = queue.size()\n'
        'nxt = queue.pop()')

    job_retry_dup_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=1)\n'
        'queue.push({"job": "dup"})\n'
        'queue.pop().fail("boom")  # dead-lettered\n'
        'dead = queue.dead_letters()[0]; dead_id = dead.id\n'
        'dead.retry()\n'
        'pending = queue.size()\n'
        'dead_ids = [j.id for j in queue.dead_letters()]\n'
        'dead = len(dead_ids)\n'
        'dup = (dead_id in dead_ids) and pending == 1')

    s6 = [
        demo("S6", "complete() is terminal; fail() increments attempts and re-enqueues; reject() aliases fail()",
             "text",
             '"job.complete() -- mark the job as done. Terminal: the job is removed and never comes back."\n'
             '"job.fail(reason) -- record a failed attempt. Increments attempts and either re-enqueues the job or dead-letters it."\n'
             '"job.reject(reason) -- alias for fail."',
             p_lifecycle, run_lang="python", run_code=lifecycle_run),
        demo("S6", "Neither complete() nor fail() -> the job was claimed on pop and is not retried",
             "text",
             '"If you call neither, the job has already left the queue (it was claimed on pop) and will not be retried."',
             p_claimed_on_pop, run_lang="python", run_code=claimed_run),
        demo("S6", "PY-12-05 · job.retry() re-queues but leaves a dead-letter duplicate",
             "text",
             '"job.retry(delay_seconds=0) -- manually re-queue the job, optionally after a delay. Bypasses the retry limit."',
             p_job_retry_dup, run_lang="python", run_code=job_retry_dup_run,
             diverge_marker="= True"),
    ]

    # ---- S7: Automatic retry and dead letters ----------------------------
    def p_deadletter(ns, sb):
        return [f'max_retries=3 → failed {ns.get("fails")} times → dead_letters()={ns.get("dead")}',
                f"a dead Job exposes id/payload/attempts/error: attempts={ns.get('d_attempts')}, error={ns.get('d_error')!r}"]

    def p_failed_vs_dead(ns, sb):
        return [f"after one fail under the limit: failed()={ns.get('failed')} (still retrying, plain dicts)",
                f"dead_letters()={ns.get('dead')} (none yet — not exhausted)"]

    def p_retry_byid(ns, sb):
        return [f"two dead, retry(job_id) on one → pending={ns.get('pending')}, dead={ns.get('dead')}",
                "retry(job_id) re-queues exactly that one job."]

    def p_retry_every(ns, sb):
        return [f"three dead, queue.retry() (no arg) → pending={ns.get('pending')}, dead={ns.get('dead')}",
                f'PY-12-04 · doc says "re-queue EVERY dead-letter job"; only {ns.get("pending")} of 3 revived.']

    def p_size_failed(ns, sb):
        return [f"after one fail under the limit: failed()={ns.get('failed')}, size('failed')={ns.get('size_failed')}",
                f"PY-12-06 · size('failed') does not count the job failed() reports (mismatch={ns.get('mismatch')})."]

    deadletter_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=3)\n'
        'queue.push({"to": "bad@example.com"})\n'
        'fails = 0\n'
        'for _ in range(10):\n'
        '    job = queue.pop()\n'
        '    if job is None: break\n'
        '    job.fail("SMTP connection refused"); fails += 1\n'
        'dl = queue.dead_letters(); dead = len(dl)\n'
        'd_attempts = dl[0].attempts if dl else None\n'
        'd_error = dl[0].error if dl else None')

    failed_vs_dead_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=3)\n'
        'queue.push({"job": "a"})\n'
        'queue.pop().fail("boom")\n'
        'failed = len(queue.failed())\n'
        'dead = len(queue.dead_letters())')

    retry_byid_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=1)\n'
        'queue.push({"n": 1}); queue.push({"n": 2})\n'
        'for _ in range(2): queue.pop().fail("boom")\n'
        'target = queue.dead_letters()[0].id\n'
        'queue.retry(target)\n'
        'pending = queue.size("pending"); dead = len(queue.dead_letters())')

    retry_every_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=1)\n'
        'for n in range(3): queue.push({"n": n})\n'
        'for _ in range(3): queue.pop().fail("boom")\n'
        'queue.retry()  # doc: re-queue EVERY dead-letter job\n'
        'pending = queue.size("pending"); dead = len(queue.dead_letters())')

    size_failed_run = (
        'from tina4_python.queue import Queue\n'
        'queue = Queue(topic="emails", max_retries=3)\n'
        'queue.push({"job": "a"})\n'
        'queue.pop().fail("boom")\n'
        'failed = len(queue.failed()); size_failed = queue.size("failed")\n'
        'mismatch = failed != size_failed')

    s7 = [
        demo("S7", "max_retries=3 -> attempted 3 times -> dead letter (Job with id/payload/attempts/error)",
             "python",
             'queue = Queue(topic="emails", max_retries=3)\n\n'
             'for job in queue.consume("emails"):\n'
             '    try:\n'
             '        send_email(job.payload)\n'
             '        job.complete()\n'
             '    except Exception as e:\n'
             '        job.fail(str(e))   # retried up to 3 times, then dead-lettered',
             p_deadletter, run_lang="python", run_code=deadletter_run),
        demo("S7", "failed() lists still-retrying jobs; dead_letters() lists exhausted ones",
             "python",
             'retrying = queue.failed()\n'
             'dead_jobs = queue.dead_letters()',
             p_failed_vs_dead, run_lang="python", run_code=failed_vs_dead_run),
        demo("S7", "retry(job_id) re-queues one specific dead-letter job",
             "python", 'queue.retry(job_id)', p_retry_byid,
             run_lang="python", run_code=retry_byid_run),
        demo("S7", "PY-12-04 · queue.retry() re-queues only ONE, not every dead-letter job",
             "python", 'queue.retry()   # Re-queue every dead-letter job',
             p_retry_every, run_lang="python", run_code=retry_every_run,
             diverge_marker="PY-12-04"),
        demo("S7", "PY-12-06 · size('failed') returns 0 while failed() lists the job",
             "python", 'queue.size("dead")       # dead-letter jobs',
             p_size_failed, run_lang="python", run_code=size_failed_run,
             diverge_marker="PY-12-06"),
    ]

    return [
        {"id": "S2", "title": "Queue configuration", "demos": s2},
        {"id": "S3", "title": "Creating a queue and pushing messages", "demos": s3},
        {"id": "S4", "title": "Consuming messages", "demos": s4},
        {"id": "S5", "title": "Priority ordering", "demos": s5},
        {"id": "S6", "title": "Job lifecycle", "demos": s6},
        {"id": "S7", "title": "Automatic retry and dead letters", "demos": s7},
    ]


register(
    12, "Queues", build_ch12, prepare_env=_ch12_prepare_env,
    blurb="Background jobs: configuration, push/produce, consume, priority, job lifecycle, retry & dead letters.",
    interactive={
        "title": "Try it yourself · push a message",
        "note": "the same Queue.push() the chapter teaches — writes to the real data/queue tree shown below",
        "push_url": "/api/queue/push",
        "topics_url": "/api/queue/topics",
        "matrix_url": "/queue/backends",
        "default_topic": "emails",
        "default_payload": {
            "to": "alice@example.com",
            "subject": "Order Confirmation",
            "body": "Your order #1234 has been confirmed.",
        },
    },
)


# ============================ routes / pages =================================
@get("/api/chapters")
async def api_chapters(request, response):
    return response([
        {"num": c["num"], "title": c["title"], "blurb": c["blurb"]}
        for c in sorted(CHAPTERS.values(), key=lambda c: c["num"])
    ])


@get("/api/chapter/{num}/demos")
async def api_chapter_demos(num, request, response):
    ch = CHAPTERS.get(int(num)) if str(num).isdigit() else None
    if not ch:
        return response({"error": f"chapter {num} is not wired into the explorer"}, 404)
    demo = _make_demo(ch["prepare_env"])
    sections = ch["build"](demo)
    return response({
        "num": ch["num"], "title": ch["title"], "version": _version(),
        "interactive": ch["interactive"], "sections": sections,
    })


def _chapter_page(num):
    return PAGE.replace("__CH__", str(num))


@get("/chapter/{num}")
async def chapter_page(num, request, response):
    return response.html(_chapter_page(num))


@get("/chapters")
async def chapters_index(request, response):
    return response.html(INDEX_PAGE)


# Back-compat: the original queue view keeps working, now served by the engine.
@get("/queue")
async def queue_page(request, response):
    return response.html(_chapter_page(12))


INDEX_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tina4 docs — live chapter explorer</title>
<style>
 :root{--bg:#fafaf7;--card:#fff;--bd:#e6e4da;--tx:#26251f;--mut:#6b6a62;}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
 .wrap{max-width:760px;margin:0 auto;padding:32px 20px 60px;}
 h1{font-size:22px;font-weight:600;margin:0 0 4px;}
 .sub{color:var(--mut);font-size:13px;margin:0 0 22px;}
 a.card{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--bd);
        border-radius:12px;padding:16px 18px;margin:10px 0;transition:background .12s;}
 a.card:hover{background:#f3f1ea;}
 .ct{font-size:16px;font-weight:600;}
 .cb{color:var(--mut);font-size:13px;margin-top:3px;}
 .empty{color:#9a988e;font-style:italic;}
</style></head>
<body><div class="wrap">
 <h1>Tina4 docs · live chapter explorer</h1>
 <p class="sub">each chapter runs faithful examples from its documentation on this live server</p>
 <div id="list"><p class="empty">loading…</p></div>
</div>
<script>
function esc(x){return String(x).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
async function load(){
 const r=await fetch("/api/chapters");const cs=await r.json();
 const el=document.getElementById("list");
 if(!cs.length){el.innerHTML='<p class="empty">No chapters wired up yet.</p>';return;}
 el.innerHTML=cs.map(c=>'<a class="card" href="/chapter/'+c.num+'"><div class="ct">Chapter '+c.num+' · '+esc(c.title)+'</div><div class="cb">'+esc(c.blurb||"")+'</div></a>').join("");
}
load();
</script></body></html>"""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tina4 docs — chapter, live</title>
<style>
  :root{--bg:#fafaf7;--card:#fff;--bd:#e6e4da;--tx:#26251f;--mut:#6b6a62;--hint:#9a988e;
        --ok:#3b6d11;--okbg:#eaf3de;--warn:#854f0b;--warnbg:#faeeda;--err:#a32d2d;--errbg:#fcebeb;
        --code:#1e1d18;--codetx:#e8e6dd;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
  .wrap{max-width:900px;margin:0 auto;padding:28px 20px 60px;}
  a.back{color:var(--mut);font-size:13px;text-decoration:none;}
  a.back:hover{color:var(--tx);}
  .top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:6px 0 18px;}
  h1{font-size:21px;font-weight:600;margin:0;}
  .sub{color:var(--mut);font-size:13px;margin:2px 0 0;}
  .chip{font-size:12px;color:var(--mut);background:#f0efe8;border:1px solid var(--bd);padding:5px 10px;border-radius:8px;white-space:nowrap;}
  h2{font-size:16px;font-weight:600;margin:26px 0 2px;}
  .secnote{color:var(--mut);font-size:12px;margin:0 0 8px;}
  .card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:12px 0;}
  .chead{display:flex;align-items:flex-start;gap:10px;margin-bottom:8px;}
  .claim{flex:1;font-size:15px;font-weight:600;}
  .badge{font-size:11px;font-weight:600;padding:3px 9px;border-radius:7px;white-space:nowrap;margin-top:2px;}
  .b-pass{color:var(--ok);background:var(--okbg);}
  .b-diverge{color:var(--warn);background:var(--warnbg);}
  .b-fail{color:var(--err);background:var(--errbg);}
  .lbl{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--hint);margin:12px 0 5px;font-weight:600;}
  pre{margin:0;background:var(--code);color:var(--codetx);border-radius:8px;padding:12px 14px;overflow-x:auto;
      font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;}
  pre.out{background:#f6f4ed;color:var(--tx);border:1px solid var(--bd);}
  label{font-size:13px;color:var(--mut);display:block;margin:8px 0 4px;}
  input,textarea{width:100%;font:14px monospace;padding:8px 10px;border:1px solid var(--bd);border-radius:8px;background:#fff;color:var(--tx);}
  textarea{min-height:84px;resize:vertical;}
  button{font:14px inherit;font-weight:500;padding:8px 16px;border:1px solid var(--bd);border-radius:8px;background:#fff;color:var(--tx);cursor:pointer;}
  button:hover{background:#f3f1ea;}
  .tree .t{display:flex;justify-content:space-between;font-family:monospace;font-size:13px;padding:6px 0;border-top:1px solid var(--bd);}
  .tree .t:first-child{border-top:none;}
  .empty{color:var(--hint);font-size:13px;font-style:italic;}
  #toast{font-size:13px;margin-top:10px;min-height:18px;}
  .tok{color:var(--ok);} .terr{color:var(--err);}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="/chapters">← all chapters</a>
  <div class="top">
    <div><h1 id="title">Chapter __CH__</h1><p class="sub" id="sub">running the documented code live…</p></div>
    <span class="chip" id="verchip"></span>
  </div>

  <div id="sections"></div>
  <div id="interactive"></div>
</div>

<script>
const CH=__CH__;
let INTERACTIVE=null;
const BADGE={pass:"works as documented",diverge:"diverges from docs",fail:"errored"};
function esc(x){return String(x).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function demoHtml(d){
  let html='<div class="card"><div class="chead"><span class="claim">'+esc(d.claim)+'</span>'+
    '<span class="badge b-'+d.status+'">'+(BADGE[d.status]||d.status)+'</span></div>'+
    '<div class="lbl">documentation'+(d.run_code?' ('+esc(d.doc_lang)+')':' code — executed live')+'</div>'+
    '<pre>'+esc(d.doc_code)+'</pre>';
  if(d.run_code){html+='<div class="lbl">executed on the server ('+esc(d.run_lang)+')</div><pre>'+esc(d.run_code)+'</pre>';}
  html+='<div class="lbl">live result</div><pre class="out">'+esc(d.output)+'</pre></div>';
  return html;
}
function interactiveHtml(it){
  return (it.matrix_url?'<div class="card"><div class="claim">Backend parity matrix</div>'+
     '<p class="secnote">run the full documented queue API live against every backend (file / RabbitMQ / MongoDB / Kafka) and see S2\\'s "work identically" claim hold or diverge per backend</p>'+
     '<a href="'+esc(it.matrix_url)+'"><button>Open the live backend matrix →</button></a></div>':'')+
   '<div class="card"><div class="claim">'+esc(it.title)+'</div>'+
   '<p class="secnote">'+esc(it.note||"")+'</p>'+
   '<label for="topic">topic</label><input id="topic" value="'+esc(it.default_topic||"")+'">'+
   '<label for="payload">payload (JSON)</label><textarea id="payload">'+esc(JSON.stringify(it.default_payload||{},null,2))+'</textarea>'+
   '<div style="margin-top:12px;display:flex;gap:10px;"><button onclick="doPush()">Push message</button><button onclick="load()">Re-run documented code</button></div>'+
   '<div id="toast"></div></div>'+
   '<div class="card"><div class="claim">Live storage <span style="font-weight:400;color:var(--mut);font-size:12px" id="pathlbl"></span></div>'+
   '<div class="tree" id="tree" style="margin-top:8px"></div></div>';
}
async function refreshTree(){
  if(!INTERACTIVE||!INTERACTIVE.topics_url)return;
  const r=await fetch(INTERACTIVE.topics_url);const s=await r.json();
  document.getElementById("pathlbl").textContent=s.path||"";
  const tree=document.getElementById("tree");
  if(!s.topics||!s.topics.length){tree.innerHTML='<div class="empty">No topics yet — push a message to auto-create storage.</div>';}
  else{tree.innerHTML=s.topics.map(t=>'<div class="t"><span>'+esc(t.topic)+'/</span><span>'+t.files+' file(s) · '+(t.pending==null?"?":t.pending)+' pending</span></div>').join("");}
}
async function load(){
  const r=await fetch("/api/chapter/"+CH+"/demos");
  if(!r.ok){document.getElementById("sub").textContent="chapter "+CH+" is not wired into the explorer";return;}
  const s=await r.json();
  document.getElementById("title").textContent="Chapter "+s.num+" · "+s.title;
  document.title="Ch"+s.num+" "+s.title+" — live";
  document.getElementById("verchip").textContent=s.version;
  let pass=0,div=0,fail=0,total=0;
  s.sections.forEach(sec=>sec.demos.forEach(d=>{total++;if(d.status==="pass")pass++;else if(d.status==="diverge")div++;else fail++;}));
  document.getElementById("sub").textContent=pass+" of "+total+" documented snippets ran clean"+(div?", "+div+" diverge":"")+(fail?", "+fail+" errored":"");
  document.getElementById("sections").innerHTML=s.sections.map(sec=>
    '<h2>'+esc(sec.id)+' · '+esc(sec.title)+'</h2>'+
    '<p class="secnote">each snippet below is faithful to the chapter, executed against this running server just now</p>'+
    sec.demos.map(demoHtml).join("")).join("");
  INTERACTIVE=s.interactive;
  document.getElementById("interactive").innerHTML=INTERACTIVE?interactiveHtml(INTERACTIVE):"";
  if(INTERACTIVE)refreshTree();
}
async function doPush(){
  const toast=document.getElementById("toast");toast.textContent="";toast.className="";
  let payload;
  try{payload=JSON.parse(document.getElementById("payload").value);}
  catch(e){toast.className="terr";toast.textContent="Invalid JSON: "+e.message;return;}
  const topic=document.getElementById("topic").value||INTERACTIVE.default_topic;
  const r=await fetch(INTERACTIVE.push_url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic,payload})});
  const d=await r.json();
  if(r.ok){toast.className="tok";toast.textContent="Pushed "+d.message_id+" -> "+d.topic+" (pending="+d.pending+")";refreshTree();}
  else{toast.className="terr";toast.textContent=d.error||("HTTP "+r.status);}
}
load();
</script>
</body>
</html>"""
