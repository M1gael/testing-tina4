# Queue backend matrix — USER-requested live showcase (NOT a verbatim doc impl).
#
# S2 claims (12-queues.md:70 / :422) that "the Queue class, push, pop, and consume
# work identically whether the backend is file, RabbitMQ, Kafka, or MongoDB." This
# view RUNS the full documented Chapter-12 queue API surface against EACH live
# backend and renders a grid so you can SEE, per documented claim, which backends
# uphold the promise and which diverge — everything a user would actually do.
#
#   GET /queue/backends                  -> the visual grid page
#   GET /api/queue/backends              -> meta (ops + backend reachability), fast
#   GET /api/queue/backends/{name}       -> run every op against one backend, live
#
# Each operation cites the documented claim + line it exercises. A broker that is
# unreachable shows as "blocked" (a logged blocker, never a false pass). Two claims
# carry an explicit doc caveat — priority (S5:208) and delay (S3:107) — so a broker
# difference THERE is "documented", not a divergence; everything else has no caveat,
# so any backend that differs is a real divergence (linked to a finding).
#
# Backend selection is process-global (TINA4_QUEUE_* env), so runs are serialised
# under a lock; each op runs in a daemon thread with a timeout so a Kafka call that
# blocks waiting for delivery (PY-12-02) can't hang the server.
import os
import socket
import shutil
import tempfile
import threading
import time
from importlib.metadata import version as _pkg_version

from tina4_python.core.router import get
from tina4_python.queue import Queue

_LOCK = threading.Lock()
_TOKEN = [0]
_ENV_KEYS = ("TINA4_QUEUE_BACKEND", "TINA4_QUEUE_URL", "TINA4_KAFKA_BROKERS",
             "TINA4_QUEUE_PATH", "TINA4_KAFKA_ASSIGN_TIMEOUT")


def _version():
    try:
        return "tina4-python " + _pkg_version("tina4-python")
    except Exception:
        return "tina4-python (unknown)"


def _tok():
    _TOKEN[0] += 1
    return f"{os.getpid()}_{_TOKEN[0]}"


def _reachable(host, port):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


BACKENDS = {
    "file": {"label": "file (LiteBackend)", "gate": lambda: True,
             "env": {"TINA4_QUEUE_BACKEND": "file"}},
    "rabbitmq": {"label": "RabbitMQ", "gate": lambda: _reachable("localhost", 5672),
                 "env": {"TINA4_QUEUE_BACKEND": "rabbitmq",
                         "TINA4_QUEUE_URL": "amqp://guest:guest@localhost:5672"}},
    "mongodb": {"label": "MongoDB", "gate": lambda: _reachable("localhost", 27017),
                "env": {"TINA4_QUEUE_BACKEND": "mongodb",
                        "TINA4_QUEUE_URL": "mongodb://localhost:27017/tina4"}},
    "kafka": {"label": "Kafka", "gate": lambda: _reachable("localhost", 9092),
              "env": {"TINA4_QUEUE_BACKEND": "kafka",
                      "TINA4_KAFKA_BROKERS": "localhost:9092",
                      "TINA4_KAFKA_ASSIGN_TIMEOUT": "1"}},
}
ORDER = ["file", "rabbitmq", "mongodb", "kafka"]


# ---- helpers used by the op runners ------------------------------------------

def _mk(name, **kw):
    """A fresh Queue on a unique topic under the currently-set backend env."""
    topic = f"mx_{name}_{_tok()}"
    return Queue(topic=topic, **kw), topic


def _drain(q, topic, limit=10):
    out = []
    for j in q.consume(topic, poll_interval=0):
        out.append(j.payload)
        j.complete()
        if len(out) >= limit:
            break
    return out


def _size_settle(q, status, want, tries=5):
    """Brokers can report size a beat late (settle race) — retry briefly so a
    transient 0 is not mistaken for a divergence."""
    n = q.size(status)
    for _ in range(tries):
        if n == want:
            return n
        time.sleep(0.3)
        n = q.size(status)
    return n


