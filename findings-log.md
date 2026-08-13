# Tina4 Evaluation — Findings Log

The mutable record for the Tina4 framework evaluation: chapter coverage, the
the Bug Hunt index, and Suggested Fixes. The Known Issues Log moved to
`known-issues/ledger.md` on 2026-08-13. **Conventions and
protocol live in [`documentation-testing/readme.md`](documentation-testing/readme.md)** — this file is data, not rules.

Known Issues / Bug Hunt table schema (defined in `documentation-testing/readme.md` → Issue Report
Format): `ID | Status | Filed | Found | Suggested fix | Note`. The first four
columns are always populated. **Note** carries as much context as the issue
needs — how it was tested, how certain the cause is, the probe/test filename(s)
if any, or nothing when the row title says enough. **Suggested fix** is a short
inline fix, a `→ FIX-NN` pointer to a long-form write-up below, or `—`.

---

## Evaluation Progress

Refreshed whenever a new test file is added or a finding ID is logged. Status values:
`in-progress` (some sections touched) | `complete` (all sections implemented) | `not-started`.

| Language | Chapter | Sections covered | Status | Findings |
| :--- | :--- | :--- | :--- | :--- |
| Python | 01 — Getting Started | (whole chapter, narrative) | in-progress | PY-01-01, PY-01-03, PY-01-05, PY-01-06, PY-01-07, PY-01-08, PY-01-09, PY-01-10 |
| Python | 10 — Middleware & Security | S3, S4, S9, S10, S12 (source + coworker incident — not yet implemented verbatim) | findings logged, impl pending | ✅ PY-10-01, ✅ PY-10-02, ✅ PY-10-03 (all fixed in 3.13.4) |
| Python | 18 — Testing | S2–S12 of 13 (S13 gotchas = guidance prose) | in-progress | **[Ledger](coverage-ledger/py-ch18-testing.md)** · open: PY-18-01, 02, 03, 07b/c, 11, 12, 13, 14 + **AUD-18-1** (test_auth_flow.py missing, HIGH); fixed 3.13.4: PY-18-04, 08, 10. 11 ch18 test files. Per-section detail + gaps in the ledger. |
| Python | 06 — ORM | glance + S2–S15 + QueryBuilder Integration (all) | complete | **[Ledger](coverage-ledger/py-ch06-orm.md)** · PY-06-01…27 (PY-06-22 fixed 3.13.39). 16 ch06 test files; full suite 208 passed / 2 skipped / 4 xfailed on 3.13.39 · CLI 3.8.51. Open coverage gaps AUD-06-1…6 tracked in the ledger. |
| Python | 12 — Queues | S1–S13 (all) | complete — audit gaps closed | **[Ledger](coverage-ledger/py-ch12-queues.md)** · PY-12-01…11 + BH-50/51/52 — ALL filed on #144 (PY-12-03 last, 2026-07-02). AUD-12-1/2/3/L closed 2026-07-02 · 3.13.48 (all faithful, no new findings). 20 ch12 test files; 86 passed / 26 skipped (broker-gated) on 3.13.48. Backend matrix + per-section detail in the ledger. |
| Python | 07 — QueryBuilder | S1 from_table + S2 select (of 11 + NoSQL/Gotchas/Exercise) | in-progress | **[Ledger](coverage-ledger/py-ch07-querybuilder.md)** · none (S1+S2 fully faithful, 9/9 tests) on 3.13.47 · CLI 3.8.53. S3+ deferred per USER cap. Live mock `GET /chapter/7`. |
| Python | 02–05, 08, 09, 11, 13–17, 19–38 | — | not-started | — |
| PHP | all | — | not-started (workspace not bootstrapped) | — |
| Ruby | all | — | not-started (workspace not bootstrapped) | — |

## Known Issues Log

All confirmed framework bugs and documentation discrepancies are tracked here.
Status values: `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.
Two row kinds share this table: `PY-NN-NN` doc-fidelity findings (from walking chapters) and `BH-<n>` assigned bug-hunt investigations (against upstream `tina4-python` issues; see the *Bug Hunt* note below). Column schema is defined in [`documentation-testing/readme.md`](documentation-testing/readme.md) → *Issue Report Format*.
**Filed** is the upstream GitHub issue/PR link, or `no` if not yet filed. **Found**
is the log date · the framework version it was found on. **Note** carries the detail —
how/whether it was tested, how certain the cause is, and the probe/test filename(s)
if any. **Suggested fix** is a short inline fix, a `→ FIX-NN` pointer, or `—`.

Both tina4-book testing/middleware filings ([#140](https://github.com/tina4stack/tina4-book/issues/140), [#141](https://github.com/tina4stack/tina4-book/issues/141)) landed and the PY-18/PY-10 rows marked `fixed` were resolved in **tina4-python 3.13.4 (2026-06-05)**; their probes flip to bug-absent against ≥3.13.4 (regression sentinels).

**All-out verification pass — 2026-06-22 · 3.13.39 (CLI 3.8.51).** Full implementation-fidelity audit (17 Ch06+Ch18 units: 0 impl-errors after fixing the S14 Author `min_length=2` drop + strengthening weak assertions / closing coverage gaps) plus adversarial verification of all 53 logged findings (7 grouped agents, disprove-by-default). Verdict: **0 refuted** (every finding legitimate), 36 confirmed real, 12 stale-fixed (11 already marked; **BH-49 newly marked fixed** here — all 3 gaps closed, the 5 gap sentinels reframed to assert-absent guards), 5 **unconfirmable by source** — CLI/website runtime claims that MUST be re-checked live before EOD filing: **PY-06-16** (`tina4 shell` absent), **PY-06-17** (`tina4 console` `src.*` import), **PY-01-07** (`tina4 install` naming), **PY-01-08** (`tina4 doctor` output), **PY-01-10** (tina4.com `/python` landing-page install — filed #143). Suite at pass end: 213 passed / 2 skipped / 4 xfailed / 0 failed.

> **MOVED 2026-08-13 — the 67 rows are now in [`known-issues/ledger.md`](known-issues/ledger.md).**
>
> That ledger is the single home for issues in this repo: it spans every language and covers both
> documentation and framework code, and it adds the two columns this table never had — the version
> each issue was **last reproduced on**, and **how to reproduce it**. Codes are unchanged, so a
> `PY-NN-NN` or `BH-<n>` quoted in an upstream issue still resolves.
>
> The narrative above and below stays here, and so does *Suggested Fixes* — the `FIX-NN` long-form
> proposals that the ledger's Suggested-fix column points at.

### Observed terminal output

Snippets attached to the findings above, where the issue is about code that doesn't run.

#### PY-01-06 — `pip install tina4` fails (wrong package name)

```
PS C:\Users\work\Documents\projects\testing-tina4\pypy> pip install tina4
ERROR: Could not find a version that satisfies the requirement tina4 (from versions: none)
ERROR: No matching distribution found for tina4
```

#### PY-01-07 — `tina4 install --help` shows it installs runtimes, not framework

```
$ tina4 install --help
Install a language runtime (python, php, ruby, nodejs)

