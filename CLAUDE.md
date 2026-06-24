# CLAUDE.md

Orientation for new collaborators (human or LLM). This file is a map. The stable
conventions/protocol live in `readme.md`; the mutable record — chapter coverage,
the Known Issues Log, the Bug Hunt index, and Suggested Fixes — lives in
`findings-log.md`; per-section **coverage ledgers** (✓/⛔/⏸ per snippet+option, with
version-stamped sign-offs) live in **`coverage-ledger/`**, one markdown per chapter. Read this
first to know *where* things are; read `readme.md` for the rules and `findings-log.md` for the data.

## What this repo is

A **QA / evaluation harness for the Tina4 web framework**, not an app and not the
framework itself. The job is to implement the official Tina4 documentation *exactly
as written*, in real Tina4 projects, and record every place the framework's actual
behaviour deviates from the docs.

The assistant acts as an **independent QA Auditor**: the framework is **read-only** (never
patched/fixed, even on a severe bug), every test **traces to a quoted documented claim** (no
speculative edge cases), and tests are **never rigged** — a genuine framework divergence stays
red and is reported, not papered over.

The loop is:

1. Take a chapter from `documentation/tina4-book/`.
2. Implement its code examples verbatim in the language's workspace (`pypy/`, `phph/`, `ruru/`).
3. Run via the `tina4` CLI and observe.
4. Log discrepancies in the Known Issues Log inside `findings-log.md`.

This is **documentation-fidelity testing**: the work verifies whether a new user
following the docs would succeed. The harness *is* the new user.

## Where canonical info lives

Two files. **`readme.md`** holds the stable conventions/protocol — the spec; if anything
disagrees with it, **`readme.md` wins**. **`findings-log.md`** holds the mutable record
(coverage, findings, fixes). This file (CLAUDE.md) is the thin map and duplicates neither.

| Topic | Where |
|---|---|
| Protocol rules (12 non-negotiable rules) | `readme.md` → `## Protocol: Chapter-Based Evaluation` |
| File / naming conventions (chapter prefix, test prefix, probe prefix, migrations, seeds) | `readme.md` → `## Standard Implementation Workflow` + `## Workspaces` |
| Patching convention (PATCH markers, OLD lines, newest-stays-verbatim) | `readme.md` → `## Patching Convention` |
| Issue reporting (KI Log six-column schema + terminal-output snippet format + sub-letter notation) | `readme.md` → `## Issue Report Format` |
| Upstream filing format (plain `<ID> — title` opening line, location/Issue/Origin body, splitting findings) | `readme.md` → `## Issue Report Format` → "Upstream filing — …" |
| Quick-reference summary of all conventions | `readme.md` → `## Convention Recap` |
| Current chapter coverage | `findings-log.md` → `## Evaluation Progress` |
| Per-section coverage ledgers (✓/⛔/⏸ per snippet+option, version-stamped sign-offs) | `coverage-ledger/<lang>-ch<NN>-<topic>.md` (e.g. `coverage-ledger/py-ch12-queues.md`) |
| All confirmed findings (Known Issues Log) | `findings-log.md` → `## Known Issues Log` |
| Assigned bug investigations (`BH-<n>` rows) | `findings-log.md` → `## Known Issues Log` (the rows) + `## Bug Hunt` (what they are) |
| Proposed fixes for findings (long-form) | `findings-log.md` → `## Suggested Fixes` |

## Non-negotiables to be aware of up front

These are the bright lines a new collaborator most often trips over. The full Protocol
in `readme.md` is the source of truth — these are pointers, not a replacement.

- **Wait for direction** — don't start a chapter until the user names it.
- **One language per conversation** — never drift between `pypy/` / `phph/` / `ruru/`.
- **Documentation ONLY, nothing else** — implement exactly what the chapter literally
  shows. Not framework source, not the dev guide / CLAUDE.md, not other chapters, not
  prior knowledge. The simulated reader knows nothing beyond the page.
- **No workarounds — if it doesn't work, it DOESN'T WORK** — never reach for an
  adjustment the chapter doesn't show (different signature, missing import, alternate
  object, extra setup). Record the failure and stop. The only verbatim deviation is a
  **USER-triggered patch** to unblock *other* sections (see Patching Convention).
- **Log the symptom; don't investigate** — capture the literal output/error and move on.
  Root-cause investigation happens ONLY when the USER explicitly asks for it.
- **Stay inside `src/{routes,orm,templates}/`, `migrations/`, `seeds/`, `tests/`** —
  no throwaway scripts next to `app.py`.
- **A database must be connected before ORM-backed tests run** (Ch06, Ch07, Ch18, and
  any chapter that touches the ORM). Start Postgres (`docker compose up -d`) — the rest
  is wired via `pypy/.env` + `pypy/conftest.py`. Symptom if not: `RuntimeError: No
  database bound`. Full setup in *Running / testing* below.