def _res(status, observed):
    return {"status": status, "observed": observed}


# ---- the documented operations a user actually performs ----------------------

def op_push(name):
    q, _ = _mk(name)
    mid = q.push({"to": "alice@example.com"})
    ok = isinstance(mid, str) and bool(mid)
    return _res("pass" if ok else "diverge", f"push() -> id={mid!r}")


def op_pop(name):
    q, _ = _mk(name)
    q.push({"to": "a@b.com"})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() returned None right after push (PY-12-02)")
    payload = j.payload
    j.complete()
    ok = payload.get("to") == "a@b.com"
    return _res("pass" if ok else "diverge", f"pop().payload={payload}")


def op_produce(name):
    q, _ = _mk(name)
    other = f"mx_{name}_other_{_tok()}"
    q.produce(other, {"x": 1})
    got = _drain(q, other)
    ok = got == [{"x": 1}]
    return _res("pass" if ok else "diverge", f"produce()->consume() drained={got}")


def op_drain(name):
    q, t = _mk(name)
    q.produce(t, {"n": 1})
    q.produce(t, {"n": 2})
    got = [p.get("n") for p in _drain(q, t)]
    ok = got == [1, 2]
    return _res("pass" if ok else "diverge", f"drain(poll_interval=0)={got}")


def op_iterations(name):
    q, t = _mk(name)
    for i in range(3):
        q.push({"n": i})
    c = 0
    for j in q.consume(t, iterations=2):
        c += 1
        j.complete()
    ok = c == 2
    return _res("pass" if ok else "diverge", f"consume(iterations=2) yielded {c}")


def op_priority(name):
    q, _ = _mk(name)
    q.push({"l": "normal"})
    q.push({"l": "urgent"}, priority=10)
    q.push({"l": "also"})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    first = j.payload.get("l")
    j.complete()
    if first == "urgent":
        return _res("pass", f"first pop = {first!r} (highest priority)")
    if name == "file":
        return _res("diverge", f"first pop = {first!r} (file must enforce priority)")
    return _res("docdiff", f"first pop = {first!r} (S5:208 — brokers' own semantics)")


def op_delay(name):
    q, _ = _mk(name)
    q.push({"l": "later"}, delay_seconds=60)
    q.push({"l": "ready"})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    first = j.payload.get("l")
    j.complete()
    if first == "ready":
        return _res("pass", f"first pop = {first!r} (delayed job hidden)")
    if name == "file":
        return _res("diverge", f"first pop = {first!r} (file must hide delayed)")
    return _res("docdiff", f"first pop = {first!r} (S3:107 — brokers' own timing)")


def op_size_pending(name):
    q, _ = _mk(name)
    q.push({"n": 1})
    q.push({"n": 2})
    n = _size_settle(q, "pending", 2)
    if n == 2:
        return _res("pass", "size('pending') = 2")
    return _res("diverge", f"size('pending') = {n} (expected 2; PY-12-02 on Kafka)")


def op_fail_dead(name):
    q, _ = _mk(name, max_retries=3)
    q.push({"job": "flaky"})
    fails = 0
    for _ in range(6):
        j = q.pop()
        if j is None:
            break
        j.fail("boom")
        fails += 1
    n = len(q.dead_letters())
    try:
        q.purge("pending")  # clear a perpetually-requeued job (RabbitMQ)
    except Exception:
        pass
    if n == 1:
        return _res("pass", f"failed {fails}x -> dead_letters()=1")
    note = " (BH-50)" if name == "rabbitmq" else (" (PY-12-02)" if name == "kafka" else "")
    return _res("diverge", f"failed {fails}x -> dead_letters()={n}{note}")


def op_failed(name):
    q, _ = _mk(name, max_retries=3)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("boom")
    f = q.failed()
    if isinstance(f, list) and len(f) >= 1:
        return _res("pass", f"failed() = {len(f)} (still-retrying)")
    return _res("diverge", f"failed() = {f!r} (attempts not persisted?)")