Usage: tina4.exe install <LANG>

Arguments:
  <LANG>  Language to install: python, php, ruby, nodejs
```

#### PY-01-08 — `tina4 doctor` exposes the mis-labelled "Tina4 CLIs" section

```
  Tina4 CLIs
  ──────────────────────────────────────────────────────────────────────
  ✗ tina4python      Python       not found  →  run: pip install tina4-python
  ✗ tina4php         PHP          not found  →  run: composer global require tina4/tina4php
  ✗ tina4ruby        Ruby         not found  →  run: gem install tina4ruby
  ✗ tina4nodejs      Node.js      not found  →  run: npm install -g tina4nodejs
  ✗ vite             tina4js      not found  →  run: npm install vite
```

#### PY-01-10 — Python landing-page quickstart fails verbatim (no `tina4` CLI install step)

Documentation shows (Python landing page, Installation section):

```
pip install tina4-python
tina4 init my-project
cd my-project
tina4 serve
```

Actual (followed verbatim, Windows):

```
PS C:\Users\work> pip install tina4-python
Successfully installed tina4-python-3.13.38

PS C:\Users\work\Documents> tina4 init my-first-tina
tina4 : The term 'tina4' is not recognized as the name of a cmdlet, function,
script file, or operable program. ...
    + FullyQualifiedErrorId : CommandNotFoundException
```

#### PY-01-09 — `tina4python` CLI crashes on Windows (cp1252) printing help

```
PS C:\Users\work> tina4python
Traceback (most recent call last):
  File "...\Python313\Scripts\tina4python.exe\__main__.py", line 5, in <module>
    sys.exit(main())
  File "...\site-packages\tina4_python\cli\__init__.py", line 126, in main
    _help()
  File "...\site-packages\tina4_python\cli\__init__.py", line 207, in _help
    print(""" Tina4 Python — CLI ... """)
  File "...\Python313\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 1703: character maps to <undefined>

PS C:\Users\work> tina4python --version
Traceback (most recent call last):
  ...
  File "...\site-packages\tina4_python\cli\__init__.py", line 157, in main
    _help([])
  ...
UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 1703: character maps to <undefined>
Unknown command: --version
```

#### PY-06-23 — S11 `recent()` scope uses SQLite `datetime('now', ?)`, fails on PostgreSQL

```
>       posts = BlogPost.recent()        # @classmethod -> cls.where("created_at > datetime('now', ?)", [f"-{days} days"])

E       psycopg2.errors.UndefinedFunction: function datetime(unknown, unknown) does not exist
E       LINE 1: SELECT * FROM posts WHERE created_at > datetime('now', '-7 d...
E                                                      ^
E       HINT:  No function matches the given name and argument types. You might need to add explicit type casts.

  query = "SELECT * FROM posts WHERE created_at > datetime('now', %s) LIMIT %s OFFSET %s"
  vars  = ['-7 days', 20, 0]
```

#### PY-06-04 — S4 `select_one`/`load` examples query a `slug` column the Note model lacks

Documentation shows (`06-orm.md:412`, `:428`):

```python
note = Note.select_one("SELECT * FROM notes WHERE slug = ?", ["my-note"])
note.load("slug = ?", ["my-note"])
```

Note model fields (S2, `06-orm.md:108-121`): `id, title, content, category, pinned, created_at, updated_at` — no `slug`.

Actual output:

```
select_one slug RAISED: UndefinedColumn | column "slug" does not exist
load slug RAISED:       UndefinedColumn | column "slug" does not exist
```

Issues:
- `slug` is referenced in two S4 query examples but is not a field on the documented Note model.
- Verbatim copy raises `UndefinedColumn` (PG) / `no such column: slug` (SQLite).
- Framework behaves correctly — the column genuinely does not exist; the gap is in the chapter.

#### PY-06-06 — S4/S6 positional path-param handlers can't be driven by the documented Test client

Documentation shows (`06-orm.md:314`, S4 `find_by_id` handler; same shape at `:361`, `:570`, `:613`):

```python
@get("/api/notes/{id:int}")
async def get_note(id, request, response):
    note = Note.find_by_id(id)
    ...
```

Actual output (driving the verbatim handler through `tina4_python.test`'s client):

```
E       TypeError: get_note() missing 1 required positional argument: 'response'
.venv\Lib\site-packages\tina4_python\test_client\__init__.py:155: TypeError
```

Issues:
- The server dispatch (`core/server.py:1272` `_invoke_handler`) injects `{id:int}` by parameter name, so the handler works under `tina4 serve`.
- The Test client (`test_client/__init__.py:155`) calls `handler(request, response)` flatly — a handler whose first positional param is the path arg raises `TypeError`.
- Handlers with no path param (`create_note`, `list_notes`) run fine via the Test client → the gap is path-param injection, not the `response(...)` call form.
- The positional signature matches the framework's own routing docs (`tina4_python/CLAUDE.md`), so testing documented handlers with the documented Test client fails on dispatch parity, not on user error.

#### PY-06-05 — glance `Post` and S6 `BlogPost` share `table_name="posts"` with incompatible schemas

Documentation shows two models on the same table — `06-orm.md:23-33` (glance) and `06-orm.md:551-565` (S6):

```python
class Post(ORM):       # ORM at a Glance
    table_name = "posts"
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True, max_length=200)
    body = StringField(default="")
    created_at = DateTimeField()

class BlogPost(ORM):   # S6 has_many
    table_name = "posts"
    id = IntegerField(primary_key=True, auto_increment=True)
    author_id = IntegerField(required=True)
    title = StringField(required=True, max_length=300)
    slug = StringField(required=True)
    # ...content, status, created_at, updated_at