- **Read-only framework — never edit framework source** — the installed `tina4_python`
  package (`pypy/.venv/Lib/site-packages/tina4_python/`), the `tina4` CLI, and any vendored
  framework code are **off-limits**: no patch, shim, or monkey-patch, even for a severe bug.
  Only OUR files get written (tests, probes, fixtures, mocks, logs). `readme.md` rule 10.
- **Strict traceability — every test cites the doc** — each test/demo carries the exact
  quoted claim + documentation file path it verifies; no test without a documented claim, no
  speculative edge cases the docs don't state. `readme.md` rule 11.
- **No test rigging** — when the framework diverges from a faithful test, the test FAILS and
  stays red (record it). Never weaken/`xfail`/skip/`try-except` a test to go green; edit a
  test only to read the doc more faithfully. `readme.md` rule 12.
- **Coverage ledger — never tag a bare "complete"** — before a section is marked done, enumerate
  every snippet + every named option and mark each `tested` / `blocked` / `deferred`; the progress
  status names the open dimensions (e.g. "file-backend complete; rabbitmq/kafka/mongo open"), never
  just "complete". `readme.md` Workflow step 7.

## Language project directories

| Dir | Language | Tina4 version | Entry | Package manager | Notes |
|-----|----------|---------------|-------|-----------------|-------|
| `pypy/` | Python (primary workspace) | tina4-python **3.13.43** (`uv.lock`) | `app.py` | `uv` | has `.tina4/` agents |
| `phph/` | PHP | *not yet bootstrapped* | (will be `index.php`) | composer | empty dir; run `tina4 init php .` before working |
| `ruru/` | Ruby | *not yet bootstrapped* | (will be `app.rb`) | bundler | empty dir; run `tina4 init ruby .` before working |

The global `tina4` CLI (Rust binary at `~/AppData/Local/tina4/tina4.exe` on Windows)
is currently **3.8.51**. The CLI and the per-language frameworks are versioned
independently — update with `tina4 update` (CLI) and `uv pip install --upgrade
tina4-python` / `composer update` / `bundle update` (frameworks).

## Running / testing

**Before running the Python suite: a database must be connected.** Most ORM-backed
tests (Ch06, Ch18, etc.) raise `RuntimeError: No database bound. Call bind_database(db)
or set TINA4_DATABASE_URL in .env` on the first ORM call if none is. The workspace is
wired so this is normally automatic:

1. **Start Postgres** — `docker compose up -d` from the repo root (see *Local Postgres
   fixture* below). Confirm `docker compose ps` shows `tina4_pg` healthy.
2. **`pypy/.env` sets `TINA4_DATABASE_URL`** → `postgresql://postgres:tina4test@localhost:5432/tina4testingdb`.
3. **`pypy/conftest.py` loads `.env` into `os.environ`** before any test (the framework
   itself only reads `.env` under `tina4 serve`, not under pytest). The ORM reads
   `TINA4_DATABASE_URL` lazily, so this binds the whole suite.