def op_dead_letters(name):
    q, _ = _mk(name, max_retries=1)
    q.push({"to": "bad@x.com"})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("smtp")
    dl = q.dead_letters()
    if dl and dl[0].payload.get("to") == "bad@x.com":
        return _res("pass", f"dead_letters()[0] Job, attempts={dl[0].attempts}")
    note = " (BH-50)" if name == "rabbitmq" else ""
    return _res("diverge", f"dead_letters() = {len(dl)}{note}")


def op_retry(name):
    q, _ = _mk(name, max_retries=1)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("x")
    q.retry()
    n = _size_settle(q, "pending", 1)
    if n == 1:
        return _res("pass", "retry() -> pending = 1")
    return _res("diverge", f"retry() -> pending = {n} (PY-12-03)")


def op_retry_id(name):
    q, _ = _mk(name, max_retries=1)
    q.push({"n": 1})
    q.push({"n": 2})
    for _ in range(2):
        j = q.pop()
        if j is None:
            break
        j.fail("x")
    dl = q.dead_letters()
    if not dl:
        return _res("diverge", "no dead letters to retry (PY-12-03/BH-50)")
    q.retry(dl[0].id)
    n = _size_settle(q, "pending", 1)
    if n == 1:
        return _res("pass", "retry(job_id) -> pending = 1")
    return _res("diverge", f"retry(job_id) -> pending = {n}")


def op_size_dead(name):
    q, _ = _mk(name, max_retries=1)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("x")
    n = q.size("dead")
    if n == 1:
        return _res("pass", "size('dead') = 1")
    note = " (BH-51)" if name in ("rabbitmq", "mongodb", "kafka") else ""
    return _res("diverge", f"size('dead') = {n}{note}")


def op_purge_pending(name):
    q, _ = _mk(name)
    q.push({"n": 1})
    q.push({"n": 2})
    q.purge("pending")
    n = _size_settle(q, "pending", 0)
    if n == 0:
        return _res("pass", "purge('pending') -> size = 0")
    return _res("diverge", f"purge('pending') -> size = {n}")


def op_purge_dead(name):
    q, _ = _mk(name, max_retries=1)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("x")
    before = len(q.dead_letters())
    if before == 0:
        return _res("na", "no dead letters on this backend to purge (see fail->dead)")
    q.purge("dead")
    after = len(q.dead_letters())
    return _res("pass" if after == 0 else "diverge",
                f"purge('dead'): dead_letters {before} -> {after}")


def op_reject(name):
    q, _ = _mk(name, max_retries=3)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.reject("nope")
    n = _size_settle(q, "pending", 1)
    if n == 1:
        return _res("pass", "reject() re-enqueued (alias of fail)")
    return _res("diverge", f"reject() -> pending = {n}")


def op_job_retry(name):
    q, _ = _mk(name, max_retries=1)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("x")
    dl = q.dead_letters()
    if not dl:
        return _res("diverge", "no dead job to retry (PY-12-03/BH-50)")
    dl[0].retry()
    n = _size_settle(q, "pending", 1)
    still = any(j.id == dl[0].id for j in q.dead_letters())
    if n == 1 and not still:
        return _res("pass", "job.retry() -> pending = 1 (moved out of dead)")
    if n == 1 and still:
        return _res("diverge", "job.retry() left a dead-letter DUPLICATE (PY-12-05)")
    return _res("diverge", f"job.retry() -> pending = {n}")


def op_retry_all(name):
    q, _ = _mk(name, max_retries=1)
    for v in range(3):
        q.push({"n": v})
    for _ in range(3):
        j = q.pop()
        if j is None:
            break
        j.fail("x")
    dead0 = len(q.dead_letters())
    if dead0 == 0:
        return _res("diverge", "no dead letters to revive (PY-12-03/BH-50)")
    q.retry()  # doc S7:312 — "Re-queue every dead-letter job"
    pend = _size_settle(q, "pending", dead0)
    if pend == dead0:
        return _res("pass", f"retry() revived all {dead0}")
    note = " (PY-12-04)" if name == "file" else ""
    return _res("diverge", f"retry() revived {pend} of {dead0}{note}")


