# Runs the tina4-php chapter examples named in ledger d-misc-02 against a real tina4-php tree.
# usage: prove.py <docs/php dir> <tina4-php tree> <port>     (prove.sh supplies all three)
# Each case prints PASS/FAIL with what the framework actually did; exit 1 on any FAIL.
import base64, json, os, re, shutil, signal, socket, subprocess, sys, tempfile, time, urllib.request, urllib.error, http.cookiejar

DOCS, TREE, PORT = sys.argv[1], sys.argv[2], int(sys.argv[3])
HERE = os.path.dirname(os.path.abspath(__file__)); APP = os.path.join(HERE, "app")
ROUTES = os.path.join(APP, "src", "routes"); TPL = os.path.join(APP, "src", "templates")
SECRET = "0123456789abcdef0123456789abcdef0123456789abcdef"
results = []

def doc(name): return open(os.path.join(DOCS, name)).read()

def block(name, marker, nth=1):
    """nth fenced block of docs/php/<name> whose text contains marker, verbatim."""
    blocks = re.findall(r"^```[a-z]*\n(.*?)^```", doc(name), re.S | re.M)
    hits = [b for b in blocks if marker in b]
    if len(hits) < nth: raise SystemExit(f"{name}: no block #{nth} containing {marker!r}")
    return hits[nth - 1]

def section_block(name, heading, nth):
    """nth fenced block under the heading line `heading` (up to the next heading of any level)"""
    text = doc(name).split("\n" + heading + "\n", 1)[1]
    text = re.split(r"^#{1,6} ", text, flags=re.M)[0]
    return re.findall(r"^```[a-z]*\n(.*?)^```", text, re.S | re.M)[nth - 1]

def body(php): return re.sub(r"^<\?php\s*\n", "", php)

def check(case, ok, detail):
    results.append(ok); print(f"{'PASS' if ok else 'FAIL'} {case}: {detail}")

def cli(php, env=None):
    """run a doc block as a script against the tree's autoloader"""
    f = tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, dir=APP)
    f.write(f"<?php\nrequire '{TREE}/vendor/autoload.php';\n" + body(php)); f.close()
    e = dict(os.environ, HOME=tempfile.mkdtemp(), **(env or {}))
    p = subprocess.run(["php", "-d", "display_errors=stderr", f.name], cwd=APP, env=e, capture_output=True, text=True, timeout=60)
    os.unlink(f.name); return p.returncode, (p.stdout + p.stderr).strip()

# ---------- server ----------
def busy():
    s = socket.socket(); s.settimeout(0.5)
    try: return s.connect_ex(("127.0.0.1", PORT)) == 0
    finally: s.close()