If tests raise "No database bound": container down, `.env` missing the URL, or running
pytest from outside `pypy/` (so conftest didn't load). To target a different DB, edit
`pypy/.env`.

```
Python:  uv run tina4 serve              # dev server with watcher/reload
         uv run tina4 test                # full test suite (pytest wrapper — see PY-18-04)
         uv run python -m pytest <path>   # target a specific file (pytest binary itself is not on PATH)
PHP:     TBD — workspace not bootstrapped (run `tina4 init php .` in phph/ first).
Ruby:    TBD — workspace not bootstrapped (run `tina4 init ruby .` in ruru/ first).
```

Watch `logs/tina4.log` for registration/execution errors while testing.

## Local Postgres fixture (live-PG probes)

The live-PG probes (`pypy/tests/test_issue_46_*.py`, `hello_pg.py`) connect to a local Postgres on `localhost:5432`, user `postgres` / password `tina4test`. Two databases:

| DB | Purpose | Schema |
|---|---|---|
| `tina4_bug46` | BH-46 reproduction fixture | `gift_cards (id SERIAL, created_by_email VARCHAR, owned_by_email VARCHAR, amount NUMERIC, is_deleted BOOLEAN, created_at TIMESTAMP)` |
| `tina4testingdb` | **Default suite DB** (`.env` `TINA4_DATABASE_URL`) — all ORM-backed chapter tests bind here | `items` (seed) + chapter tables created by tests at runtime (`notes`, `users`, `products`, …) |

Probes auto-skip (`pytest.mark.skipif`) when the instance is unreachable — a machine without the fixture still runs the mocked probes cleanly.

**Runtime: Docker** (`postgres:18`). `docker-compose.yml` at the repo root defines the `tina4_pg` service; `dev/postgres-init/init.sh` runs once on first start and creates + seeds both DBs above. Note the data volume mounts at `/var/lib/postgresql` (not `/data`) — required by `postgres:18`.

```powershell
docker compose up -d          # start (from repo root)
docker compose down           # stop, keep data
docker compose down -v        # stop + wipe volume → init.sh re-seeds on next up
docker compose logs postgres  # watch init / readiness
```

**Bring-up from zero:** `docker compose up -d`, wait for `(healthy)` in `docker compose ps`. The init script seeds `gift_cards` (2 rows) + `items` (3 rows).

**Verify:** `docker compose exec postgres psql -U postgres -c "\l"` lists both DBs; `cd pypy; uv run python tests/hello_pg.py` round-trips.

**`init.sh` line endings must stay LF** (it runs in a Linux container) — pinned via `.gitattributes` (`*.sh text eol=lf`). CRLF breaks the shebang.

A native Windows install (`postgresql-x64-18` service) was the original runtime; it's now stopped + set to Manual start. To fall back to it, stop the container (`docker compose down`) and `Start-Service postgresql-x64-18` — same port/creds/DBs, so probes don't care which is serving.

## Local queue brokers (Chapter 12 queue backend probes)

The queue backend-parity / lifecycle tests (`pypy/tests/test_ch12_queue_backend_parity.py`, `test_ch12_queue_backend_lifecycle.py`, `test_ch12_queue_kafka_semantics.py`, `test_ch12_queue_mongo_clear_probe.py`) round-trip against real brokers. Stood up with plain `docker run` (not in `docker-compose.yml`):

```bash
docker run -d --name tina4_rabbit -p 5672:5672 rabbitmq:3
docker run -d --name tina4_mongo  -p 27017:27017 mongo:7
docker run -d --name tina4_kafka  -p 9092:9092 apache/kafka:3.7.0   # KRaft single-node, defaults
```

Drivers per Chapter 12 S2 (`uv add pika pymongo confluent-kafka`): `pika` 1.4.1, `pymongo` 4.17.0, `confluent-kafka` 2.14.2. The tests are **broker-gated** — each `socket`-checks its port and SKIPS if the broker is down (a logged blocker, never a false pass). Env per backend: `TINA4_QUEUE_BACKEND` + `TINA4_QUEUE_URL` (`amqp://guest:guest@localhost:5672` / `mongodb://localhost:27017/tina4`) or `TINA4_KAFKA_BROKERS=localhost:9092`.

```bash
docker stop tina4_rabbit tina4_mongo tina4_kafka     # free resources
docker start tina4_rabbit tina4_mongo tina4_kafka    # bring back for re-runs
```

Note: kafka/rabbitmq have raw-socket fallbacks (driver optional); **only mongodb hard-requires its driver** (`pymongo`) at construction. RabbitMQ guest/guest works from localhost only. Kafka first delivery lags ~16s (consumer-group join) — drain-once/immediate `pop()` return nothing (PY-12-02).

## Documentation source — `documentation/tina4-book/`

Seven "books", chapters as markdown under `book-N-*/chapters/NN-topic.md`:

| Book | Dir | Chapters |
|------|-----|----------|
| Understanding | `book-0-understanding` | 4 |
| Python | `book-1-python` | 38 |
| PHP | `book-2-php` | 38 |
| Ruby | `book-3-ruby` | 38 |
| Node.js | `book-4-nodejs` | 38 |
| JavaScript (frontend/Frond) | `book-5-javascript` | 16 |
| Delphi | `book-6-delphi` | 15 |

- `plan/` — API reference, brand guide, parity matrices. `plan/parity/` has per-subsystem
  parity audits (auth, database, orm, queue, router, session, sse, template, websocket).
- The **live site at https://tina4.com is the actual source of truth**; this local copy is a
  fallback (refreshable with `tina4 books`). See the Source of Truth section in `readme.md`.

## Other directories in the tree (background)

Not part of the harness's workflow, but present in the repo:

- **`.agents/`** (gitignored) — local Claude skills (reporting, verification); not in fresh clones.
- **`.prompts/`, `.skills/`** — duplicates of the same three Tina4 guides; they describe how to
  *build with* Tina4 and would tell you to "fix bugs proactively." The Protocol overrides.
- **`scratch/skills/`** — fuller copies of the same guides with `references/` subdirs. Deep reference.
- **`pypy/.tina4/agents/`** — Tina4's own agent configs. Part of the framework under test, not this harness.
- **`php-temp-test/`** — a vendored tina4php scratch/integration env. Ignore unless explicitly using it.

## Git

- Remote: `git@github.com:M1gael/testing-tina4.git`, default branch `main`.
- **Two-branch workflow.** `main` holds the refined state: chapter implementations,
  probes (doc-fidelity and bug-hunt alike, each tagged with a `# Probe — covers <ID>`
  header line), fixtures, and the readme logs. `bug-hunting` is the scratch branch for
  nasty/rough investigation work — draft comments, dead-end patches, multi-attempt
  iteration, and the `bug-hunting/` evidence directory (which never merges to `main`).
  When an investigation stabilises, its refined probes + readme rows are consolidated
  onto `main`; compare the branches at the end of an investigation to see what still
  needs cleaning up.
- Commit messages in history are conventional-ish (`test(python):`, `docs:`, `chore:`,
  `feat(php):`) and frequently reference the tina4 version and issue IDs being verified.
- Before any user-requested `/commit`, follow the Issue Report Format in `readme.md` for
  any finding being introduced in the commit.