def op_size_failed(name):
    q, _ = _mk(name, max_retries=3)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("boom")
    f = len(q.failed())
    sf = q.size("failed")
    if f == sf:
        return _res("pass", f"failed()={f}, size('failed')={sf}")
    note = " (PY-12-06)" if name == "file" else ""
    return _res("diverge", f"failed()={f} but size('failed')={sf}{note}")


def op_consume_continuous(name):
    q, t = _mk(name)
    q.push({"n": 1})
    got = None
    for j in q.consume(t):  # default poll — the S4 headline worker loop
        got = j.payload
        j.complete()
        break
    if got and got.get("n") == 1:
        return _res("pass", "consume() worker loop delivered the job")
    return _res("diverge", f"consume() delivered {got!r}")


def op_consume_job_id(name):
    q, t = _mk(name)
    mid = q.push({"pick": "me"})
    q.push({"pick": "no"})
    got = [j.payload for j in q.consume(t, job_id=mid)]
    if got == [{"pick": "me"}]:
        return _res("pass", "consume(job_id) yielded the target job")
    return _res("diverge", f"consume(job_id) yielded {got} (PY-12-07: pop_by_id is file-only)")


def op_consume_batch(name):
    q, t = _mk(name)
    for i in range(2):
        q.push({"n": i})
    batch = None
    for jobs in q.consume(t, batch_size=2, poll_interval=0):
        batch = jobs
        for j in jobs:
            j.complete()
        break
    n = len(batch) if batch else 0
    if n == 2:
        return _res("pass", "consume(batch_size=2) yielded a list of 2")
    return _res("diverge", f"consume(batch_size=2) yielded {n}")


def op_process(name):
    q, t = _mk(name)
    for i in range(2):
        q.push({"n": i})
    seen = []

    def handler(job):
        seen.append(job.payload)
        job.complete()

    q.process(handler, max_jobs=2)
    if len(seen) == 2:
        return _res("pass", "process(handler, max_jobs=2) handled 2 jobs")
    return _res("diverge", f"process() handled {len(seen)} of 2")


def op_pop_batch(name):
    q, t = _mk(name)
    for i in range(3):
        q.push({"n": i})
    jobs = q.pop_batch(2)
    n = len(jobs)
    for j in jobs:
        j.complete()
    if n == 2:
        return _res("pass", "pop_batch(2) returned 2 jobs")
    return _res("diverge", f"pop_batch(2) returned {n}")


def op_pop_by_id(name):
    q, t = _mk(name)
    mid = q.push({"pick": "me"})
    q.push({"pick": "no"})
    j = q.pop_by_id(mid)
    if j is not None and j.payload.get("pick") == "me":
        j.complete()
        return _res("pass", "pop_by_id returned the target job")
    note = " (file-only — PY-12-07)" if name != "file" else ""
    return _res("diverge", f"pop_by_id returned None{note}")


def op_clear_fresh(name):
    q, t = _mk(name)
    try:
        n = q.clear()  # on a fresh (never-connected) queue
        return _res("pass", f"clear() on a fresh queue returned {n!r}")
    except Exception as e:  # noqa: BLE001
        note = " (BH-52)" if name == "mongodb" else ""
        return _res("error", f"{type(e).__name__}: {e}{note}")


def op_get_topic(name):
    q, t = _mk(name)
    ok = q.get_topic() == t
    return _res("pass" if ok else "diverge", f"get_topic() = {q.get_topic()!r}")


def op_retry_backoff(name):
    q, _ = _mk(name, max_retries=5, retry_backoff=1)
    q.push({"n": 1})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    j.fail("boom")
    held = q.pop() is None  # file: held during the backoff window
    if name == "file":
        time.sleep(1.3)
        released = q.pop() is not None
        if held and released:
            return _res("pass", "retry_backoff held then released the job")
        return _res("diverge", f"held={held}, released={released}")
    return _res("docdiff" if not held else "pass",
                f"held={held} (S7:273 — retry_backoff applies to the file backend)")