class Server:
    def __init__(self, routes, env=None, dotenv="TINA4_DEBUG=false\n"):
        shutil.rmtree(ROUTES, ignore_errors=True); os.makedirs(ROUTES)
        for n, src in routes.items(): open(os.path.join(ROUTES, n), "w").write(src)
        open(os.path.join(ROUTES, "zz_fixture.php"), "w").write(FIXTURE)
        open(os.path.join(APP, ".env"), "w").write(dotenv)
        if busy(): raise SystemExit(f"PORT {PORT} BUSY before start")
        e = dict(os.environ, HOME=tempfile.mkdtemp(), TINA4_OVERRIDE_CLIENT="true", TINA4_SECRET=SECRET, **(env or {}))
        self.log = open(os.path.join(HERE, "server.log"), "w")
        self.p = subprocess.Popen(["php", f"{TREE}/bin/tina4php", "serve", f"127.0.0.1:{PORT}"], cwd=APP, env=e, stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(80):
            if self.p.poll() is not None: break
            if busy(): break
            time.sleep(0.25)
        self.up = self.p.poll() is None and busy()
    def stop(self):
        if self.p.poll() is None: self.p.send_signal(signal.SIGTERM); self.p.wait(timeout=40)
        for _ in range(80):
            if not busy(): break
            time.sleep(0.25)
        else: print(f"PORT {PORT} STILL BUSY after stop")
        self.log.close()
    def errors(self):
        return "; ".join(sorted(set(re.findall(r'"level":"ERROR","message":"([^"]{0,140})', open(os.path.join(HERE, "server.log")).read()))))
    def tail(self): return open(os.path.join(HERE, "server.log")).read()[-400:].replace("\n", " ")

FIXTURE = r'''<?php
\Tina4\Router::get("/posts/1", fn($rq, $rs) => $rs->json(["id" => 1, "title" => "t"]));
\Tina4\Router::get("/users/1", fn($rq, $rs) => $rs->json(["id" => 1, "name" => "Leanne", "email" => "l@x.io"]));
\Tina4\Router::get("/ping", fn($rq, $rs) => $rs->json(["ok" => 1]));
'''

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None

def opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(NoRedirect, urllib.request.HTTPCookieProcessor(jar))

def token():
    rc, out = cli("echo \\Tina4\\Auth::getToken(['user_id' => 1]);", {"TINA4_SECRET": SECRET})
    return out.splitlines()[-1]

def req(op, path, method="GET", data=None, ctype=None, tok=None):
    r = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=data, method=method)
    if ctype: r.add_header("Content-Type", ctype)
    if tok: r.add_header("Authorization", "Bearer " + tok)
    try:
        resp = op.open(r, timeout=30); return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

def ws_echo(path, text):
    s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
    hs = b""
    while b"\r\n\r\n" not in hs: hs += s.recv(4096)
    if b" 101 " not in hs.split(b"\r\n")[0]: return "handshake " + hs.split(b"\r\n")[0].decode()
    rest = hs.split(b"\r\n\r\n", 1)[1]
    m = os.urandom(4); p = text.encode()
    s.sendall(bytes([0x81, 0x80 | len(p)]) + m + bytes(b ^ m[i % 4] for i, b in enumerate(p)))
    buf = rest
    try:
        while True:
            while len(buf) >= 2:
                n = buf[1] & 0x7f; h = 2
                if n == 126: n = int.from_bytes(buf[2:4], "big"); h = 4
                if len(buf) < h + n: break
                op, payload, buf = buf[0] & 0x0f, buf[h:h + n], buf[h + n:]
                if op == 1: s.close(); return payload.decode()
            buf += s.recv(4096)
    except socket.timeout:
        s.close(); return "no reply within 5s"

# =============== cases ===============
os.makedirs(TPL, exist_ok=True)
for d in ("data", "public"): shutil.rmtree(os.path.join(APP, d), ignore_errors=True)
os.makedirs(os.path.join(APP, "data", "reports"))
PDF = b"%PDF-1.4 doc-example\n"
open(os.path.join(APP, "data", "reports", "q1.pdf"), "wb").write(PDF)
REAL_PDF = os.path.join(APP, "data", "reports", "q1.pdf")
open(os.path.join(TPL, "dashboard.html"), "w").write("hello {{ user_name }}")
open(os.path.join(TPL, "contact.html"), "w").write("{% if flash %}{{ flash.type }}:{{ flash.message }}{% endif %}|")

# --- 1. Tina4\Database: the class the chapters import ---
rc, out = cli("var_export([class_exists('Tina4\\Database'), class_exists('Tina4\\Database\\Database')]);")
check("db: class_exists(Tina4\\Database, Tina4\\Database\\Database)", out.endswith("array (\n  0 => false,\n  1 => true,\n)") or "0 => false" in out and "1 => true" in out, out.replace("\n", " "))
stale = []
for n in sorted(os.listdir(DOCS)):
    if not n.endswith(".md") or n.startswith("36-releases"): continue  # release notes record history
    for i, line in enumerate(doc(n).splitlines(), 1):
        if re.search(r"Tina4\\Database(?![\\\w])", line): stale.append(f"{n}:{i}")
