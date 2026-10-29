# Applies the d-misc-02 doc fix to a tree. usage: fix.py <dir holding the php chapters>
# (tina4-documentation docs/php or tina4-book book-2-php/chapters). Prints replacements per file.
import os, re, sys
D = sys.argv[1]; SKIP = os.environ.get("SKIP", "")  # SKIP=<n>: leave piece n unfixed (gating check)
def edit(name, pairs, regex=False):
    if PIECE == SKIP: return
    p = os.path.join(D, name); s = open(p).read(); n = 0
    for old, new in pairs:
        if regex: s, k = re.subn(old, new, s)
        else: k = s.count(old); s = s.replace(old, new)
        n += k
        if k == 0: print(f"  MISS {name}: {old[:60]!r}")
    open(p, "w").write(s); print(f"{name}: {n}")

PIECE = "1"
# 1. the class is Tina4\Database\Database (release notes left as history)
for n in sorted(os.listdir(D)):
    if n.endswith(".md") and not n.startswith("36-") and re.search(r"Tina4\\Database(?![\\\w])", open(os.path.join(D, n)).read()):
        edit(n, [(r"Tina4\\Database(?![\\\w])", r"Tina4\\Database\\Database")], regex=True)
edit("05-database.md", [("through the global `Tina4\\Database\\Database` class", "through the `Tina4\\Database\\Database` class")])

PIECE = "2"
# 2. $request->session is a Tina4\Session object, not an array
edit("08-authentication.md", [
    ('$request->session["user_id"] = 42;', '$request->session->set("user_id", 42);'),
    ('$request->session["user_name"] = "Alice";', '$request->session->set("user_name", "Alice");'),
    ('$request->session["logged_in"] = true;', '$request->session->set("logged_in", true);'),
    ('empty($request->session["logged_in"])', '!$request->session->get("logged_in")'),
    ('"user_name" => $request->session["user_name"]', '"user_name" => $request->session->get("user_name")'),
    ('$request->session = [];', '$request->session->clear();'),
])
edit("16-email.md", [
    ('$flash = $request->session["_flash"] ?? null;\n    unset($request->session["_flash"]);',
     '$flash = $request->session->get("_flash");\n    $request->session->delete("_flash");'),
])
edit("16-email.md", [(r'(?s)\$request->session\["_flash"\] = \[(.*?)\n(\s*)\];', r'$request->session->set("_flash", [\1\n\2]);')], regex=True)

PIECE = "3"
# 3. file($path, $contentType, $download): no download-name argument, `..` refused
edit("03-request-response.md", [
    ("Tina4 sets the correct `Content-Type` from the file extension and adds `Content-Disposition` so the browser downloads instead of displaying.\n\nCustom filename:\n\n```php\nreturn $response->file(\"/path/to/report.pdf\", \"monthly-report-march-2026.pdf\");",
     "Tina4 sets the correct `Content-Type` from the file extension. The second argument overrides that type (`null` keeps the detected one).\n\nForce a download (`Content-Disposition: attachment`, saved under the file's own name):\n\n```php\nreturn $response->file(\"/path/to/report.pdf\", null, true);"),
    ('$filepath = __DIR__ . "/../../data/reports/" . $filename;', '$filepath = dirname(__DIR__, 2) . "/data/reports/" . $filename;'),
    ("The browser downloads the file. Tina4 detects the MIME type from the extension and sets headers accordingly.\n\nForce a specific download filename:\n\n```php\nreturn $response->file($filepath, \"Q1-2026-Sales-Report.pdf\");",
     "Tina4 detects the MIME type from the extension and sets headers accordingly. A path containing a `..` segment is refused with `403`, so build it with `dirname(__DIR__, 2)` rather than `__DIR__ . \"/../..\"`.\n\nForce a download (the browser saves it under the file's own name):\n\n```php\nreturn $response->file($filepath, null, true);"),
    ('$filepath = __DIR__ . "/../../public/uploads/" . $filename;', '$filepath = dirname(__DIR__, 2) . "/public/uploads/" . $filename;'),
])

PIECE = "4"
# 4. PHP WebSocket handlers receive ($connection, $data, $event)
edit("23-websocket.md", [
    ("function ($connection, $event, $data)", "function ($connection, $data, $event)"),
    ("- **$connection**: The WebSocket connection object. Send messages through it.\n- **$event**: The event type: `\"open\"`, `\"message\"`, or `\"close\"`.\n- **$data**: The message data. Present only for `\"message\"` events.",
     "- **$connection**: The WebSocket connection object. Send messages through it.\n- **$data**: The message data. Present only for `\"message\"` events (`null` for `\"open\"` and `\"close\"`).\n- **$event**: The event type: `\"open\"`, `\"message\"`, or `\"close\"`."),
])

PIECE = "5"
# 5. Api results carry the status code under http_code
edit("21-api-client.md", [
    ("$result['status']", "$result['http_code']"),
    ("- `status` - HTTP status code (integer)", "- `http_code` - HTTP status code (integer; `null` when no response arrived)"),
    ("Always check `status` before accessing `body`.", "Always check `http_code` before accessing `body`."),
    ("Check for `status === 429`", "Check for `http_code === 429`"),
])

PIECE = "6"
# 6. Service declares $running protected; a private redeclaration is a fatal error
edit("27-service-runner.md", [("    private bool $running = true;", "    protected bool $running = true;")])

PIECE = "7"
# 7. TINA4_LOG_OUTPUT accepts stdout, file, both
edit("15-logging.md", [("# Log output destination (stderr | stdout | file)\nTINA4_LOG_OUTPUT=stderr",
                        "# Log output destination (stdout | file | both)\nTINA4_LOG_OUTPUT=stdout")])

PIECE = "8"
# 8. Container::get() throws RuntimeException; there is no ContainerException
edit("26-di-container.md", [
    ("// Throws \\Tina4\\ContainerException if name not registered", "// Throws \\RuntimeException if name not registered"),
    ("} catch (\\Tina4\\ContainerException $e) {", "} catch (\\RuntimeException $e) {"),
    ("echo $e->getMessage();  // \"Service 'nonexistent' is not registered\"", "echo $e->getMessage();  // \"Service not registered: nonexistent\""),
])
