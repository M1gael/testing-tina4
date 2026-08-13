# CLAUDE.md

Orientation for new collaborators (human or LLM). This file is a map. The stable
conventions/protocol live in `documentation-testing/readme.md`; the mutable record — chapter coverage,
the Bug Hunt index, and Suggested Fixes — lives in
`findings-log.md`; per-section **coverage ledgers** (✓/⛔/⏸ per snippet+option, with
version-stamped sign-offs) live in **`coverage-ledger/`**, one markdown per chapter. The
cross-session **work backlog** (asked-for-but-not-yet-done) lives in **`outstanding-tasks.md`**
at the repo root — check it when resuming. Read this
first to know *where* things are; read `documentation-testing/readme.md` for the rules and `findings-log.md` for the data.

Repo shape at a glance — two evaluation axes plus their shared record:

| Path | What |
|---|---|
| `documentation-testing/` | **Doc-fidelity testing** (the primary job) — protocol spec in `readme.md`, one workspace per language: `pypy/`, `phph/`, `ruru/` |
| `agent-testing/` | **AI-tool evaluation** — can models build with Tina4 given the context Tina4 ships. Findings are not ledger-eligible until re-tested (see that dir's readme) |
| `comparison-testing/` | **Comparative measurement** — what a developer saves or loses choosing Tina4 over Flask/FastAPI/Django. Feature-matched apps, scripted counting. Findings are not ledger-eligible (see that dir's readme) |
| `bug-hunting/` | Long-form evidence per assigned `BH-<n>` investigation |
| `coverage-ledger/` | Per-chapter ✓/⛔/⏸ ledgers, one markdown each |
| `known-issues/ledger.md` | **Every issue, all languages** — documentation and framework code, one row each, with the version last reproduced on and how to reproduce it |
| `findings-log.md` | The record — coverage, Bug Hunt index, Suggested Fixes. The Known Issues Log **moved out** to `known-issues/ledger.md` on 2026-08-13 |
| `tutorial/` | Working notes for the **tutorial / course** section — `book-7-course` has a 36-module syllabus and no modules built. Nothing here ships |
| `outstanding-tasks.md` | Cross-session backlog, including the docs PRs in flight |
| `documentation/tina4-book/` | The documentation under test (untracked — symlink or `tina4 books`) |
| `dev/`, `docker-compose.yml` | Local Postgres fixture |

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
2. Implement its code examples verbatim in the language's workspace (`documentation-testing/pypy/`, `documentation-testing/phph/`, `documentation-testing/ruru/`).
3. Run via the `tina4` CLI and observe.
4. Log discrepancies as a row in `known-issues/ledger.md`.

This is **documentation-fidelity testing**: the work verifies whether a new user
following the docs would succeed. The harness *is* the new user.

## Where canonical info lives

Two files. **`documentation-testing/readme.md`** holds the stable conventions/protocol — the spec; if anything
disagrees with it, **`documentation-testing/readme.md` wins**. **`findings-log.md`** holds the mutable record
(coverage, findings, fixes). This file (CLAUDE.md) is the thin map and duplicates neither.

| Topic | Where |
|---|---|
| Protocol rules (12 non-negotiable rules) | `documentation-testing/readme.md` → `## Protocol: Chapter-Based Evaluation` |
| File / naming conventions (chapter prefix, test prefix, probe prefix, migrations, seeds) | `documentation-testing/readme.md` → `## Standard Implementation Workflow` + `## Workspaces` |
| Patching convention (PATCH markers, OLD lines, newest-stays-verbatim) | `documentation-testing/readme.md` → `## Patching Convention` |
| Issue reporting (ledger schema + terminal-output snippet format + sub-letter notation) | `documentation-testing/readme.md` → `## Issue Report Format`; the live column set is at the top of `known-issues/ledger.md` |
| Upstream filing format (plain `<ID> — title` opening line, location/Issue/Origin body, splitting findings) | `documentation-testing/readme.md` → `## Issue Report Format` → "Upstream filing — …" |
| Quick-reference summary of all conventions | `documentation-testing/readme.md` → `## Convention Recap` |
| Current chapter coverage | `findings-log.md` → `## Evaluation Progress` |
| Per-section coverage ledgers (✓/⚠/⛔/⏸/`n/a` per snippet+option, version-stamped sign-offs) | `coverage-ledger/<lang>-ch<NN>-<topic>.md` — **currently only `py-ch07` + `py-ch12` exist; until every implemented chapter has one, the Evaluation Progress table in `findings-log.md` is the authoritative coverage index.** Template: `coverage-ledger/_TEMPLATE.md` |
| All confirmed findings, every language | `known-issues/ledger.md` — 84 rows; supersedes the Known Issues Log |
| Assigned bug investigations (`BH-<n>` rows) | `known-issues/ledger.md` (the rows) + `findings-log.md` → `## Bug Hunt` (what they are) + `bug-hunting/` (evidence) |
| Proposed fixes for findings (long-form) | `findings-log.md` → `## Suggested Fixes` |

## Non-negotiables to be aware of up front

These are the bright lines a new collaborator most often trips over. The full Protocol
in `documentation-testing/readme.md` is the source of truth — these are pointers, not a replacement.

- **Wait for direction** — don't start a chapter until the user names it.
- **One language per conversation** — never drift between `documentation-testing/pypy/` / `documentation-testing/phph/` / `documentation-testing/ruru/`.
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
  is wired via `documentation-testing/pypy/.env` + `documentation-testing/pypy/conftest.py`. Symptom if not: `RuntimeError: No
  database bound`. Full setup in *Running / testing* below.
- **Read-only framework — never edit framework source** — the installed `tina4_python`
  package (`documentation-testing/pypy/.venv/lib/python3.14/site-packages/tina4_python/`), the `tina4` CLI, and any vendored
  framework code are **off-limits**: no patch, shim, or monkey-patch, even for a severe bug.
  Only OUR files get written (tests, probes, fixtures, mocks, logs). `documentation-testing/readme.md` rule 10.
- **Strict traceability — every test cites the doc** — each test/demo carries the exact
  quoted claim + documentation file path it verifies; no test without a documented claim, no
  speculative edge cases the docs don't state. `documentation-testing/readme.md` rule 11.
- **No test rigging** — when the framework diverges from a faithful test, the test FAILS and
  stays red (record it). Never weaken/`xfail`/skip/`try-except` a test to go green; edit a
  test only to read the doc more faithfully. `documentation-testing/readme.md` rule 12.
- **Coverage ledger — never tag a bare "complete"** — before a section is marked done, enumerate
  every snippet + every named option and mark each `tested` / `blocked` / `deferred`; the progress
  status names the open dimensions (e.g. "file-backend complete; rabbitmq/kafka/mongo open"), never
  just "complete". `documentation-testing/readme.md` Workflow step 7.

## Language project directories

| Dir | Language | Tina4 version | Entry | Package manager | Notes |
|-----|----------|---------------|-------|-----------------|-------|
| `documentation-testing/pypy/` | Python (primary workspace) | tina4-python **3.13.94** installed (`.venv`; `pyproject.toml` floor is `>=3.1.0`) | `app.py` | `uv` | has `.tina4/` agents |
| `documentation-testing/phph/` | PHP | *not bootstrapped* | (will be `index.php`) | composer | only `vendor/` present — no `index.php`/`src/` yet; run `tina4 init php .` before working |
| `documentation-testing/ruru/` | Ruby | *not yet bootstrapped* | (will be `app.rb`) | bundler | empty (`.gitkeep` only); run `tina4 init ruby .` before working |

All three language workspaces live under `documentation-testing/`. Earlier revisions of this
file placed Ruby at the repo root as `ruru/` — it is `documentation-testing/ruru/`.

The global `tina4` CLI (Rust binary) is at **`/usr/local/bin/tina4`** on this machine and is
currently **3.8.64**. (Earlier revisions of this file documented a Windows host —
`~/AppData/Local/tina4/tina4.exe`; the harness now runs on Fedora Linux.) The CLI and the
per-language frameworks are versioned
independently — update with `tina4 update` (CLI) and `uv pip install --upgrade
tina4-python` / `composer update` / `bundle update` (frameworks).

## Running / testing

**Before running the Python suite: a database must be connected.** Most ORM-backed
tests (Ch06, Ch18, etc.) raise `RuntimeError: No database bound. Call bind_database(db)
or set TINA4_DATABASE_URL in .env` on the first ORM call if none is. The workspace is
wired so this is normally automatic:

1. **Start Postgres** — `docker compose up -d` from the repo root (see *Local Postgres
   fixture* below). Confirm `docker compose ps` shows `tina4_pg` healthy.
2. **`documentation-testing/pypy/.env` sets `TINA4_DATABASE_URL`** → `postgresql://postgres:tina4test@localhost:5432/tina4testingdb`.
3. **`documentation-testing/pypy/conftest.py` loads `.env` into `os.environ`** before any test (the framework
   itself only reads `.env` under `tina4 serve`, not under pytest). The ORM reads
   `TINA4_DATABASE_URL` lazily, so this binds the whole suite.

If tests raise "No database bound": container down, `.env` missing the URL, or running
pytest from outside `documentation-testing/pypy/` (so conftest didn't load). To target a different DB, edit
`documentation-testing/pypy/.env`.

```
Python:  uv run tina4 serve              # dev server with watcher/reload
         uv run tina4 test                # full test suite (pytest wrapper — see PY-18-04)
         uv run python -m pytest <path>   # target a specific file (pytest binary itself is not on PATH)
PHP:     TBD — workspace not bootstrapped (run `tina4 init php .` in documentation-testing/phph/ first).
Ruby:    TBD — workspace not bootstrapped (run `tina4 init ruby .` in documentation-testing/ruru/ first).
```

Watch `logs/tina4.log` for registration/execution errors while testing.

## Local Postgres fixture (live-PG probes)

The live-PG probes (`documentation-testing/pypy/tests/test_issue_46_*.py`, `hello_pg.py`) connect to a local Postgres on `localhost:5432`, user `postgres` / password `tina4test`. Two databases:

| DB | Purpose | Schema |
|---|---|---|
| `tina4_bug46` | BH-46 reproduction fixture | `gift_cards (id SERIAL, created_by_email VARCHAR, owned_by_email VARCHAR, amount NUMERIC, is_deleted BOOLEAN, created_at TIMESTAMP)` |
| `tina4testingdb` | **Default suite DB** (`.env` `TINA4_DATABASE_URL`) — all ORM-backed chapter tests bind here | `items` (seed) + chapter tables created by tests at runtime (`notes`, `users`, `products`, …) |

Probes auto-skip (`pytest.mark.skipif`) when the instance is unreachable — a machine without the fixture still runs the mocked probes cleanly.

**Runtime: Docker** (`postgres:18`). `docker-compose.yml` at the repo root defines the `tina4_pg` service; `dev/postgres-init/init.sh` runs once on first start and creates + seeds both DBs above. Note the data volume mounts at `/var/lib/postgresql` (not `/data`) — required by `postgres:18`.

```bash
docker compose up -d          # start (from repo root)
docker compose down           # stop, keep data
docker compose down -v        # stop + wipe volume → init.sh re-seeds on next up
docker compose logs postgres  # watch init / readiness
```

**Bring-up from zero:** `docker compose up -d`, wait for `(healthy)` in `docker compose ps`. The init script seeds `gift_cards` (2 rows) + `items` (3 rows).

**Verify:** `docker compose exec postgres psql -U postgres -c "\l"` lists both DBs; `cd documentation-testing/pypy; uv run python tests/hello_pg.py` round-trips.

**`init.sh` line endings must stay LF** (it runs in a Linux container) — pinned via `.gitattributes` (`*.sh text eol=lf`). CRLF breaks the shebang.

Docker is the only runtime on this machine. Earlier revisions documented a native **Windows** `postgresql-x64-18` service as a fallback (`Start-Service postgresql-x64-18`) — that host is gone; the harness runs on Fedora Linux. For a native fallback here, use the distro package (`postgresql-server`) on the same port/creds/DBs — probes don't care which is serving.

## Local queue brokers (Chapter 12 queue backend probes)

The queue backend-parity / lifecycle tests (`documentation-testing/pypy/tests/test_ch12_queue_backend_parity.py`, `test_ch12_queue_backend_lifecycle.py`, `test_ch12_queue_kafka_semantics.py`, `test_ch12_queue_mongo_clear_probe.py`) round-trip against real brokers. Stood up with plain `docker run` (not in `docker-compose.yml`):

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

**Live backend showcase (USER-requested visual):** with all brokers up + `tina4 serve`, open `GET /queue/backends` (`src/routes/queue_backend_matrix.py`, linked from the Chapter-12 page `/chapter/12`). It runs the full documented queue API (20 ops) against file/RabbitMQ/MongoDB/Kafka live and renders a per-claim parity grid — the visual proof of S2's "work identically" claim. Backend selection is process-global env, so runs are lock-serialised; each op runs in a daemon thread with a timeout so Kafka's non-delivery can't hang serve.

## Documentation source — `documentation/tina4-book/`

**Untracked** (`.gitignore`) — it is an upstream repo, not harness content. Populate it either way:

- **Symlink a local clone** (current setup on this machine):
  `git clone git@github.com:tina4stack/tina4-book.git` somewhere, then
  `ln -s <path-to-clone> documentation/tina4-book`. Keeps one copy shared across projects
  and lets you `git pull` for refreshes.
- **Or pull with the CLI** — `tina4 books` extracts into place.

If `documentation/tina4-book/` is missing or dangling, no chapter work can start — every
Protocol step 1 reads from here.

Eight "books", chapters as markdown under `book-N-*/chapters/NN-topic.md`. Counts as of
2026-08-03 (they grow — re-count rather than trusting this table):

| Book | Dir | Chapters |
|------|-----|----------|
| Understanding | `book-0-understanding` | 4 |
| Python | `book-1-python` | 39 |
| PHP | `book-2-php` | 39 |
| Ruby | `book-3-ruby` | 38 |
| Node.js | `book-4-nodejs` | 38 |
| JavaScript (frontend/Frond) | `book-5-javascript` | 19 |
| Delphi | `book-6-delphi` | 15 |
| Course | `book-7-course` | 2 |

- `plan/` — API reference (`API-REFERENCE.md`), brand guide, chapter-reshuffle notes, and the
  per-subsystem parity audits as flat `parity-<subsystem>.md` files (auth, database, orm,
  queue, request-response, router, session, sse, template, websocket, remaining) plus
  `PARITY-MATRIX-*.md`. There is **no `plan/parity/` subdirectory** — earlier revisions of
  this file claimed one.
- The **live site at https://tina4.com is the actual source of truth**; this local copy is a
  fallback. See the Source of Truth section in `documentation-testing/readme.md`.

## Other directories in the tree (background)

Not part of the harness's workflow, but present in the repo:

- **`.agents/`** (gitignored) — local Claude skills (reporting, verification); not in fresh clones.
- **`.prompts/`, `.skills/`** — duplicates of the same three Tina4 guides; they describe how to
  *build with* Tina4 and would tell you to "fix bugs proactively." The Protocol overrides.
- **`documentation-testing/pypy/.tina4/agents/`** — Tina4's own agent configs. Part of the framework under test, not this harness.
- **`documentation-testing/php-temp-test/`** — a vendored tina4php scratch/integration env. Ignore unless explicitly using it.
- **`dev/postgres-init/`** — one-shot init script for the `tina4_pg` Docker fixture (see *Local Postgres fixture*).

Two directories earlier revisions of this file described **do not exist**: `scratch/skills/`
(deep-reference guide copies — use `.skills/`) and `notes/` (relocated long-form design notes;
the referenced `FIX-04-test-output-formatter.md` is nowhere in the repo). The `notes/` directory
at the *gitdir root* is an unrelated Obsidian vault — not this repo's.

## `agent-testing/` — can AI tools build with Tina4?

A second evaluation axis, distinct from doc-fidelity. `documentation-testing/` asks *do the docs
work for a human reader*; `agent-testing/` asks *does the framework's AI-facing context work for
a model*. Three arms — `codex-skill-delivery/` (does `tina4 ai` context reach OpenAI Codex),
`ai-context-delivery/` (the scaffolded app carrying all seven context files),
`small-model-tiers/` (the `.tina4/` agent on Qwen 27B–36B, three difficulty tiers). See
[`agent-testing/readme.md`](agent-testing/readme.md).

**Its findings are NOT KI Log material.** Agent runs carry no quoted-documented-claim trace, so
rules 11–12 exclude them. They collect in `agent-testing/unverified-leads.md` and must be
re-tested inside `documentation-testing/` against a real chapter before earning a `PY-NN-NN` ID.

## Git

- Remote: `git@github.com:M1gael/testing-tina4.git`, default branch `main`. Note this repo
  uses the **`M1gael`** identity on plain `github.com`; the upstream `tina4stack` repos are
  cloned over the `github-work` SSH alias (`MichaelC8E`). Don't cross the two.
- **Single branch in practice.** `main` holds everything: chapter implementations, probes
  (doc-fidelity and bug-hunt alike, each tagged with a `# Probe — covers <ID>` header line),
  fixtures, the logs, and the `bug-hunting/` evidence directory (40 tracked files).
- **The documented two-branch workflow was never implemented.** Earlier revisions described a
  `bug-hunting` scratch branch for rough investigation work, with `bug-hunting/` never merging
  to `main`. No such branch exists locally or on `origin`, and the directory is tracked on
  `main`. Either create the branch and move scratch work onto it, or drop the convention —
  until then `main` is the only branch. See `bug-hunting/README.md` → *Branch scope*.
- Commit messages in history are conventional-ish (`test(python):`, `docs:`, `chore:`,
  `feat(php):`) and frequently reference the tina4 version and issue IDs being verified.
- Before any user-requested `/commit`, follow the Issue Report Format in `documentation-testing/readme.md` for
  any finding being introduced in the commit.