check("db: chapters naming Tina4\\Database (no such class)", not stale, f"{len(stale)} refs {stale[:4]}{'...' if len(stale) > 4 else ''}")

# --- the server-side cases share one boot ---
routes = {
    "db.php": block("05-database.md", '"/api/test-db"'),
    "session.php": block("08-authentication.md", '"/login-form"'),
    "contact.php": block("16-email.md", 'Router::get("/contact"'),
    "reports.php": block("03-request-response.md", '"/api/reports/{filename}"'),
    "images.php": block("03-request-response.md", '"/api/images/{filename}"'),
    "ws.php": block("23-websocket.md", '"/ws/echo"'),
    "frag.php": "<?php\n\\Tina4\\Router::get('/frag/dl8', function ($request, $response) {\n    $filepath = '" + REAL_PDF + "';\n    "
                + body(section_block("03-request-response.md", "## 8. File Downloads", 2)).strip()
                + "\n});\n\\Tina4\\Router::get('/frag/dl3', function ($request, $response) {\n    "
                + body(section_block("03-request-response.md", "### file() -- File Download Response", 2)).strip().replace("/path/to/report.pdf", REAL_PDF)
                + "\n});\n",
}
srv = Server(routes, env={"TINA4_DATABASE_URL": "sqlite:///data/app.db"})
if not srv.up:
    check("server boot", False, srv.tail()); print("VERDICT"); sys.exit(2)
try:
    tok = token(); op = opener()
    # --- Database::getConnection() through the import the chapter uses ---
    c, h, b = req(op, "/api/test-db")
    check("db: 05 §3 GET /api/test-db", c == 200 and b"answer" in b, f"{c} {b[:120]!r}")
    # --- 2. $request->session[...] ---
    op = opener()
    c1, _, b1 = req(op, "/login-form", "POST", b"{}", "application/json", tok)
    c2, _, b2 = req(op, "/dashboard")
    c3, _, b3 = req(op, "/logout", "POST", b"{}", "application/json", tok)
    check("session: 08 login -> dashboard -> logout", c1 == 302 and c2 == 200 and b"hello Alice" in b2 and c3 == 302,
          f"login {c1} {b1[:80]!r} | dashboard {c2} {b2[:60]!r} | logout {c3} {b3[:80]!r}")
    op = opener()
    req(op, "/contact")
    c1, _, b1 = req(op, "/contact", "POST", b"{}", "application/json", tok)
    c2, _, b2 = req(op, "/contact"); c3, _, b3 = req(op, "/contact")
    check("session: 16 contact flash shown once", c1 == 302 and b2.startswith(b"error:Please fill") and b3 == b"|",
          f"post {c1} {b1[:80]!r} | get {c2} {b2[:60]!r} | again {c3} {b3[:40]!r}")
    # --- 3. $response->file() ---
    c, h, b = req(opener(), "/api/reports/q1.pdf")
    check("file: 03 §8 GET /api/reports/q1.pdf", c == 200 and b == PDF, f"{c} {b[:40]!r}")
    for path, what in (("/frag/dl8", "03 §8 'Force a download filename'"), ("/frag/dl3", "03 §3 'download' line")):
        c, h, b = req(opener(), path)
        cd, ct = h.get("Content-Disposition", ""), h.get("Content-Type", "")
        check(f"file: {what}", c == 200 and ct.startswith("application/pdf") and cd.startswith("attachment"), f"{c} Content-Type={ct!r} Content-Disposition={cd!r}")
    bnd = "XbX"; up = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"p.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + b"\x89PNGdata" + f"\r\n--{bnd}--\r\n".encode()
    c1, _, b1 = req(opener(), "/api/images", "POST", up, f"multipart/form-data; boundary={bnd}", tok)
    url = json.loads(b1).get("saved_name", "") if c1 == 201 else ""
    c2, _, b2 = req(opener(), "/api/images/" + url) if url else (0, {}, b"")
    check("file: 03 §12 upload then GET /api/images/<saved>", c1 == 201 and c2 == 200 and b2 == b"\x89PNGdata", f"upload {c1} | get {c2} {b2[:30]!r}")
    # --- 4. WebSocket handler argument order ---
    got = ws_echo("/ws/echo", "hi")
    if srv.errors(): print("  server errors:", srv.errors())
    check("ws: 23 §3 /ws/echo replies 'Echo: hi'", got == "Echo: hi", repr(got))
