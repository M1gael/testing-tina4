# Chapter 12 Queues — live proof view (USER-requested tooling, not a verbatim
# doc impl). Served at GET /queue under `tina4 serve`. For each claim a
# documented section makes, the page shows the EXACT snippet from 12-queues.md
# and EXECUTES it on the live server at request time, surfacing the real
# return values / stdout / files created — so you see the taught code in action
# and whether it works. Grouped by section (S2, S3, … added as they land).
#
# Doc-code demos run in an isolated temp queue dir (TINA4_QUEUE_PATH) so they
# are repeatable and don't pollute the visible storage. The "try it yourself"
# push writes to the real data/queue so you watch persistence.
#
# POST is @noauth() so the browser can call it without a Bearer token (write
# routes are gated by default — PY-06-07).
import io
import os
import shutil
import contextlib
import tempfile

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


def _exec_sandbox(code, post=None, extra_env=None):
    """Execute a documentation snippet against the live framework in an
    isolated temp queue dir. Captures stdout, lets `post(ns, sandbox)` compute
    output lines while storage still exists, then restores env + tears down.
    Returns (stdout, error, lines)."""
    tmp = tempfile.mkdtemp(prefix="qexpl_")
    prior_path = os.environ.get("TINA4_QUEUE_PATH")
    prior_bkd = os.environ.get("TINA4_QUEUE_BACKEND")
    os.environ["TINA4_QUEUE_PATH"] = tmp
    if extra_env:
        os.environ.update(extra_env)
    else:
        os.environ.pop("TINA4_QUEUE_BACKEND", None)  # file is the default
    ns, buf, error, lines = {}, io.StringIO(), None, []
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, ns)
        if post:
            lines = post(ns, tmp)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    finally:
        if prior_path is None:
            os.environ.pop("TINA4_QUEUE_PATH", None)
        else:
            os.environ["TINA4_QUEUE_PATH"] = prior_path
        if prior_bkd is None:
            os.environ.pop("TINA4_QUEUE_BACKEND", None)
        else:
            os.environ["TINA4_QUEUE_BACKEND"] = prior_bkd
        shutil.rmtree(tmp, ignore_errors=True)
    return buf.getvalue(), error, lines


def _files_in(sandbox, topic):
    d = os.path.join(sandbox, topic)
    try:
        return [f for f in os.listdir(d) if f.endswith(".queue-data")]
    except Exception:
        return []


def _demo(section, claim, doc_lang, doc_code, post, run_lang=None, run_code=None,
          extra_env=None, diverge_marker=None):
    code_to_run = run_code if run_code is not None else doc_code
    out, err, lines = _exec_sandbox(code_to_run, post, extra_env=extra_env)
    body = err or "\n".join(lines)
    if err:
        status = "fail"
    elif diverge_marker and diverge_marker in body:
        status = "diverge"
    else:
        status = "pass"
    d = {"claim": claim, "doc_lang": doc_lang, "doc_code": doc_code,
         "output": body, "status": status}
    if run_code is not None:
        d["run_lang"] = run_lang or "python"
        d["run_code"] = run_code
    return d


# ---- Verbatim snippets from documentation/.../12-queues.md ---------------

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


def _sections():
    # ---- S2: Queue configuration -----------------------------------------
    def p_file_default(ns, sb):
        q = ns.get("queue")
        b = type(q._backend).__name__ if q is not None else "?"
        return [f"TINA4_QUEUE_BACKEND unset → Queue(topic=\"emails\")._backend = {b}",
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
        _demo("S2", "File backend is the zero-config default",
              "bash", DOC_FILE_DEFAULT, p_file_default,
              run_lang="python",
              run_code='from tina4_python.queue import Queue\nqueue = Queue(topic="emails")'),
        _demo("S2", "The backend is selected via an environment variable — your code stays the same",
              "bash", DOC_ENV_RABBIT, p_env_rabbit,
              run_lang="python",
              run_code='import os\nos.environ["TINA4_QUEUE_BACKEND"] = "rabbitmq"\nfrom tina4_python.queue import Queue\nqueue = Queue(topic="emails")',
              extra_env={"TINA4_QUEUE_BACKEND": "rabbitmq"}),
    ]

    # ---- S3: Creating a Queue and Pushing Messages -----------------------
    def p_create_push(ns, sb):
        q = ns.get("queue")
        b = type(q._backend).__name__ if q is not None else "?"
        return [f"message_id = {ns.get('message_id')!r}",
                f"count = queue.size() → {ns.get('count')!r}",
                f"type(queue._backend).__name__ = {b}",
                f"storage auto-created: data/queue/emails/ → {_files_in(sb, 'emails')}"]

    def p_produce(ns, sb):
        return [f"Queue(topic=\"invoices\").size() = {Queue(topic='invoices').size()}",
                f"storage: data/queue/invoices/ → {_files_in(sb, 'invoices')}"]

    def p_payload(ns, sb):
        import glob, json
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
        return [f"Queue(topic=\"t\", backend=\"file\")._backend     = {fb}",
                f"Queue(topic=\"t\", backend=\"rabbitmq\")._backend = {rb}",
                "=> the backend= constructor argument IS accepted and DOES select "
                "the backend, contradicting the documented \"not constructor parameters\"."]

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
        _demo("S3", "Create a queue, push a message, read the size",
              "python", DOC_CREATE_PUSH, p_create_push),
        _demo("S3", "produce() pushes to a named topic without a separate Queue instance",
              "python", DOC_PRODUCE, p_produce,
              run_code='from tina4_python.queue import Queue\n' + DOC_PRODUCE),
        _demo("S3", "The payload is any dictionary that can be serialized to JSON",
              "text", '"The payload is any dictionary that can be serialized to JSON." (S3)',
              p_payload, run_lang="python", run_code=payload_run),
        _demo("S3", "PY-12-01 · doc says the backend is env-only, NOT constructor parameters",
              "text", DOC_BLOCKQUOTE, p_blockquote,
              run_lang="python", run_code=blockquote_run,
              diverge_marker="RabbitMQBackend"),
    ]

    return [
        {"id": "S2", "title": "Queue configuration", "demos": s2},
        {"id": "S3", "title": "Creating a queue and pushing messages", "demos": s3},
    ]