```

Actual output — verbatim `Post.create(title="x")` against the S6 `BlogPost` table:

```
PostgreSQL query failed: UndefinedColumn: column "body" of relation "posts" does not exist
Post.create(title='x') -> <Post id=None>
```

Against `Post`'s own clean schema, all 8 Common Query Operations work:

```
create(title='x')        -> id=1
post.save()              -> id=2
find_by_id(p.id)         -> <Post id=1>
find({'title':'x'})      -> 1 rows
where('title = ?',['x']) -> 1 rows
all()                    -> 2 rows
count()                  -> 2
post.delete()            -> True
```

Issues:
- Two documented models declare `table_name = "posts"` with incompatible columns — copy-paste collision.
- Verbatim `Post.create(title="x")` hits `UndefinedColumn: column "body"` when the S6 table exists first.
- `create()` swallows the error and returns an unsaved `<Post id=None>` (no exception, no `False`) — same swallow class as PY-18-13e.

#### PY-06-07 — documented write routes return 401 (undocumented Bearer gate)

Documentation shows (`06-orm.md:276-285`):

```python
@post("/api/notes")
async def create_note(request, response):
    note = Note()
    note.title = request.body["title"]
    # ...
    note.save()
    return response({"message": "Note created", "note": note.to_dict()}, 201)
```

Actual output (verbatim `POST /api/notes` under `tina4 serve`, no token):

```
{"error":"Unauthorized","message":"Valid authorization token required","status":401}
```

Issues:
- Tina4 gates POST/PUT/PATCH/DELETE behind a Bearer token by default; the chapter shows the write route as a plain `@post` with no auth note.
- Read routes (`GET /api/notes`, `/api/notes/{id}`, `/api/authors/{id}`, `/api/posts/{id}`) serve 200 over HTTP — only writes 401.
- Chapter 6 never mentions `auth`, `token`, `@noauth()`, or a Bearer header (grep: zero matches outside the word "author").
- Not a framework bug — the gate is the intended default (PY-10-02); the gap is documentation. Same shape in the S9 Auto-CRUD `curl -X POST` example and the S14 solution.

#### PY-06-08 — `BooleanField` is native BOOLEAN on PG; S4 `select([1])` fails

Documentation shows — S2 field-types table (`06-orm.md:136`) and the S4 SQL-first example (`06-orm.md:401-404`):

```
| BooleanField | bool | INTEGER (0/1) | True/False |
```

```python
notes = Note.select(
    "SELECT * FROM notes WHERE pinned = ? ORDER BY created_at DESC",
    [1], limit=20, offset=0
)
```

Actual output (verbatim, PostgreSQL):

```
psycopg2.errors.UndefinedFunction: operator does not exist: boolean = integer
LINE 1: SELECT * FROM notes WHERE pinned = 1 ORDER BY created_at DES...
information_schema.columns: notes.pinned data_type = boolean
```

Issues:
- On PG the `pinned` column is native `BOOLEAN`, not `INTEGER (0/1)` as the field-types table states.
- The raw-SQL `select(..., [1], ...)` example passes integer `1`; PG rejects `boolean = integer`.
- `[True]` works, and `find({"pinned": True})` works (the ORM translates) — only the documented raw `[1]` form breaks.
- Cross-ref BH-46 (`SQLTranslator.boolean_to_int`).

#### PY-06-13 — Test client skips the write-route auth gate (serve 401 vs client 201)

`POST /api/notes` — verbatim S4 `create_note` (`06-orm.md:276-285`):

Over `tina4 serve` (real HTTP):

```
{"error":"Unauthorized","message":"Valid authorization token required","status":401}
```

Through the `tina4_python.test` client (`self.post("/api/notes", json={...})`):

```
STATUS 201
{"message":"Note created","note":{"id":1,"title":"X",...}}
```

Issues:
- Same handler, two dispatchers, two outcomes — `tina4 serve` enforces the Bearer gate, the Test client does not.
- A write-route test via the documented Test client passes (201) while the route 401s in production.
- Dispatch-parity family with PY-06-06 (path params); here the divergence is auth.

#### PY-06-16 / PY-06-17 — S3 interactive `create_table()` flow broken in the program

Documentation shows (`06-orm.md:260-264`):

```bash
tina4 shell
>>> from src.orm.note import Note
>>> Note.create_table()
```

Actual output:

```
$ tina4 shell
error: unrecognized subcommand 'shell'        # PY-06-16 — REPL is `tina4 console`

$ tina4 console
[ERROR] Failed to load .../src/orm/note.py: No module named 'src'   # PY-06-17 (startup auto-load)
>>> from src.orm.note import Note
ModuleNotFoundError: No module named 'src'      # PY-06-17 — manual import fails too
```

Issues:
- `tina4 shell` is not a CLI subcommand (real REPL: `tina4 console`).
- `tina4 console` does not put the project root on `sys.path`, so `from src.orm.X import Y` fails — the same modules load fine under `tina4 serve`.
- Together: the documented S3 interactive `create_table()` flow cannot be run in the program. The ORM/soft-delete behaviour itself works (pytest vs live PG).

#### PY-06-18 — auto-CRUD shadows custom routes (doc says custom wins)

Documentation shows (`06-orm.md:941-943`): *"Custom routes defined in `src/routes/` load before auto-CRUD routes. They take precedence."*

Actual — `Note` with `auto_crud = True` + custom `/api/notes` routes, under `tina4 serve`:

```
[INFO] AutoCrud: registered 5 routes for Note (/api/notes)   # auto-CRUD registers FIRST
...
[DEBUG] Route registered: POST /api/notes (auth=required)    # custom registers AFTER

$ curl http://localhost:7146/api/notes
{"records":[],"data":[],"count":0,"total":0,"limit":10,"offset":0,"page":1,...}   # auto-CRUD payload, not custom {notes,count}
```

Issues:
- Auto-CRUD routes register before custom same-path routes and serve the request — custom routes are shadowed.
- Directly contradicts the documented precedence ("custom routes take precedence").

#### PY-18-02 — `tina4 test` fails because pytest isn't installed

```
$ tina4 test
C:\Users\work\Documents\projects\testing-tina4\pypy\.venv\Scripts\python.exe: No module named pytest
```

#### PY-18-03 — `tina4 test --help` has no options

```
$ tina4 test --help
Run tests (delegates to language CLI)

Usage: tina4.exe test

Options:
  -h, --help  Print help
```

Re-verified 2026-06-05 on CLI 3.8.28 + tina4-python 3.13.4:

```
$ tina4 test --verbose
error: unexpected argument '--verbose' found

$ tina4 test --file tests/test_ch18_basic.py
error: unexpected argument '--file' found
```

S9 re-verification (2026-06-05, CLI 3.8.28 + tina4-python 3.13.4) — the
chapter's two Code Coverage examples both reject at the CLI before pytest is
reached:

```
$ tina4 test --cov=src --cov-report=term
error: unexpected argument '--cov' found

