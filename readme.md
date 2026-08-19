# testing-tina4

A **QA harness for the Tina4 web framework** — not an app, and not the framework itself.

The job: implement the official Tina4 documentation *exactly as written*, in real Tina4
projects, and record every place the framework's actual behaviour deviates from the docs.
The harness plays the part of a new reader who knows nothing beyond the page in front of
them. If following the docs doesn't work, that is the finding.

```
testing-tina4/
├── readme.md                 this file — the map
├── documentation-testing/    the work: protocol, language workspaces, coverage, backlog
└── known-issues/             the record: every issue, one file
```

Two directories. One does the testing, the other holds the results.

## What each directory is for

| Path | Job |
|---|---|
| **`documentation-testing/`** | **All testing work.** The protocol spec plus one project workspace per language. |
| `documentation-testing/readme.md` | **The rules.** 13 non-negotiable protocol rules, naming conventions, patching convention, issue-report format. If anything anywhere disagrees with this file, this file wins. |
| `documentation-testing/pypy/` | **Python workspace** — the primary one, and the only bootstrapped one. Chapter implementations live in `src/`, tests in `tests/` (57 files). |
| `documentation-testing/phph/` | PHP workspace — **not bootstrapped**, `vendor/` only. Run `tina4 init php .` before working. |
| `documentation-testing/ruru/` | Ruby workspace — **not bootstrapped**, empty. Run `tina4 init ruby .` before working. |
| `documentation-testing/php-temp-test/` | A vendored tina4php scratch env. **Not a workspace.** Nothing references it; safe to delete. |
| `documentation-testing/coverage-ledger/` | **What has been exercised** — per chapter, per snippet, per named option, marked ✓/⚠/⛔/⏸/`n/a`. `README.md` is the index. Also carries the `AUD-*` rows: gaps in *our* test coverage, which are not Tina4 defects and deliberately never enter the ledger. |
| `documentation-testing/outstanding-tasks.md` | **The backlog.** Work asked for but not done, across sessions. Open items only — when something lands it moves to the ledger or the coverage ledger and the row is deleted. |
| `documentation-testing/audit-log.md` | **History.** Version bumps, retests, fix re-verifications, audit verdicts. Not a bug log. |
| **`known-issues/`** | **The record.** Every confirmed problem, nothing else. |
| `known-issues/ledger.md` | **The only issue log in this repo** — every language, documentation and framework code alike, one row per issue. **105 rows, 84 open.** |
| `known-issues/suggested-fixes.md` | Long-form `FIX-NN` proposals. Not a second issue list — the ledger's *Suggested fix* column points here. |

Four record types, four homes, no overlap:

- **An issue** → `known-issues/ledger.md`
- **Coverage** (what we did and didn't exercise) → `documentation-testing/coverage-ledger/`
- **A to-do** → `documentation-testing/outstanding-tasks.md`
- **What happened when** → `documentation-testing/audit-log.md`

## The loop

1. Take a chapter from `documentation/tina4-book/`.
2. Implement its code examples verbatim in the language workspace.
3. Run through the `tina4` CLI and observe.
4. Log every divergence as a row in `known-issues/ledger.md`.
5. Mark the chapter's snippets in `documentation-testing/coverage-ledger/`.

## Non-negotiables

Pointers, not a replacement — the full protocol is in `documentation-testing/readme.md`.

- **Wait for direction** — don't start a chapter until the user names it.
- **One language per conversation** — never drift between `pypy/`, `phph/`, `ruru/`.
- **Documentation only** — implement what the chapter literally shows. Not framework source,
  not the framework's own `CLAUDE.md` or skills, not other chapters, not prior knowledge.
- **No workarounds** — if the documented code doesn't work, it doesn't work. Never reach for
  an adjustment the chapter doesn't show. Record the failure and stop.
- **Log the symptom; don't investigate** — root-cause work happens only when asked for.
- **Never patch the workspace framework to get *past* something.** `tina4 init` installs a copy
  of the framework into the project's `.venv`. Editing that copy to unblock a failing test,
  silence an error, or make a chapter proceed is banned outright — the test then goes green
  against a framework nobody else has, and nothing in the output says so. Testing a candidate
  **fix** is a different act and is allowed; the line between them, and how to leave the
  workspace clean afterwards, is in *Fixing the framework*.
- **Pull before you work.** Every repo in play gets fetched at the start of a session, and a
  fork gets brought up to date with the official repo before anything is built on it. A finding
  measured against a stale checkout is a finding about the past — see *Working against the real
  repositories*.
- **Strict traceability** — every test cites the exact quoted claim and doc path it verifies.
  No test without a documented claim, no speculative edge cases.
- **No test rigging** — when the framework diverges from a faithful test, the test FAILS and
  stays red. Never weaken, `xfail`, skip or `try/except` a test to go green.
- **Never tag a bare "complete"** — enumerate every snippet and every named option before
  a section is called done.

## Workspaces

| Dir | Language | Version | Entry | Package manager |
|---|---|---|---|---|
| `documentation-testing/pypy/` | Python (primary) | tina4-python **3.13.105** in `.venv` | `app.py` | `uv` |
| `documentation-testing/phph/` | PHP | *not bootstrapped* | (`index.php`) | composer |
| `documentation-testing/ruru/` | Ruby | *not bootstrapped* | (`app.rb`) | bundler |

The `tina4` CLI (Rust binary) is at `/usr/local/bin/tina4`, currently **3.8.77**. CLI and
frameworks version independently — `tina4 update` for the CLI,
`uv lock --upgrade-package tina4-python && uv sync` in `pypy/` for the Python framework.

## Running the Python suite

```bash
cd documentation-testing/pypy
uv run tina4 serve                # dev server with watcher/reload
uv run tina4 test                 # full suite (pytest wrapper — see PY-18-04)
uv run python -m pytest <path>    # one file (the pytest binary is not on PATH)
```

Watch `logs/tina4.log` for registration and execution errors.

**ORM-backed chapters need a database first.** Ch06, Ch07, Ch18 and anything else touching
the ORM raise `RuntimeError: No database bound` on the first ORM call otherwise.
`conftest.py` loads `.env` into `os.environ` before any test (the framework itself only
reads `.env` under `tina4 serve`, not under pytest), and the ORM reads `TINA4_DATABASE_URL`
lazily — so a running database plus a correct `.env` binds the whole suite.

Expected: `postgresql://postgres:tina4test@localhost:5432/tina4testingdb`, with an `items`
seed table; chapter tables are created by the tests at runtime.

> **The Docker fixture that provided this was deleted on 2026-08-19.** `docker-compose.yml`
> (a `postgres:18` service named `tina4_pg`) and `dev/postgres-init/init.sh` (which created
> and seeded the databases on first start) are both gone. Until something replaces them,
> Postgres has to be provided by hand on the same port and credentials — the tests do not
> care what is serving. Recover the originals with
> `git show HEAD:docker-compose.yml` and `git show HEAD:dev/postgres-init/init.sh`.

Probes that need a live database `skipif` when it is unreachable, so a machine without one
still runs the mocked probes cleanly rather than failing loudly.

Chapter 12's queue tests are broker-gated the same way — each socket-checks its port and
skips if RabbitMQ / MongoDB / Kafka is down. Brokers were run as plain `docker run`
containers, never in the compose file, so nothing was lost with it:

```bash
docker run -d --name tina4_rabbit -p 5672:5672   rabbitmq:3
docker run -d --name tina4_mongo  -p 27017:27017 mongo:7
docker run -d --name tina4_kafka  -p 9092:9092   apache/kafka:3.7.0
```

Only MongoDB hard-requires its driver (`pymongo`) at construction; Kafka and RabbitMQ have
raw-socket fallbacks. Kafka's first delivery lags ~16s on consumer-group join, so an
immediate `pop()` returns nothing (PY-12-02).

## Documentation source — `documentation/tina4-book/`

**Untracked and currently absent.** Every Protocol step 1 reads from here, so no chapter work
can start without it:

```bash
mkdir -p documentation && tina4 books                          # pull with the CLI
mkdir -p documentation && ln -s <path-to-clone> documentation/tina4-book   # or symlink a clone
```

The live site at <https://tina4.com> is the actual source of truth; this local copy is a
convenience. See *Source of Truth* in `documentation-testing/readme.md`.

## Fixing the framework

Testing and fixing are different jobs with different rules. A finished fix never lives here —
it lives in a clone of the real source, outside this repo:

```
gitdir/tina4-python/     clone of tina4stack/tina4-python
```

Pull it first — a fix written against a clone that is 20 commits behind is a fix for a problem
someone may already have solved. See *Working against the real repositories*.

The order matters more than the location:

1. **Reproduce against the untouched installed copy.** Nothing is edited yet. This is the
   step the read-only rule protects, and it is the one that can never be skipped — an
   unreproduced defect has nothing to fix.
2. **Try the candidate fix wherever it is fastest to try.** Editing the framework inside the
   workspace `.venv` is fine here. Poking at the installed copy to see whether an idea holds
   up is how you find out if it does, and forcing that through a clone first only slows the
   answer down.
3. **Move the fix that worked into the clone**, with a regression test that fails against
   unfixed source. The scratch patch was scaffolding; the clone is the artifact.
4. **Restore the workspace before testing anything else:**
   ```bash
   cd documentation-testing/pypy && uv sync --reinstall-package tina4-python
   ```
   Then re-verify from the clone via `PYTHONPATH` rather than site-packages, so the result
   is reproducible by someone who never saw your scratch patch.

Step 4 is what separates this from the failure mode the read-only rule exists to stop.
A patched `.venv` left in place turns every later run in that workspace into a lie, and the
test output looks identical either way. **A scratch patch that outlives the question it
answered is the banned thing.** If you cannot say which files you touched, reinstall rather
than guess.

Two hard limits, whatever the workflow:

- **Never patch to make a chapter proceed.** Only to test a fix for a defect already
  reproduced in step 1. "The test passes once I patch this" is a finding, not a fix.
- **Never report a result measured against a patched workspace.** Ledger rows,
  fix-verifications and audit entries cite the clean run or the `PYTHONPATH` run.

The `PYTHONPATH` route stays the better default when the fix is already written — it alters
nothing, so it needs no cleanup and cannot be forgotten.

As of 2026-08-19 that clone holds four fix branches, each with regression tests that
fail against unfixed source — covering `PY-FW-01` (`@cached` never cached), `PY-FW-02`
(`ServiceRunner.register` accepted a handler it could not call), `PY-FW-03` (`@websocket`
shadowed by the subpackage) and the `tina4 ai` context-installer cluster
(`CLI-FW-05/07/08/10/12`). `PY-FW-03` is the only one filed: PR
[#116](https://github.com/tina4stack/tina4-python/pull/116) from fork `MichaelC8E/tina4-python`
(`fix/websocket-decorator-shadowed`). The other three stay local. Origin is `tina4stack`;
the fork remote is `fork` (`git@github-work:MichaelC8E/tina4-python.git`).

## Working against the real repositories

The framework, the book and the site all live outside this repo. Testing or fixing against a
stale copy of any of them produces findings about a version nobody is running.

```
gitdir/tina4-python/          origin = tina4stack; fork = MichaelC8E
gitdir/tina4-book/            fork of tina4stack/tina4-book      (fork = MichaelC8E)
gitdir/tina4-documentation/   fork of tina4stack/tina4-documentation
gitdir/tina4-js/              clone of tina4stack/tina4-js
```

**Start every session by pulling.** Not the one repo you expect to touch — all of them, because
a doc claim gets checked against framework source and a framework fix gets checked against the
doc that describes it.

```bash
for r in tina4-python tina4-book tina4-documentation tina4-js; do
  git -C ../$r fetch --all --prune
done
```

**A fork is only useful once it is level with the official repo.** Both doc repos are forks, and
a fork's `main` drifts behind silently — there is no warning, the files just quietly describe an
older release. Check the distance before trusting anything in one:

```bash
git -C ../tina4-book rev-list --left-right --count fork/main...upstream/main
#                                                  ^ours-only  ^upstream-only
```

If the fork has 0 commits of its own, syncing is a fast-forward and loses nothing. Bring it
level *before* branching, and branch new work off `upstream/main` rather than off whatever the
fork's `main` happens to be.

> Both doc forks were missing an `upstream` remote entirely on 2026-08-19 — only `fork` was
> configured, so the drift (19 and 73 commits) was invisible. `upstream` was added to both. If a
> clone has no remote pointing at tina4stack, add one first; you cannot measure drift you cannot
> see.

Two identities, and they must not cross: this repo uses **`M1gael`** on plain `github.com`;
every `tina4stack` repo is cloned over the **`github-work`** SSH alias (`MichaelC8E`).

## Git

- Remote `git@github.com:M1gael/testing-tina4.git`, default branch `main`. This repo uses the
  **`M1gael`** identity on plain `github.com`; upstream `tina4stack` repos are cloned over the
  `github-work` SSH alias (`MichaelC8E`). Don't cross the two.
- **`main` is the only branch.** An earlier revision described a `bug-hunting` scratch branch;
  it never existed and the directory it referred to is gone.
- Probes carry a `# Probe — covers <ID>` header line naming the ledger row they cover.
- Before any user-requested `/commit`, follow the *Issue Report Format* in
  `documentation-testing/readme.md` for any finding the commit introduces.

## Removed 2026-08-19

Cleared in a consolidation pass. Everything issue-shaped was migrated into
`known-issues/ledger.md` first — as self-contained rows carrying their own root cause,
reproduction and suggested fix, so none of them depend on these directories. Recover any of
it from git history.

| Removed | What it held | Where it went |
|---|---|---|
| `bug-hunting/` | Long-form `BH-<n>` evidence, plus `debug-false/` and `serve-port/` | Findings → ledger `PY-FW-09`…`PY-FW-15`, `SITE-DOC-02/03`, `CLI-DOC-01`. `BH-46`…`BH-52` rows already stood alone. |
| `agent-testing/` | Can AI tools build with Tina4— three arms, plus `unverified-leads.md` | Leads discarded by decision (unverified, no doc trace). The per-tool delivery scorecard was folded into ledger `CLI-FW-06`. |
| `codex/` | The Codex context-delivery fixture and mechanism study | `CODX-01`…`07` were already re-coded into the ledger as `CLI-FW-05`…`11` on 2026-08-13. |
| `comparison-testing/` | Tina4 vs Flask/FastAPI/Django, feature-matched | Nothing to migrate — the run recorded *"Capability gaps: None"*; the rest is measurement, not defects. |
| `dev/`, `docker-compose.yml` | The Postgres fixture | See *Running the Python suite* — no replacement yet. |
| `documentation/` | The book under test | Untracked anyway; recreate with `tina4 books`. |
| `.prompts/`, `.skills/`, `tutorial/`, `routine-bugcheck/` | Old guides, course notes, an empty directory | Nothing. |