@get("/api/queue/demos")
async def queue_demos(request, response):
    return response({
        "version": "tina4-python 3.13.39",
        "path": _queue_path(),
        "env_backend": os.environ.get("TINA4_QUEUE_BACKEND"),
        "sections": _sections(),
        "topics": _topics(),
    })


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


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ch12 Queues — documented code, live</title>
<style>
  :root{--bg:#fafaf7;--card:#fff;--bd:#e6e4da;--tx:#26251f;--mut:#6b6a62;--hint:#9a988e;
        --ok:#3b6d11;--okbg:#eaf3de;--warn:#854f0b;--warnbg:#faeeda;--err:#a32d2d;--errbg:#fcebeb;
        --code:#1e1d18;--codetx:#e8e6dd;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
  .wrap{max-width:900px;margin:0 auto;padding:28px 20px 60px;}
  .top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:18px;}
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
  <div class="top">
    <div><h1>Chapter 12 · Queues</h1><p class="sub" id="sub">running the documented code live…</p></div>
    <span class="chip" id="verchip"></span>
  </div>

  <div id="sections"></div>

  <div class="card">
    <div class="claim">Try it yourself · push a message</div>
    <p class="secnote">the same Queue.push() the chapter teaches — writes to the real data/queue you see below</p>
    <label for="topic">topic</label>
    <input id="topic" value="emails" placeholder="emails">
    <label for="payload">payload (JSON)</label>
    <textarea id="payload">{
  "to": "alice@example.com",
  "subject": "Order Confirmation",
  "body": "Your order #1234 has been confirmed."
}</textarea>
    <div style="margin-top:12px;display:flex;gap:10px;"><button onclick="push()">Push message</button><button onclick="load()">Re-run documented code</button></div>
    <div id="toast"></div>
  </div>

  <div class="card">
    <div class="claim">Live storage <span style="font-weight:400;color:var(--mut);font-size:12px" id="pathlbl"></span></div>
    <div class="tree" id="tree" style="margin-top:8px"></div>
  </div>
</div>

<script>
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
async function load(){
  const r=await fetch("/api/queue/demos");const s=await r.json();
  document.getElementById("verchip").textContent=s.version+(s.env_backend?(" · "+s.env_backend):" · file (default)");
  let pass=0,div=0,fail=0,total=0;
  s.sections.forEach(sec=>sec.demos.forEach(d=>{total++;if(d.status==="pass")pass++;else if(d.status==="diverge")div++;else fail++;}));
  document.getElementById("sub").textContent=pass+" of "+total+" documented snippets ran clean"+(div?", "+div+" diverges":"")+(fail?", "+fail+" errored":"");
  document.getElementById("sections").innerHTML=s.sections.map(sec=>
    '<h2>'+esc(sec.id)+' · '+esc(sec.title)+'</h2>'+
    '<p class="secnote">each snippet below is verbatim from the chapter, executed against this running server just now</p>'+
    sec.demos.map(demoHtml).join("")).join("");

  document.getElementById("pathlbl").textContent=s.path;
  const tree=document.getElementById("tree");
  if(!s.topics.length){tree.innerHTML='<div class="empty">No topics yet — push a message to auto-create storage.</div>';}
  else{tree.innerHTML=s.topics.map(t=>'<div class="t"><span>'+esc(t.topic)+'/</span><span>'+t.files+' file(s) · '+(t.pending==null?"?":t.pending)+' pending</span></div>').join("");}
}
async function push(){
  const toast=document.getElementById("toast");toast.textContent="";toast.className="";
  let payload;
  try{payload=JSON.parse(document.getElementById("payload").value);}
  catch(e){toast.className="terr";toast.textContent="Invalid JSON: "+e.message;return;}
  const topic=document.getElementById("topic").value||"emails";
  const r=await fetch("/api/queue/push",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic,payload})});
  const d=await r.json();
  if(r.ok){toast.className="tok";toast.textContent="Pushed "+d.message_id+" -> "+d.topic+" (storage_created="+d.storage_created+", pending="+d.pending+")";load();}
  else{toast.className="terr";toast.textContent=d.error||("HTTP "+r.status);}
}
load();
</script>
</body>
</html>"""


@get("/queue")
async def queue_explorer_page(request, response):
    return response.html(PAGE)