def op_job_serialize(name):
    q, t = _mk(name)
    q.push({"to": "a@b.com"})
    j = q.pop()
    if j is None:
        return _res("diverge", "pop() None (PY-12-02)")
    out = j.to_json()
    j.complete()
    ok = isinstance(out, str) and "a@b.com" in out
    return _res("pass" if ok else "diverge", f"job.to_json() carries the payload = {ok}")


OPS = [
    ("push", "push() returns a message id", "S3", op_push),
    ("pop", "pop() round-trips the payload, then complete()", "S4", op_pop),
    ("produce", "produce()/consume() across topics", "S10", op_produce),
    ("drain", "consume(poll_interval=0) drains once", "S4", op_drain),
    ("iterations", "consume(iterations=N) stops after N", "S4", op_iterations),
    ("priority", "priority: highest first (caveat S5:208)", "S5", op_priority),
    ("delay", "delay_seconds hidden (caveat S3:107)", "S3", op_delay),
    ("size_pending", "size('pending') counts waiting jobs", "S3", op_size_pending),
    ("fail_dead", "fail -> retry -> dead-letter", "S7", op_fail_dead),
    ("failed", "failed() lists still-retrying jobs", "S7", op_failed),
    ("dead_letters", "dead_letters() returns Job objects", "S7", op_dead_letters),
    ("retry", "retry() revives a dead letter", "S7", op_retry),
    ("retry_all", "retry() re-queues EVERY dead letter", "S7", op_retry_all),
    ("retry_id", "retry(job_id) revives one specific", "S7", op_retry_id),
    ("size_dead", "size('dead') counts dead letters", "S7", op_size_dead),
    ("size_failed", "size('failed') matches failed()", "S7", op_size_failed),
    ("purge_pending", "purge('pending') drops waiting", "S7", op_purge_pending),
    ("purge_dead", "purge('dead') clears dead store", "S7", op_purge_dead),
    ("reject", "job.reject() aliases fail()", "S6", op_reject),
    ("job_retry", "job.retry() re-queues a job", "S6", op_job_retry),
    # --- the rest of what an average user reaches for -------------------------
    ("consume_cont", "consume() worker loop delivers a job", "S4", op_consume_continuous),
    ("consume_jobid", "consume(job_id) yields one specific job", "S4", op_consume_job_id),
    ("retry_backoff", "retry_backoff holds the re-enqueue", "S7", op_retry_backoff),
    ("consume_batch", "consume(batch_size=N) yields a list", "API", op_consume_batch),
    ("process", "process(handler, max_jobs=N) drains", "API", op_process),
    ("pop_batch", "pop_batch(N) returns up to N jobs", "API", op_pop_batch),
    ("pop_by_id", "pop_by_id(id) returns a specific job", "API", op_pop_by_id),
    ("clear_fresh", "clear() on a fresh queue", "API", op_clear_fresh),
    ("get_topic", "get_topic() returns the topic", "API", op_get_topic),
    ("job_json", "job.to_json() serialises the job", "API", op_job_serialize),
]


def _run_op(fn, name, timeout=6):
    """Run one op in a daemon thread; a Kafka call that blocks on delivery can't
    hang the request — it returns a timeout divergence instead."""
    box = {}

    def worker():
        try:
            box["r"] = fn(name)
        except Exception as e:  # noqa: BLE001 — surface any framework error as a cell
            box["r"] = _res("error", f"{type(e).__name__}: {e}")

    th = threading.Thread(target=worker, daemon=True)
    th.start()
    th.join(timeout)
    if th.is_alive():
        return _res("diverge", f"timed out >{timeout}s (no delivery — PY-12-02)")
    return box.get("r", _res("error", "no result"))