finally:
    srv.stop()
order = [f"23-websocket.md:{i}" for i, l in enumerate(doc("23-websocket.md").splitlines(), 1) if "function ($connection, $event, $data)" in l]
check("ws: 23 handlers declared ($connection, $event, $data)", not order, f"{len(order)} handlers")

# --- 5. Api result key ---
srv = Server({})
try:
    base = f"http://127.0.0.1:{PORT}"
    rc, out = cli(block("21-api-client.md", "'/posts/1'").replace("https://jsonplaceholder.typicode.com", base), {"TINA4_ALLOW_PRIVATE_REQUESTS": "true"})
    check("api: 21 §3 echo $result[...] prints 200", out.startswith("200"), out[:140].replace("\n", " "))
    rc, out = cli(block("21-api-client.md", "'/users/1'").replace("https://jsonplaceholder.typicode.com", base), {"TINA4_ALLOW_PRIVATE_REQUESTS": "true"})
    check("api: 21 §4 prints Name:", out.startswith("Name: Leanne"), out[:140].replace("\n", " "))
finally:
    srv.stop()
left = [f"21-api-client.md:{i}" for i, l in enumerate(doc("21-api-client.md").splitlines(), 1)
        if re.search(r"\$result\['status'\]|`status`|status ===|\$tokenResult\['status'\]", l)]
check("api: 21 still reading the result's 'status'", not left, f"{len(left)} lines {left[:3]}")

# --- 6. Service subclass $running ---
for n in range(1, 5):
    src = block("27-service-runner.md", "bool $running", n)
    cls = re.search(r"class (\w+)", src).group(1)
    rc, out = cli(src + f"\necho 'declared {cls}';")
    check(f"service: 27 block {n} ({cls}) declares", rc == 0 and out.endswith(f"declared {cls}"), out[-160:].replace("\n", " "))

# --- 7. TINA4_LOG_OUTPUT from the chapter's env block ---
envblk = block("15-logging.md", "TINA4_LOG_OUTPUT=")
srv = Server({}, dotenv=envblk + "\nTINA4_DEBUG=false\n")
try:
    c, h, b = req(opener(), "/ping") if srv.up else (0, {}, srv.tail().encode())
    check("log: 15 §10 env block boots and serves", c == 200, f"{c} {b[:160]!r}")
finally:
    srv.stop()

# --- 8. Container get() on a missing name ---
rc, out = cli(block("26-di-container.md", "$container->get('nonexistent')"), {"TINA4_DATABASE_URL": "sqlite:///data/app.db"})
check("container: 26 §5 catch clause catches", rc == 0 and "nonexistent" in out, out[-200:].replace("\n", " "))

shutil.rmtree(ROUTES, ignore_errors=True); os.makedirs(ROUTES)
for d in ("data", "public", "logs", ".tina4"): shutil.rmtree(os.path.join(APP, d), ignore_errors=True)
for f in (".env.local", "server.log"): os.path.exists(os.path.join(APP if f[0] == "." else HERE, f)) and os.unlink(os.path.join(APP if f[0] == "." else HERE, f))
open(os.path.join(APP, ".env"), "w").write("TINA4_DEBUG=false\n")
print(f"VERDICT ok={results.count(True)} bad={results.count(False)}")
sys.exit(0 if all(results) else 1)