$ tina4 test --cov=src --cov-report=html
error: unexpected argument '--cov' found
```

The underlying tooling works — `uv run python -m pytest --cov=src
--cov-report=term` produces the expected report against the same suite
(73 statements, 97% covered) — but the chapter's documented invocation path
through `tina4 test` does not.

#### PY-18-04 — Discovery silently skips non-`test_*.py` files; actual output is raw pytest

A file named `ch18_basic.py` (without the `test_` prefix) is not discovered:

```
$ tina4 test
collected 0 items
no tests ran in 0.01s
```

Docs claim this output format:

```
Running tests...

  BasicTest
    [PASS] test_addition
    [PASS] test_string_contains
    [PASS] test_array_length

  3 tests, 3 passed, 0 failed (0.02s)
```

Actual output is raw pytest:

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\work\Documents\projects\testing-tina4\pypy
configfile: pyproject.toml
collected 3 items

tests\test_ch18_basic.py ...                                             [100%]

============================== 3 passed in 0.22s ==============================
```

#### PY-18-07 — Section 4 snippet fails twice in a row

Before adding the `Product` import:

```
tests\test_ch18_product.py FFFFF                                         [100%]
================================== FAILURES ===================================
_______________________ ProductTest.test_create_product _______________________

    def test_create_product(self):
>       product = Product()
E       NameError: name 'Product' is not defined

tests\test_ch18_product.py:7: NameError
```

After adding `from src.orm.product import Product`, every `product.save()` hits:

```
_______________________ ProductTest.test_create_product _______________________

    def test_create_product(self):
        product = Product()
        product.name = "Test Widget"
        ...
>       product.save()

.venv\Lib\site-packages\tina4_python\orm\model.py:308: in save
    db = self._get_db()
...
E       RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env
```

#### PY-18-08 — Section 5 route-test signatures don't match reality

We used this from the docs:

```python
resp = self.get("/health")
assert_equal(resp.status_code, 200, "Health check should return 200")
```

It didn't work and said:

```
E       AttributeError: 'TestResponse' object has no attribute 'status_code'
```

We used this from the docs:

```python
resp = self.post("/api/products", {
    "name": "Route Test Product",
    "category": "Testing",
    "price": 42.00
})
```

It didn't work and said:

```
E       TypeError: Test.post() takes 2 positional arguments but 3 were given
```

#### PY-18-12 — S7 `User` referenced with no import

Documentation shows (`18-testing.md:466-501`, refreshed 2026-06-05):

```python
from tina4_python.test import Test, assert_equal, assert_not_none
import time

class UserTest(Test):

    def set_up(self):
        user = User()
        user.name = "Test User"
        user.email = f"test-{int(time.time())}@example.com"
        user.save()
        self.user_id = user.id
    ...
```

Actual output:

```
    def set_up(self):
        # Runs before each test
>       user = User()
E       NameError: name 'User' is not defined

tests\test_ch18_setup_teardown.py:12: NameError
```

Issues:
- `User` referenced in `set_up`, `tear_down`, and both test methods. Not imported anywhere in the chapter.
- No `User` ORM model defined or shown in Ch18.
- Same defect class as PY-18-07a (S4 Product) before the 3.13.4 fix; the parallel fix was not applied to S7.

#### PY-18-13 — S12 `test_user_model.py` broken in 5 independent ways

Documentation shows (`18-testing.md:744-811`):

```python
import uuid
from tina4_python.test import Test, assert_equal, assert_true, assert_not_none, assert_raises

class UserModelTest(Test):

    def test_duplicate_email(self):
        ...
        assert_raises(create_duplicate, Exception, "Should reject duplicate email")

    def test_select_users(self):
        ...
        users, count = User.where("1=1")
        assert_true(len(users) >= 3, "Should have at least 3 users")
```

Actual output (verbatim, sequential — each error reached after patching the previous):

```
# PY-18-13a — on collection before any test runs:
NameError: name 'User' is not defined

# PY-18-13b — after adding import, on first test:
RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env

# PY-18-13d — test_select_users (reaches this after a/b patched):
ValueError: too many values to unpack (expected 2)
tests\test_user_model.py:82: ValueError

# PY-18-13e — test_duplicate_email (with UNIQUE index manually applied):
AssertionError: Should reject duplicate email
.venv\Lib\site-packages\tina4_python\test\__init__.py:387: AssertionError
```

Issues:
- `User` never imported — `NameError` before any test runs (PY-18-13a).
- No `TINA4_DATABASE_URL`, no `create_table()` — `RuntimeError` on first `user.save()` (PY-18-13b).
- No `unique` kwarg on `StringField`, no migration/index shown — chapter mandates duplicate rejection with no mechanism (PY-18-13c).
- `User.where("1=1")` returns `list`, not `(list, int)` — needs `with_count=True` (PY-18-13d).
- `ORM.save()` swallows all exceptions (model.py:336-338) — `assert_raises` can never fire; real contract is `save()` returns `False` (PY-18-13e).

#### PY-18-10 — Response Object reference doesn't match `TestResponse`

Documentation shows (`18-testing.md:384-393`):

```python
resp.status_code   # HTTP status code (200, 201, 404, etc.)
resp.body          # Response body as a string
resp.headers       # Response headers as a dict
resp.content_type  # Content-Type header value
```

Framework reality (`tina4_python/test_client/__init__.py:28-52`):

```python
class TestResponse:
    __slots__ = ("status", "body", "headers", "content_type")
    self.status: int = response.status_code
    self.body: bytes = response.content
    self.content_type: str = response.content_type
    self.headers: dict = {...}
    def json(self): ...
    def text(self): ...
```

Probe (`documentation-testing/pypy/tests/test_ch18_response_object_probe.py`):

```
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_doc_resp_status_code_attribute_exists FAILED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_real_resp_status_attribute_works     PASSED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_doc_resp_body_is_a_string            FAILED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_real_resp_body_is_bytes              PASSED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_undocumented_text_helper_exists      PASSED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_undocumented_json_helper_exists      PASSED
```

Failure details:

```
E       AttributeError: 'TestResponse' object has no attribute 'status_code'
E       AssertionError: docs claim resp.body is a string
```

Issues:
- `resp.status_code` documented; real attribute is `resp.status`.
- `resp.body` documented as string; real type is `bytes`.
- `resp.json()` and `resp.text()` methods exist on the class; not listed in the reference.

## Bug Hunt — `BH-<n>` rows