def _run_backend(name):
    cfg = BACKENDS[name]
    if not cfg["gate"]():
        return {"label": cfg["label"], "reachable": False, "elapsed": 0.0,
                "results": {oid: _res("blocked", "broker unreachable")
                            for oid, *_ in OPS}}
    with _LOCK:
        prior = dict(os.environ)
        tmp = None
        t0 = time.monotonic()
        try:
            for k in _ENV_KEYS:
                os.environ.pop(k, None)
            if name == "file":
                tmp = tempfile.mkdtemp(prefix="mx_file_")
                os.environ["TINA4_QUEUE_PATH"] = tmp
            os.environ.update(cfg["env"])
            results = {oid: _run_op(fn, name) for oid, _t, _d, fn in OPS}
        finally:
            os.environ.clear()
            os.environ.update(prior)
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
        elapsed = round(time.monotonic() - t0, 1)
    return {"label": cfg["label"], "reachable": True, "elapsed": elapsed,
            "results": results}


def _meta():
    return {
        "version": _version(),
        "ops": [{"id": o[0], "title": o[1], "doc": o[2]} for o in OPS],
        "backends": [{"name": n, "label": BACKENDS[n]["label"],
                      "reachable": BACKENDS[n]["gate"]()} for n in ORDER],
    }


@get("/api/queue/backends")
async def api_backends_meta(request, response):
    return response(_meta())


@get("/api/queue/backends/{name}")
async def api_backends_run(name, request, response):
    if name not in BACKENDS:
        return response({"error": f"unknown backend {name!r}"}, 404)
    return response({"backend": name, **_run_backend(name)})


@get("/queue/backends")
async def queue_backends_page(request, response):
    return response.html(PAGE)


PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Queue backends — live parity matrix</title>
<style>
 :root{--bg:#fafaf7;--card:#fff;--bd:#e6e4da;--tx:#26251f;--mut:#6b6a62;--hint:#9a988e;
       --ok:#3b6d11;--okbg:#eaf3de;--warn:#854f0b;--warnbg:#faeeda;--err:#a32d2d;--errbg:#fcebeb;
       --na:#8a887e;--nabg:#f0efe8;}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
 .wrap{max-width:1080px;margin:0 auto;padding:26px 20px 70px;}
 a.back{color:var(--mut);font-size:13px;text-decoration:none;} a.back:hover{color:var(--tx);}
 h1{font-size:21px;font-weight:600;margin:6px 0 2px;}
 .sub{color:var(--mut);font-size:13px;margin:0 0 6px;}
 .claim{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px 14px;margin:12px 0 16px;font-size:14px;}
 .claim b{font-weight:600;}
 table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:hidden;}
 th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--bd);vertical-align:top;font-size:13px;}
 th{background:#f3f1ea;font-weight:600;position:sticky;top:0;}
 td.op{min-width:230px;} .op .t{font-weight:600;} .op .d{color:var(--hint);font-size:11px;}
 .bk{min-width:170px;}
 .cell{display:flex;flex-direction:column;gap:3px;}
 .badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 7px;border-radius:6px;width:max-content;}
 .b-pass{color:var(--ok);background:var(--okbg);} .b-docdiff{color:var(--warn);background:var(--warnbg);}
 .b-diverge{color:var(--err);background:var(--errbg);} .b-error{color:var(--err);background:var(--errbg);}
 .b-blocked{color:var(--na);background:var(--nabg);} .b-na{color:var(--na);background:var(--nabg);}
 .b-run{color:var(--mut);background:var(--nabg);}
 .obs{color:var(--mut);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;line-height:1.4;}
 .colhead .lab{font-size:14px;} .colhead .meta{font-weight:400;color:var(--mut);font-size:11px;}
 .legend{margin:14px 0;font-size:12px;color:var(--mut);display:flex;gap:14px;flex-wrap:wrap;}
 .legend span{display:inline-flex;align-items:center;gap:5px;}
 .dot{width:10px;height:10px;border-radius:3px;display:inline-block;}
 .sumrow td{background:#f9f7f0;font-weight:600;}
</style></head>
<body><div class="wrap">
 <a class="back" href="/chapter/12">&larr; Chapter 12 · Queues</a>
 <h1>Queue backends · live parity matrix</h1>
 <p class="sub" id="ver">running the full documented API against every live backend…</p>
 <div class="claim">
   <b>S2 / S9 claim (12-queues.md):</b> "the <code>Queue</code> class, <code>push</code>, <code>pop</code>, and
   <code>consume</code> work identically whether the backend is file, RabbitMQ, Kafka, or MongoDB."
   Every row below is that promise, exercised live just now against each running broker.
   Rows tagged <b>S3–S10</b> are documented Chapter-12 claims; rows tagged <b>API</b> are public
   methods a user can reach for that the chapter does not show (extended coverage: process(),
   pop_batch(), pop_by_id(), consume(batch_size=), clear(), get_topic(), job.to_json()).
 </div>
 <div class="legend">
   <span><span class="dot" style="background:var(--okbg)"></span>works as documented</span>
   <span><span class="dot" style="background:var(--warnbg)"></span>documented difference (S5:208 / S3:107)</span>
   <span><span class="dot" style="background:var(--errbg)"></span>diverges (finding)</span>
   <span><span class="dot" style="background:var(--nabg)"></span>blocked / n-a</span>
 </div>
 <table id="grid"><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table>
</div>
<script>
const BADGE={pass:"works",docdiff:"documented diff",diverge:"diverges",error:"error",blocked:"broker down",na:"n/a",run:"running…"};
function esc(x){return String(x).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
let META=null;
function cellHtml(r){
 if(!r)return '<div class="cell"><span class="badge b-run">running…</span></div>';
 return '<div class="cell"><span class="badge b-'+r.status+'">'+(BADGE[r.status]||r.status)+'</span>'+
        '<span class="obs">'+esc(r.observed||"")+'</span></div>';
}
async function load(){
 META=await (await fetch("/api/queue/backends")).json();
 document.getElementById("ver").textContent=META.version+" · "+META.backends.filter(b=>b.reachable).length+" of "+META.backends.length+" backends reachable";
 let head='<th>Operation (documented)</th>';
 META.backends.forEach(b=>head+='<th class="bk colhead" id="h_'+b.name+'"><div class="lab">'+esc(b.label)+'</div><div class="meta">'+(b.reachable?"reachable":"unreachable")+'</div></th>');
 document.getElementById("head").innerHTML=head;
 let body='';
 META.ops.forEach(o=>{
   body+='<tr><td class="op"><div class="t">'+esc(o.title)+'</div><div class="d">'+esc(o.doc)+'</div></td>';
   META.backends.forEach(b=>body+='<td class="bk" id="c_'+b.name+'_'+o.id+'">'+cellHtml(null)+'</td>');
   body+='</tr>';
 });
 // summary row
 body+='<tr class="sumrow"><td>verdict · works / documented-diff / diverges</td>';
 META.backends.forEach(b=>body+='<td id="sum_'+b.name+'">…</td>');
 body+='</tr>';
 document.getElementById("body").innerHTML=body;
 META.backends.forEach(b=>runBackend(b));
}
async function runBackend(b){
 if(!b.reachable){
   META.ops.forEach(o=>{document.getElementById("c_"+b.name+"_"+o.id).innerHTML=cellHtml({status:"blocked",observed:"broker unreachable"});});
   document.getElementById("sum_"+b.name).textContent="blocked";
   return;
 }
 try{
   const d=await (await fetch("/api/queue/backends/"+b.name)).json();
   let pass=0,doc=0,div=0;
   META.ops.forEach(o=>{
     const r=d.results[o.id];
     document.getElementById("c_"+b.name+"_"+o.id).innerHTML=cellHtml(r);
     if(r.status==="pass")pass++;else if(r.status==="docdiff")doc++;else if(r.status==="diverge"||r.status==="error")div++;
   });
   document.getElementById("h_"+b.name).querySelector(".meta").textContent="ran in "+d.elapsed+"s";
   document.getElementById("sum_"+b.name).textContent=pass+" / "+doc+" / "+div;
 }catch(e){
   document.getElementById("sum_"+b.name).textContent="error: "+e.message;
 }
}
load();
</script></body></html>"""