Bug-hunt findings live in [`known-issues/ledger.md`](known-issues/ledger.md), labelled `BH-<n>` where `<n>` is
the upstream `tina4-python` issue number (e.g. `BH-46` ↔ [`#46`](https://github.com/tina4stack/tina4-python/issues/46)).
They share the KI Log's format and differ only in origin:

- **`PY-NN-NN`** — surfaced by the documentation-fidelity protocol while walking chapters.
- **`BH-<n>`** — a bug the user *assigned*: a reproduction / root-cause request against an
  existing GitHub issue ("go investigate this, dig with tests and theories until the root
  cause is nailed down"). Each `BH-<n>` row's **Note** opens with what's being investigated.

Per-finding evidence is kept on the `bug-hunting` branch (never `main`):
- `bug-hunting/issue-<n>-<slug>.md` — root cause, source-line evidence, adversarial
  verification, recommended fix, draft upstream comment.
- `documentation-testing/pypy/tests/test_issue_<n>_*.py` — probes that *try to trigger the bug*: the assertion
  reads as FAIL while the bug is present (functionality goal unmet) and PASSES once the
  upstream fix lands — the same correct-state sentinel direction as the `PY-NN-NN` probes
  (documentation-testing/readme.md → Convention Recap → *Probe pattern*). Legacy exception: some BH-46/49
  gap-assertions were authored inverted (pass-while-buggy, "flip to fail when fixed") — their
  row Notes describe them as-built; new probes follow the canonical direction above.

The GitHub issue thread is the "official log"; the **Filed** column links it.

## Suggested Fixes

Proposed remedies for entries in [`known-issues/ledger.md`](known-issues/ledger.md). Each fix tags one or more issue IDs
and includes rationale, concrete edits, and acceptance criteria.

Status values: `proposed` | `accepted` | `applied` | `rejected`.

### Editorial principles

These guidelines apply to every fix proposed in this section. Future fixes should default
to them unless there's a specific reason not to:

1. **Tina4 docs are not install guides for other people's tools.** Prerequisites
   (Python, uv, Rust/Cargo, Ruby, PHP, Composer, Node, etc.) get listed and linked
   out — never embedded as platform-specific install snippets. The owners of those
   tools maintain better install docs than the Tina4 docs ever can, and trying to mirror them
   creates drift and bloats every page.
2. **Required vs. optional prereqs are marked as such.** If a tool is needed only
   for one specific path (e.g. Cargo for `cargo install tina4`), label it optional
   and tie it to the path that needs it.
3. **One concept per heading.** External prereqs, the CLI, and the framework package
   are three different things and live in three different sections. Don't mix them.
4. **Show the dependency chain, in order.** Language runtime → tool → project. Pages
   should follow that flow so a reader following them top-down never has to scroll
   back.
5. **Annotate every prerequisite with what it's for.** Each entry in a prereqs list
   carries a one-line note explaining its role — not "install Python," but "Python
   3.12+ — the runtime that executes your app." A reader scanning the list should
   know *why* each item is required, not just that it is.

### FIX-01 — Restructure the Python Getting Started page

**Tags:** PY-01-01
**Page:** `https://tina4.com/python/01-getting-started.html`
**Status:** proposed

**The problem in one sentence.** The current page collapses three distinct concepts —
external prerequisites, the Tina4 CLI (a Rust tool), and the `tina4-python` framework
package — into a single "What You Need / Install" mash-up. A first-time reader can't tell
where the boundary is between "things outside Tina4," "the tool," and "the framework."

**Proposed structure.** Replace the current "What You Need" + "Installing the Tina4 CLI"
sections with three top-level headings that follow the actual dependency chain:

```
## 1. Prerequisites
   Python 3.12+    — the language runtime that executes your app.
                     Install from python.org/downloads.
   uv              — manages your project's Python dependencies; `tina4 init`
                     uses it to add the framework package to your project.
                     Install from docs.astral.sh/uv/getting-started/installation.

## 2. Install the Tina4 CLI
   What it is:     a Rust binary that scaffolds and runs Tina4 projects.
                   It is NOT the Python framework — that lives inside your project
                   and is pulled in by `tina4 init` (see step 3).
   macOS:          brew install tina4stack/tap/tina4
   Linux/macOS:    curl -fsSL https://.../install.sh | bash
   Windows:        irm https://.../install.ps1 | iex
   Verify:         tina4 --version

## 3. Create your first project
   tina4 init python my-app
   cd my-app
   tina4 serve
   What just happened: `tina4 init` scaffolded the project structure and
   added `tina4-python` to your dependencies via uv.
```

**What to delete from the current page.**

- The "What You Need" list item #3 ("The Tina4 CLI — a Rust-based binary...") — the CLI
  is the subject of the next heading, not a prerequisite to itself.
- The `python3 --version` verification command in prereqs (or move it inline with the
  Python link). It currently implies Python is installable but no instructions are given —
  worse than just linking out.
- Any platform-specific `uv` install snippets in prereqs. Replace with a single line:
  *"uv — install from [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)."*

**Rationale.**

- Mirrors the actual dependency chain: language → tool → project.
- Equalizes Python and uv (PY-01-01 symptom a): both link out, neither gets snippets.
- Distinguishes the CLI from the framework (PY-01-01 symptom b): they live in different
  headings, with an explicit "this is NOT the Python framework" call-out.
- Eliminates the contradiction of listing the CLI as a prerequisite while also installing
  it on the same page (PY-01-01 symptom c).

**Acceptance criteria.**

- A reader who has only Python + uv installed can follow steps 2→3 and reach a running
  server without needing to scroll back to re-read prereqs.
- The words "Tina4 CLI" and "tina4-python" each appear in exactly one heading scope, and
  the page text explicitly states that they are different things.
- The prereqs section contains zero install commands — only link-outs.

---

### FIX-02 — Cargo install option

**Tags:** PY-01-03
**Page:** `https://tina4.com/python/01-getting-started.html` (and any sibling
language pages that show the same option).
**Status:** proposed

**The problem in one sentence.** The page offers `cargo install tina4` as an install
path without ever listing Cargo (the Rust toolchain) as a prerequisite or linking to
how to get it.

**Three acceptable resolutions** — pick one:

**Option A: remove the cargo option from this page.**
The Homebrew, curl, and PowerShell paths already cover every supported platform.
Removing cargo shortens the page and eliminates the unannounced-prereq trap.
Mention cargo only in the project's GitHub README for contributors building from source.

**Option B: keep cargo, but quarantine it.**
Move the `cargo install tina4` snippet under a clearly labelled subsection — e.g.
*"Install from source (advanced)"* — that opens with a one-line prereq note:

> *Requires the Rust toolchain. If you don't already have it, install via
> [rustup.rs](https://rustup.rs) first.*

**Option C (recommended): list Cargo as an *optional* prerequisite, with the note inline at the cargo command.**
Keeps the cargo install path visible alongside the other platforms (no new subsection),
but makes its dependency explicit so the reader can't be ambushed. Two parts:

1. In the Prerequisites section, after the required items, add a third entry:

   > *Cargo / Rust toolchain (optional) — only needed if you plan to install the
   > Tina4 CLI via `cargo install`. See [rustup.rs](https://rustup.rs).*

2. In the install snippets, label the cargo line clearly so the conditional nature
   is obvious at the point of use:

   ```
   macOS:        brew install tina4stack/tap/tina4
   Linux/macOS:  curl -fsSL .../install.sh | bash
   Windows:      irm .../install.ps1 | iex
   From source:  cargo install tina4   (requires Rust — see Prerequisites)
   ```

This is the recommended option because it preserves user choice, sets expectations
up-front *and* at the point of use, and avoids creating a new "advanced" subsection
for what is really just one extra line.

**What NOT to do.**

- Do not leave the cargo command alongside the brew/curl/PowerShell options as a
  same-level "alternative" with no prereq note. That's the current state and the
  source of the issue.
- Do not silently assume readers who reach for cargo "obviously" have Rust — many will
  recognize the syntax from copy-paste habits without having the toolchain.

**Acceptance criteria.**

- Either no `cargo install tina4` appears on the Getting Started page (Option A), OR
  every occurrence of it is accompanied — either inline or via a clearly named parent
  subsection — by a note that names Rust/Cargo as a requirement and links to
  [rustup.rs](https://rustup.rs) (Options B or C).
- A reader with no Rust toolchain who follows the recommended install path on any
  platform succeeds without a missing-tool error.
- The global Prerequisites section, if it mentions Cargo at all, marks it as
  *optional* and ties it to a specific install path (Option C).

---

### FIX-03 — `tina4 test --file` should auto-resolve in `tests/`

**Tags:** PY-18-03
**Page:** `https://tina4.com/python/18-testing.html` S8 (Running Tests), plus
the CLI implementation in the Rust binary.
**Status:** proposed

**The problem in one sentence.** When `--file` is eventually implemented for
`tina4 test`, the documented call form `tina4 test --file tests/test_product.py`
forces the reader to type the `tests/` prefix even though the framework
already knows tests live in `tests/`. Discovery is convention-based; the flag
shouldn't undo that convention.

**Recommendation.** The CLI should accept a bare filename and resolve it
against `tests/` automatically. Full paths still work for explicit cases.

```
tina4 test --file test_ch18_basic.py            # auto-resolves tests/test_ch18_basic.py
tina4 test --file tests/test_ch18_basic.py      # explicit path also accepted
tina4 test --file src/probes/check_x.py         # absolute-from-project path: used as-is
```

Resolution order (first match wins):
1. Path exists relative to cwd (current behaviour shown in docs).
2. Path exists relative to `tests/`.
3. Glob match within `tests/` for `**/{name}` (e.g. `--file test_ch18_basic.py`
   resolves even if it sits in `tests/ch18/test_ch18_basic.py`).

**Doc update once implemented.** S8 examples should drop the `tests/` prefix to
demonstrate the convention:

```
tina4 test --file test_product.py                              # specific file
tina4 test --file test_product.py --method test_create_product # specific method
```

With a one-line callout: *"Bare filenames resolve in `tests/` automatically.
Pass an explicit path (`tests/sub/test_x.py`) when needed."*

**Why.** Tina4's design philosophy is convention over configuration (per the
framework's own `CLAUDE.md`). The current docs contradict that by making the
reader spell out the location of a dir the framework already owns. Pytest
itself supports this via test IDs (`pytest test_x.py::Class::method`) but
only when invoked from project root with `tests/` on the discovery path —
`tina4 test --file` is positioned as the user-friendly wrapper, so the
ergonomics should be at least as good.

**Acceptance criteria.**

- `tina4 test --file test_product.py` succeeds without `tests/` prefix when
  the file lives at `tests/test_product.py`.
- `tina4 test --file tests/test_product.py` continues to work (no breaking
  change).
- S8 doc examples updated to use the bare-filename form, with a one-line
  callout naming the resolution rule.

---

### FIX-04 — `tina4 test` output formatter (relocated)

Speculative UI spec for a `tina4 test` output formatter (per-file bar, right-anchored status, bottom printer line). **PY-18-04 is CLOSED (fixed 3.13.4 — `tina4 test` cleanly wraps pytest);** the maintainer never requested this formatter. Full spec relocated to [`notes/FIX-04-test-output-formatter.md`](notes/FIX-04-test-output-formatter.md).

### FIX-05 — Chapter 6 (ORM) should set up its own database

**Tags:** PY-06-01, PY-06-02
**Type:** Documentation
**Page:** `https://tina4.com/python/06-orm.html`
**Status:** proposed

**The problem in one sentence.** Chapter 6 teaches the ORM but never shows the
two things every example silently depends on — a connected database (PY-06-01)
and an existing table per model (PY-06-02) — so a reader who lands on this
chapter, or copies any section past S3, hits `No database bound` then
`relation "<table>" does not exist`.

**Proposed structure.** Add a short setup block at the very top of the chapter
(before S2 "Defining a Model"), then a one-line per-section reminder where new
models appear.

1. **Top-of-chapter setup section** — demonstrate the connection the chapter
   assumes, pointing back to Chapter 5:

   > **Before you start.** The ORM needs a database connection. Set
   > `TINA4_DATABASE_URL` in your `.env` (see Chapter 5) — the ORM auto-binds to
   > it. Each model maps to a table; create it with `Model.create_table()` (shown
   > below) or a migration before you query or save.

2. **Per-section table reminder** — every section that introduces a model
   (S6 Author/BlogPost, S8 Task, S12 Product, S13/14 blog) opens with a single
   line, e.g.:

   > *Assuming a database is connected and the `authors` and `posts` tables exist
   > (`Author.create_table()`, `BlogPost.create_table()`).*

3. **Self-contained exercise/solution.** The S14 solution (`src/routes/blog.py`)
   should either include the `create_table()` calls (app startup) or ship a
   migration for `authors`, `posts`, `comments` — as written it saves to three
   tables that no chapter step creates.

**Rationale.**

- Mirrors the actual dependency chain: connect DB → create table → query.
- Fixes both PY-06-01 (binding) and PY-06-02 (tables) at their root — the chapter
  omitting its own setup — rather than patching each example.
- A reader can follow Chapter 6 top-down, or jump to any section, and reach a
  working result without inferring the missing setup.

**Acceptance criteria.**

- A reader who has only completed Chapter 5 can run any Chapter 6 section's code
  and have it succeed (no `No database bound`, no `relation does not exist`).
- Every section that defines a model names the table it needs and how to create it.
- The S14 solution is runnable as shipped — the three tables it writes to are
  created by the chapter (startup `create_table()` or migration).

---

### FIX-06 — Strip Chapter 6 (ORM) to Python only

**Tags:** PY-06-03
**Type:** Documentation
**Page:** `https://tina4.com/python/06-orm.html`
**Status:** proposed

**The problem in one sentence.** The Python ORM chapter carries ~85 lines of
non-Python content — PHP/Ruby/Node.js model definitions and a four-language
comparison table (`06-orm.md:13-98`) — before the Python material proper begins.

**Proposed change.**

- Remove the PHP, Ruby, and Node.js code blocks from the "ORM at a Glance"
  section (`06-orm.md:37-78`).
- Drop the four-language "Common Query Operations" table (`06-orm.md:85-94`), or
  reduce it to the Python column only.
- Remove cross-language caveats in the surrounding prose (e.g. *"PHP needs
  `(new Post())`…"*, *"Ruby methods drop the parentheses"*).
- If the cross-language parity story is worth telling, move it to a shared
  overview page that sits above the per-language books — not inside the Python
  chapter.

**Rationale.**

- A reader in the Python book wants Python. Other-language code is noise that
  pushes the actual Python material down the page.
- The same applies to every Python chapter — check for and strip the same
  multi-language interludes elsewhere (this fix is scoped to Ch06; others get
  their own findings as they're walked).

**Acceptance criteria.**

- Chapter 6 contains only Python code and Python-relevant prose.
- No PHP/Ruby/Node.js code blocks or N-language comparison tables remain in the
  chapter body.

---

### FIX-07 — Lead the Quick Reference with an Installation / Update section; rename it "Getting Started / Quick Reference"

**Tags:** PY-01-10 (primary); relates to PY-01-09, PY-01-01
**Page:** the existing **Quick Reference** page — to be renamed **"Getting Started / Quick Reference"**. The broken landing quickstart (`/python/#installation`, PY-01-10) links here instead of carrying its own commands. Pattern repeats per language.
**Thread:** [#143](https://github.com/tina4stack/tina4-book/issues/143) — Tina4 Chapter Quick Reference (PY-01-10 report filed here 2026-06-19).
**Status:** proposed

**The problem in one sentence.** Install commands are scattered (a four-line quickstart on the landing page, a fuller flow in the Getting Started chapter) and no single place lists *every* command a from-zero reader runs, in order — and the landing quickstart is the broken one (PY-01-10): it shows `pip install tina4-python → tina4 init → cd → tina4 serve`, never installs the `tina4` CLI, so a brand-new reader dies at step 2 with `'tina4' is not recognized`.

**Proposed structure.** Don't add a new page. Make the existing **Quick Reference** the canonical home: add an **Installation / Update** block as its **first section**, and rename the page **"Getting Started / Quick Reference"** so a newcomer recognizes it as the entry point. A reader who has *only their OS* — no project, no CLI, no framework — follows that first section top-down and reaches a running server. Headings follow the dependency chain (Editorial principle 4); the CLI and the framework package stay in separate sub-sections (principle 3); other tools link out, never embedded (principle 1).

```
## Prerequisites   (Tina4 links out — it does not bundle these)
   Python 3.12+  — the runtime that executes your app.   → python.org/downloads
   uv            — manages your project's dependencies.   → docs.astral.sh/uv

## Install the Tina4 CLI   (one Rust binary; serves all four languages)
   What it is:   the tool that scaffolds and runs projects. NOT the Python
                 framework — that lives inside your project (next section).
   macOS:        brew install tina4stack/tap/tina4
   Linux/macOS:  curl -fsSL https://raw.githubusercontent.com/tina4stack/tina4/main/install.sh | bash
   Windows:      irm https://raw.githubusercontent.com/tina4stack/tina4/main/install.ps1 | iex
   Verify:       tina4 --version

## Create and run a project
   tina4 init python my-app
   cd my-app
   tina4 serve            # → http://localhost:7145

## Update   (returning users)
   tina4 update                       # upgrade the CLI
   uv pip install -U tina4-python     # upgrade the framework, inside a project
```

**What changes elsewhere.**

- **Landing "Get Started" becomes the *what*, not the *how*** — what Tina4 is, what you need (concepts), and "pick a language." It links to the Installation / Update section of **Getting Started / Quick Reference** instead of carrying its own command list.
- **Delete the broken four-line quickstart** (`pip install tina4-python → tina4 init → …`) from the landing page. Its `pip install tina4-python` lead is the trap: it yields the framework package + the `tina4python` script, not the `tina4` CLI the next line calls (and that script then crashes on a cp1252 Windows console — PY-01-09).
- **Bare `pip install tina4-python` appears only in the separate, clearly-labelled "Manual Setup (No CLI)" route** — the one that ends in `python app.py` and never invokes `tina4`. It must not lead any CLI-based flow.
- **The Getting Started chapter narrative references Getting Started / Quick Reference** rather than re-listing the commands, so setup commands live in exactly one place.

**Relationship to FIX-01.** FIX-01 restructures the Getting Started *chapter* in place (Prerequisites / Install the CLI / Create project). FIX-07 puts those same canonical commands in the first section of **Getting Started / Quick Reference** so they exist once and other pages link to them. Both share the three-concept model; FIX-07 supersedes the *install portion* of any page that currently re-lists commands.

**Acceptance criteria.**

- A reader with only their OS installed follows the Installation / Update section top-down and reaches a running server — no scroll-back, no missing-tool error, no missing-command error (`tina4 init` never runs before the CLI is installed).
- No page presents a CLI-based flow whose first command is `pip install tina4-python`. That command appears only in the "Manual Setup (No CLI)" route.
- The words "Tina4 CLI" and "tina4-python" each live in one heading scope, with an explicit "these are different things" call-out.
- An Update sub-section lets a returning user upgrade the CLI (`tina4 update`) and the framework package, each labelled for its target.
- The Quick Reference page is titled **"Getting Started / Quick Reference"** with Installation / Update as its first section; the landing page's old four-line quickstart no longer exists and links here instead.


## Maintenance & Audit Log

Version bumps, GitHub re-checks, fix re-verifications, and audit verdicts — moved here from
`outstanding-tasks.md` per its move-and-delete contract. This is the durable home for
completed-action records; the backlog holds only resulting OPEN todo items.

### 2026-07-02 — framework bump 3.13.49 + filing-candidate re-verification (PY-12-03, PY-06-06)

- **tina4-python 3.13.48 → 3.13.49** (`uv lock --upgrade-package tina4-python` + `uv sync`). CLI checked via `tina4 update`: 3.8.53 already latest. Upstream 48→49 diff: version bump, `public/js/tina4js.min.js`, docs/skills only — **no `queue/`, `test_client/`, or `core/server.py` changes.**
- Per the version-stamp policy, no blanket re-verify — only the two filing candidates probed:
  - **PY-12-03 STILL OPEN on 3.13.49** — brokers restarted (`tina4_rabbit`, `tina4_mongo`); `test_ch12_queue_backend_lifecycle.py` expectation suite green with 0 skips (live brokers reached); `size(status)` stubs byte-identical at the same lines.
  - **PY-06-06 STILL OPEN on 3.13.49, both sides** — direct-dispatch probe: `_invoke_handler` injects `id=42` into the documented positional handler (`{"got":42}`); Test client flat call unchanged → `test_ch06_routes.py` TypeError sentinels pass. (Server-side had been unverified since 3.13.30 — now closed.)
- Report bodies drafted in chat per report-brevity, adversarially verified (3-agent refute pass; PY-12-03 corrected on 3 points, PY-06-06 clean), and GitHub cross-checked for duplicates (371 comments + all bodies, both repos — none). **Both FILED 2026-07-02**: PY-12-03 → [#144](https://github.com/tina4stack/tina4-book/issues/144#issuecomment-4868451205), PY-06-06 → [#142](https://github.com/tina4stack/tina4-book/issues/142#issuecomment-4868455231). Unfiled count 30 → 28.

### 2026-07-02 — Ch12 audit coverage gaps closed (AUD-12-1/2/3/L)

- **Environment:** Docker recovered (`tina4_pg` up, healthy); the 3 queue brokers stay down — not needed (all Ch12 gaps are file-backend). tina4-python 3.13.48 · CLI 3.8.53.
- **AUD-12-1 (S8)** — NEW `documentation-testing/pypy/tests/test_ch12_orders_route_s8.py` (2 tests): in-process `tina4_python.test` client drives the registered `POST /api/orders` handler — exact fan-out payloads on emails/invoices/warehouse_sync, instant-201 body while all jobs still pending, 1:1 fan-out per request. Client bypasses the Bearer gate (PY-06-13 mechanics, disclosed); served 401 stays PY-12-10.
- **AUD-12-2 (S11/S12)** — NEW `documentation-testing/pypy/tests/test_ch12_email_routes_s12.py` (6 tests): all four email endpoints + the 400 branch both ways (one-missing → exactly that error; empty → all three). Retry test constructed with exactly 1 dead so the documented outcome and retry()'s one-per-call actual (PY-12-04) coincide, disclosed.
- **AUD-12-3 (S7)** — `retry_failed()` VERIFIED FAITHFUL (2 new tests in the S7 file): re-queues a dead job that is under a RAISED `max_retries` (the constructable "dead and under the limit" state); leaves at-limit jobs dead. The tautology concern is resolved — no doc-claim ambiguity, no finding.
- **AUD-12-L** — all four LOW items closed: `failed()` both exclusive bounds + pop()-path same-id re-delivery (S7 file), `job.retry()` default no-hold (S6 file), `TINA4_QUEUE_URL` own-knob selection (S9 file).
- **Runs:** new tests green ×2 (deterministic); full ch12 sweep **86 passed / 26 skipped**, 0 failed. **No new findings — every gap verified faithful.** Ledger closed-block + progress row updated; backlog rows removed.

### 2026-06-30 — framework bump + doc refresh + doc-system audit
- **tina4-python 3.13.47 → 3.13.48** (latest; released 2026-06-29). `uv lock --upgrade-package tina4-python` + `uv sync`; only `documentation-testing/pypy/uv.lock` changed. CLI stays 3.8.53. 3.13.48 = i18n interpolation hardening + swagger decorator-stacking fix (#59) + bundled-skill doc-truth; **none touch any open finding** — no re-verify per version-stamp rule.
- **Docs refreshed** (`tina4 books`): only `36-releases.md` changed vs the local copy; all implemented chapters (06/07/12/18) byte-identical → every line-ref still valid.
- **Coverage / fidelity audit** (12-agent workflow `wpr69vtjq`, Ch06/07/12/18): fidelity SOLID — **ZERO our-divergences**; every divergence-asserting test is a correct sentinel for a logged finding; no rigging. ~185 / 221 documented claims covered. Real coverage gaps found → **AUD-\*** (tracked in each chapter's ledger Open items). Empirical suite re-run blocked this session (Docker engine wedged; native PG-service start needs admin).
- **Doc-system audit + optimization** (7-agent workflow `wcb2k5all`): structure judged sound, drift fixed — created `coverage-ledger/_TEMPLATE.md`; backfilled `py-ch06-orm.md` + `py-ch18-testing.md` ledgers; slimmed the 4 Evaluation Progress cells (~31 KB of run-on narrative → one-line status + ledger link); relocated the FIX-04 spec to `notes/` (PY-18-04 is closed); consolidated memory (folded `upstream-labels` + `doc-reference-style` into `report-brevity`, regrouped MEMORY.md); reconciled the coverage legend to 5 states; fixed cross-file contradictions (phph workspace state, retired bracketed-title, superseded 3-section report shape, BH-46 stale re-check note).

### 2026-06-29 — maintenance check (update + GitHub responses + fix re-verify)
- CLI `tina4 update` 3.8.52 → **3.8.53**; framework `tina4-python` 3.13.47 already latest at the time.
- **GitHub:** no new maintainer activity on any filed thread. book #140 / #142 / #143 / #144 all OPEN (last comment MichaelC8E); py #46 CLOSED, #47 / #48 OPEN (maintainer "fixed in vX" replies), #49 OPEN.
- **Fix re-verify on 3.13.47** (6 issue probes, 32 passed / 4 xfailed): py #46 error-visibility, #47 driver ImportError, #48 schema-aware introspection all FIXED and stay fixed; BH-46/47/48/49 confirmed fixed/closed. The 4 xfails are drafted-patch-shape assertions the maintainer chose not to ship (not residual bugs, no XPASS).

