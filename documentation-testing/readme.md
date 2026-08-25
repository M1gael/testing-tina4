# Tina4 Framework Evaluation

A documentation-fidelity QA harness for the **Tina4** web framework. The official docs are
implemented verbatim across multiple languages, run, and every place the framework's actual
behavior deviates from what the docs say is logged.

**This is its own project.** It lives in `testing-tina4/` alongside other projects, but it is
not a sub-part of them and it does not share their files. The work is crawling the official
documentation chapter by chapter and section by section: implement what the page shows,
establish whether the things it cites exist and behave as described, and record what does not.
This file is the authority on how that is done — if anything anywhere disagrees with it,
including the root `readme.md`, this file wins.

**Not here:**

- **Fixing the framework** — any patch, branch, fork, pull request or upstream filing against
  `tina4-python` or any other framework repo. That is a different activity with different
  rules; see Protocol rule 10. Its workflow, history and backlog do not belong in this
  directory, and neither do notes about clones, remotes or releases.
- **A second issue list** — confirmed findings are logged *out* to `../known-issues/ledger.md`.
- **Another project's history or backlog** — `audit-log.md` and `outstanding-tasks.md` in this
  directory are **this project's**: chapter retests, version bumps, doc-testing work not yet
  done. Framework-fix verification and PR chasing are not this project's history, however much
  they look like an audit trail.

If a piece of work does not fit the description above, it does not get written here because
this was the nearest plausible file. It belongs to another project, or to none.

## Goal

This repo is an **independent QA audit** of the Tina4 framework against its own
documentation. The assistant acts as a **QA Auditor**: write and run a test suite that
strictly verifies the framework against the docs, then *report* — never *repair* — what
diverges. The framework is read-only; tests are never rigged to pass.

*   **Documentation Verification** — implement framework features *exactly* as written in the
    official documentation.
*   **Discrepancy Identification** — find and document any place where actual behavior diverges
    from the docs.
*   **Regression Testing** — re-run evaluations across framework versions to confirm fixes and
    catch regressions.

## Source of Truth

The **live documentation at <https://tina4.com>** is the authoritative source. A local copy of
the books lives in `documentation/tina4-book/` (refreshable with `tina4 books`), but it is used
**only as fallback** and only when the USER directly requests it.

## Protocol: Chapter-Based Evaluation

The assistant acts as an **independent QA Auditor**. The execution loop is: extract concrete,
testable claims from the documentation (inputs, outputs, side effects, error handling) → write
tests that verify those specific claims against the framework → run them → output a Discrepancy
Report. The framework is **read-only**, tests are **never rigged**, and every test **traces to a
quoted documented claim**. The ASSISTANT MUST follow these rules without exception:

1.  **Wait for Direction** — do NOT start any chapter until the USER explicitly names it
    (e.g., "Work on Python Chapter 3").
2.  **Strict Sequencing** — implement chapters only in the order requested. No skipping ahead.
3.  **Implementation Fidelity — documentation ONLY, nothing else** — implement the
    documented example *exactly as written* in the correct language workspace (`documentation-testing/pypy/`,
    `documentation-testing/phph/`, `documentation-testing/ruru/`). Use **only what the chapter literally shows** — not framework source,
    not the framework's dev guide / CLAUDE.md, not other chapters, not prior knowledge,
    not "the API the framework actually exposes." If the chapter shows a handler signature,
    an import, a method call, a config value — that is what gets written, character for
    character. The reader being simulated knows nothing beyond the page in front of them.
4.  **No Proactive Fixes — NO WORKAROUNDS** — do NOT patch framework bugs, "improve" the
    documented code, or reach for any adjustment the chapter doesn't show (a different
    method signature, a missing import, reading a value off a different object, an extra
    setup step, etc.). **If the documented code doesn't work, it DOESN'T WORK** — record
    the failure and stop. Making it work is not the job; verifying the docs as-is is. The
    *only* permitted deviation from verbatim is a **USER-triggered patch** (see Patching
    Convention) whose sole purpose is to unblock *other* sections held up by an
    already-logged bug — never to "complete" the section that revealed the bug.
5.  **Verbatim First, Log the Symptom — diagnose only on instruction** — the implementation
    pass always runs the chapter's code as written, even when a bug is already known or
    suspected. When output or code doesn't work as expected, **log the observed symptom**
    (the literal output / error) and move on — do NOT investigate root causes, read
    framework source, or build proof harnesses proactively. Deep cause investigation
    happens **only when the USER explicitly instructs it** (typically while reviewing
    logged issues). Discovery path doesn't matter; what matters is the finding is a real
    framework or documentation discrepancy, empirically observed, and logged plainly.
6.  **Strict Structural Testing** — all work happens inside the standard Tina4 project
    structure (`src/routes`, `src/orm`, `src/templates`, `migrations/`, `seeds/`).
    Throwaway scripts next to `app.py` are prohibited unless a feature genuinely cannot be
    tested any other way (e.g., CLI-internal logic).
7.  **Language-Specific Conversations** — one language per conversation. A Python session
    stays Python; it never drifts to Ruby or PHP.
8.  **Issue Reporting** — report each discrepancy in the plain-text block format below for
    the USER to track.
9.  **Exhaustive Option Coverage — exercise every named option** — when the documentation
    says a feature supports options a, b, c (multiple database engines, queue backends,
    session/cache stores, auth modes, field types, transports, etc.), **each one is
    actually used** — not just the default or one representative. "Selectable" /
    "constructible" never substitutes for "works": if the docs say a backend is supported,
    drive a real end-to-end round-trip through it (stand up the broker/engine/service if
    that's what it takes). A section is **covered** only when every option it names has
    been exercised for real. If an option genuinely cannot be stood up in this environment,
    that is a **logged blocker** with its own note — never a silent skip, and never counted
    as covered. (Sharpens *Coverage bar*: every snippet AND every named option.) Enforced by the
    **coverage ledger** (Workflow step 7): before a section is called done, enumerate every snippet
    and option and mark each `tested` / `blocked` / `deferred` — never tag a bare "complete".
10. **Read-Only Framework — never modify the framework source** — the framework under test
    (the installed `tina4_python` package, the `tina4` CLI, any vendored framework code) is
    **strictly off-limits to edits**. Do NOT patch, fix, monkey-patch, shim, or alter it, even
    on finding a severe bug. The only files the assistant writes are its OWN: tests, probes,
    fixtures, the live mocks, and these logs. Fixing *ours* (a harness / test / doc-impl
    mistake) is allowed; touching framework code is not, ever.
11. **Strict Traceability — every test cites the doc** — every test (and every live-mock demo)
    MUST carry, in a docstring or comment, the **exact quoted claim** it verifies plus the
    **documentation file path** it came from. No test exists without a documented claim behind
    it. Do NOT invent features or assert standard edge cases (None handling, empty input,
    concurrency, type coercion, …) unless the docs explicitly state that behavior — if the page
    doesn't claim it, there is nothing to verify. (The quote+path lives in the *test*; finding
    *reports* still use the human `Chapter N, S<num>` style — different audiences, no conflict.)
12. **No Test Rigging — a real divergence stays red** — when the framework behaves differently
    from a faithful test, the test MUST FAIL and stay failing; record it. Never weaken an
    assertion, wrap it in `try/except`, `xfail`/skip it, or otherwise "adjust" a test to go
    green over a genuine framework divergence. The *only* legitimate reason to change a test is
    to make it a **more faithful** reading of the doc (a mis-stated claim) — never to paper over
    the framework. (See rule 4 and *Verify fidelity, fix ours*: fix the test only when the
    test, not the framework, was wrong.)

## Workspaces

| Dir | Language | Bootstrap |
|-----|----------|-----------|
| `documentation-testing/pypy/` | Python | `tina4 init python .` |
| `documentation-testing/phph/` | PHP | `tina4 init php .` |
| `documentation-testing/ruru/` | Ruby | `tina4 init ruby .` |

`php-temp-test/` is a vendored tina4php scratch env — **not** a language workspace. Ignore it unless the USER names it.

Coverage ledgers live in **`coverage-ledger/`** (this directory). Confirmed issues live in **`../known-issues/ledger.md`**. Long-form `FIX-NN` proposals live in **`../known-issues/suggested-fixes.md`**. Chapter progress is **`coverage-ledger/README.md`**. Audit history is **`audit-log.md`**. The work backlog is **`outstanding-tasks.md`** (this directory).

Every workspace follows the same layout: `src/{routes,orm,templates}/`, `migrations/`,
`seeds/`, plus a `tests/` directory for chapter test files. Always bootstrap via the
`tina4` CLI — never hand-create the structure.

**Test filename prefix is non-negotiable.** `tina4 test` is a thin pytest wrapper
(see [PY-18-04](../known-issues/ledger.md)) and inherits pytest's default discovery rules:
files must be named `test_*.py` or `*_test.py` to be collected. A file named
`ch18_basic.py` is silently skipped (`collected 0 items`, no warning). Combine the
required prefix with the chapter-prefix convention: `tests/test_ch18_basic.py`,
`tests/test_ch10_middleware.py`, etc.

## Running a workspace

| Dir | Language | Framework in `.venv` | Entry | Package manager |
|---|---|---|---|---|
| `pypy/` | Python (primary) | tina4-python **3.13.105** | `app.py` | `uv` |
| `phph/` | PHP | *not bootstrapped* | (`index.php`) | composer |
| `ruru/` | Ruby | *not bootstrapped* | (`app.rb`) | bundler |

The `tina4` CLI (Rust binary) is at `/usr/local/bin/tina4`, currently **3.8.77**. The CLI and
the frameworks version independently — `tina4 update` for the CLI,
`uv lock --upgrade-package tina4-python && uv sync` in `pypy/` for the Python framework.

### The Python suite

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

## Standard Implementation Workflow

1.  **Isolation** — all implementation occurs inside the current language's workspace.
2.  **Naming** — files are chapter-prefixed and zero-padded:
    `src/routes/ch01_routing.py`, `src/orm/ch06_author.rb`, etc. One file per documented
    feature/section.
3.  **In-file context** — start each file with a lowercase, space-prefixed comment describing
    the test case.
4.  **Verification** — run the project via `tina4 serve`. Exercise routes via CLI/browser.
    Watch `logs/tina4.log` (or equivalent) for registration and execution errors.
5.  **Reporting** — when behavior diverges from docs, capture it in `known-issues/ledger.md`
    using the format below.
6.  **Live per-section mock** — alongside the verbatim tests, **every implemented section
    ships a navigable mock served under `tina4 serve`** that the USER can open in a browser
    and exercise by hand. The mock is built **only from what that section's docs teach** —
    it runs the section's actual documented code live (real endpoints where the section
    defines them; an interactive demo page where the section is library-level). One page
    per chapter, a block per section, each block showing the verbatim snippet and its live
    result so the USER physically sees whether the taught code works. Pattern reference:
    `src/routes/chapter_explorer.py` — a registry-driven engine serving `GET /chapters`
    (index) and `GET /chapter/{num}` (one chapter, a block per section); add a chapter with
    one `build(demo)` function + a `register(...)` call, no other file changes. (`GET /queue`
    still resolves to chapter 12 for back-compat.) This is a deliverable, not optional
    polish — a section isn't done until its mock is reachable.
7.  **Coverage ledger — enumerate before you claim "done"** — a section is NEVER tagged a bare
    "complete". Before marking it done, write a ledger that lists **every snippet** and **every
    named option** the section contains, each marked `✓ tested` (with the test/probe name or the
    live-mock demo), `⛔ blocked` (with the reason — e.g. broker not stood up, driver not
    installed), `⚠ diverges` (framework differs from the doc — cite the finding ID; its sentinel test is the coverage), `⏸ deferred` (USER-deferred, with a pointer), or `n/a` (nothing to test — concept-only prose). The ledgers live in
    **`coverage-ledger/`** (this directory), one markdown per chapter — `coverage-ledger/<lang>-ch<NN>-<topic>.md`
    (e.g. `py-ch12-queues.md`). **The Evaluation Progress table in `coverage-ledger/README.md` MUST carry ONLY a one-line status + a link
    to the ledger — NEVER per-section narrative (all coverage detail belongs in the ledger).** That status must name the open dimensions
    explicitly — e.g. "file-backend complete; rabbitmq/kafka/mongo open", never just "complete".
    **Every sign-off is version-stamped:** each section records the date and the tina4 versions it
    was verified on — `tina4-python <framework> · CLI <cli>` — so it is always clear *when* and
    against *which* versions a section was exercised. Re-stamp (don't overwrite) when a section is
    re-run on a newer version. This closes the gap where coverage is asserted from memory and an
    option or a hard-to-test snippet silently slips. (Operationalises rule 9 + *Coverage bar* —
    turns the principle into a checklist that can't be skipped.)

## Probes

For every finding whose framework characteristic is testable in code, write a probe
(`tests/test_chNN_<topic>_probe.py`; bug-hunt probes are named `test_issue_<n>_*.py`). Narrative /
structural findings that can't be expressed as an assertion are carved out ("where possible").

- **Assert the CORRECT framework state, not the buggy state.** A probe *tries to trigger the bug*;
  if it still triggers, the probe reads as a FAIL. So it FAILS before the fix (bug visible) and
  PASSES after (fix confirmed) with no edit, then stays live in the suite — a steady-state PASS
  that flips to FAIL the moment the framework regresses.
- **First line is always a one-line tag:** `# Probe — covers <ID(s)>. <one-line purpose>.` — so
  doc-fidelity probes (`PY-NN-NN`) and bug-hunt probes (`BH-NN` / `test_issue_<n>_*.py`) are
  distinguishable at a glance while living together in `tests/`. The header also records finding
  history + fix version.
- One assertion = one observation; reference the probe filename from the ledger row. Patterns:
  trace-list inspection via direct dispatcher invocation (`documentation-testing/pypy/tests/test_ch10_middleware_probe.py`
  → `PY-10-01/02/03`); positive contract assertions on framework objects
  (`documentation-testing/pypy/tests/test_ch18_response_object_probe.py` → `PY-18-10`).

## Patching Convention

**Patching is user-triggered, not automatic.** Default behaviour is verbatim implementation
(per Protocol rules 3, 4, and 5 — implement as documented, no proactive fixes, verbatim
first then diagnose). When the user explicitly asks to patch — typically because a
broken snippet must run so evaluation can continue into subsequent sections — the
following convention applies.

The convention exists so that patches can be reverted later to verify the original docs
bugs are still present in future framework versions.

**Rules (apply only when the USER has asked to patch):**

1.  **Every patch references an existing finding ID** in `known-issues/ledger.md`. If no
    finding exists yet, log it first (per Protocol rules 4 and 5 — no proactive fixes,
    verbatim first then diagnose).
2.  **Inline patch marker** — single-line changes use a `# PATCH [<finding-ID>]: ...`
    comment immediately above the patched line, and preserve the original line below it
    as a `# OLD: ...` comment so reversion is one-step:
    ```python
    # PATCH [PY-18-08b]: resp.status_code attribute doesn't exist; real attr is resp.status.
    # OLD: assert_equal(resp.status_code, 200, "Health check should return 200")
    assert_equal(resp.status, 200, "Health check should return 200")
    ```
3.  **Block patch marker** — multi-line setup (imports, env config, schema creation) goes
    in a clearly delimited block at the top of the file:
    ```python
    # ============================== PATCHES ==============================
    # PATCH [PY-18-07a]: chapter never imports Product.
    from src.orm.product import Product
    # PATCH [PY-18-07b]: chapter claims auto test DB, but none is bound by default.
    import os
    os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")
    Product.create_table()
    # ============================ END PATCHES ============================
    ```
4.  **Verbatim chapter code stays preserved** below the patches, untouched. The block
    marker makes it visually clear where "ours" ends and "theirs" begins.
5.  **Files that need no patches get a header comment** stating so explicitly:
    ```python
    # ch18 section 2 — "Your First Test"
    # VERBATIM from the chapter. No code patches required for this snippet to pass.
    ```

**Why this matters.** Protocol rule 5 ("Verbatim First, Then Diagnose") requires every
implementation pass to run the chapter's code as written, even when a bug is suspected.
But once a bug is documented, two things still need to be possible: (a) verifying that
the framework works *around* the bug so subsequent features can be tested, AND (b)
retaining the ability to confirm the bug is still present in future framework versions.
Without PATCH markers, a future re-test would either re-hit all known bugs (slow) or
assume the patched version represents reality (false). With them, the file is both
runnable and reversible.

### Newest file stays verbatim

Within a chapter, only the **most recently-created test file** stays verbatim/unpatched.
All older test files in that chapter get patched (or marked with the "VERBATIM — no
patches needed" header if the docs-as-written code happens to work).

**Sequence:** create file A (verbatim) → test → if it has issues, log findings → user
asks to move on → patch A → create file B (verbatim) → test → patch B when moving to C
→ and so on.

**Why:** when `tina4 test` runs, the only "interesting" failures in the output should be
from the file currently under evaluation. If every prior file still hits its
documented bugs on every run, the signal-to-noise ratio collapses and it's hard to spot
new issues in the newest snippet. Patching previous files isolates the current focus.

**The rule is user-triggered** — same as patching in general. The user decides when to
move on from one file to the next; the assistant doesn't pre-emptively patch.

## Issue Report Format

There are two outputs, used at different moments.

**1. Discrepancy Report — the test-run output.** After running a suite, summarise each
failing *faithful* test as a short block the USER can read at a glance:

```
- Documented Claim: "<exact quote>" (<doc file path>)
- Expected Behavior: <what the doc says should happen>
- Actual Behavior:   <what the framework actually did — literal output / error>
```

Report only; do **not** attempt fixes, and stop execution after the report. Confirmed
discrepancies then graduate to `known-issues/ledger.md` for durable tracking.

**2. Ledger row — the durable record.** When you find a discrepancy, append a row to
[`known-issues/ledger.md`](../known-issues/ledger.md). **The live column set is defined at the
top of that file and is the only authority** — it was restructured on 2026-08-24 and this
section is a summary, not a spec. Nine columns:

```
| <Code> | <Kind> | <Port status> | <Doc verified> | <Version> | <Date found> | <Fix> | <Note> | <Reproduce> |
```

- **Code** — `<kind>-<subsystem>-<NN>` lowercase, e.g. `f-orm-01`, `d-ws-01`. `f` framework,
  `d` documentation; subsystem from the closed vocabulary in `ledger.md`. Legacy `PY-NN-NN`,
  `BH-<n>` and `SCOPE-KIND-NN` codes are **frozen** wherever they are quoted upstream; renamed
  rows carry their old ID in the Note under **Record:**. Never renumber a filed row.
- **Kind** — `framework` or `documentation`. Redundant for new codes but load-bearing for the
  legacy ones, whose IDs encode no kind.
- **Port status** — one token per port in the order `py php rb nd js dlp cli`, written
  `port:state` with `#N` once filed. Lifecycle `affected → fixed → filed#N → merged#N`, plus
  `?` (never checked), `n/a` (no such surface) and `clear` (checked, absent). **This column is
  the row's status — there is no Status or Filed column**, because one defect across five
  languages is five branches and five pull requests, which a single cell cannot hold. Never
  turn a `?` into a `clear` without running the reproduction against that port.
- **Doc verified** — added 2026-08-25, **same shape as `Port status`**: one token per port,
  same order `py php rb nd js dlp cli`. Each language has its own page and they can disagree.
  States: `?` not checked, `n/a` no page to check, `ok` correct, `silent` no page covers it,
  `stale` now wrong, then `filed#N` / `merged#N` for the documentation PR. A port's token stays
  `?` until that port's `Port status` is settled. **Rows you write from this project are `n/a`
  across the board** — a documentation finding has nothing to verify itself against.
- **Version** — the version the behaviour was *actually observed on*. If you only re-read the
  source, say so; a found-version is not a reproduced-version.
- **Date found** — `<YYYY-MM-DD>`.
- **Fix** — a short inline fix, a `→ FIX-NN` pointer into
  [`suggested-fixes.md`](../known-issues/suggested-fixes.md), or `—`.
- **Note** — the detail: docs-say vs actual, how it was tested, how certain the cause is, the
  smallest repro hint (`file:line`, function, exact error), the proof project, and the
  cross-port check. **Record:** at the end carries the old ID, the scope gloss and the filing
  text folded in from the removed columns.
- **Reproduce** — the command or the sequence, not prose.

**Filing destination still depends on the finding type.** Doc-fidelity findings are filed
against the book repo
**[`tina4stack/tina4-book`](https://github.com/tina4stack/tina4-book/issues)**; framework
bug-hunts go to the language repo — and to *that port's* repo, so `rb:filed#39` is ruby's 39,
not python's. A chapter-evaluation finding that turns out to be a framework defect still files
on `tina4-book`. The USER files (see *Local-first, upstream-at-EOD* in the Convention Recap);
the assistant records the link in the port token once it is filed.

- **Sub-letter notation** (e.g. `PY-18-08b`, `PY-18-07a`) refers to *bullets within* a single
  finding row — informal pointers used in PATCH comments and upstream filing titles to
  isolate one of several symptoms grouped under one ID. Sub-letters are **not** separate
  rows in this table. Search by the parent ID (`PY-18-08`) to find the row.

Bug-hunt rows (`BH-<n>`) live in the **same** ledger under this schema — not a
separate table. For them, **Filed** is the `tina4-python` issue link (the BH-ID's own number)
and **Note** opens with what's being investigated. `PY-NN-NN` rows come from walking a chapter;
`BH-<n>` rows are assigned hunts against an upstream `tina4-python` issue. Both live in the same ledger.

**Terminal-output snippet format.** When the finding is about code that doesn't run, put the
shortest decisive output in the ledger **How to reproduce** or **Note** column. Keep it to the
shortest decisive line — the `bug-hunting/` directory that used to hold long dumps was removed
on 2026-08-19, so a row has to stand on its own. Canonical shape:

````
#### <ID> — <short title>

Documentation shows:

```<lang>
<verbatim chapter snippet>
```

Actual output:

```
<minimal error output — usually just the `E       ...` line>
```

Issues:
- one bullet per concrete observation
- factual, short
````

Keep snippets minimal — the chapter code + the framework's complaint, nothing else. Skip
pytest's headers, the full traceback, and any internal inspection. The stance is clinical:
this is what the docs literally show, this is what the framework literally returned.

**Legacy entries.** Some earlier evidence sections in this file (e.g. PY-18-04, PY-18-07,
PY-18-08) still use the older `We used this from the docs: / It didn't work and said:`
template. They predate this convention and are preserved as filed. All new entries use
the neutral form above.

**Upstream filing — title / opening line.** Every report opens with a plain
`<ID> — <short title>` line: the finding ID, an em-dash, a short descriptive title.
No square brackets, no `##` heading marks, no bold — no decorations. The ID still leads,
so maintainers can grep upstream by `PY-06-08` and trace it back to a row in the local
ledger without manual cross-linking.

```
PY-06-01 — Chapter 6 shows no database-binding step
PY-06-08 — BooleanField documented as INTEGER, native BOOLEAN on PostgreSQL
```

For a comment on an existing chapter thread, this line is the first line of the comment
body. For a brand-new issue, it goes in the title field. If several findings are filed
together, list the IDs: `PY-01-01, PY-01-03 — Getting Started — top section confused + cargo prereq missing`.

(The older `[PY-NN-NN]`-in-brackets + `##`-heading title style is legacy — preserved on
already-filed threads, not used for new reports.)

**Upstream filing — body template.** After the title line comes a one-line documentation
location, then an `Issue:` paragraph, then — for framework defects only — an `Origin:`
paragraph. Clinical, actor-free voice. No "we" / "I" / "us" — let the docs and error speak.

````
PY-06-08 — BooleanField documented as INTEGER, native BOOLEAN on PostgreSQL

Ch6 ORM. S2 "Defining a Model" Field Types table lists BooleanField as "INTEGER (0/1)"; S4 "CRUD Operations" SQL-first example passes an integer for the boolean column.

Issue: <docs-say vs. actual, in prose>. Verbatim calls, SQL, and error/log output go in their own code blocks:

```python
notes = Note.select("SELECT * FROM notes WHERE pinned = ? ORDER BY created_at DESC", [1], ...)
```

```text
operator does not exist: boolean = integer
```

For a documentation gap, close the Issue paragraph with a one-line corrective action and STOP.

Origin: <framework defects ONLY — a short paragraph narrowing the cause for the maintainer, with framework source file:line. Omit entirely for a plain documentation gap.>
````

Three rules govern the shape:

- **Doc references** — name the location as `Ch<N> <Chapter Name>, S<n> "<Section Name>"`.
  No line numbers, no "book", no `.md` filename (they shift and add noise). Framework source
  `file:line` *is* used — but only inside the `Origin:` paragraph; the no-line-numbers rule
  is about documentation references.
- **Match depth to finding type** — a plain documentation gap (framework behaves correctly,
  docs just omit/misstate) is short: location + `Issue:` + one-line corrective action, no
  `Origin:`. A genuine framework defect adds the `Origin:` paragraph narrowing where the cause
  lies in the source.
- **Code and logs in their own blocks** — verbatim calls, SQL, and error/log output go in
  fenced code blocks (inline backticks for short tokens). The prose explains; the block
  carries the verbatim text.

**No standalone "Suggested fix" sections for obvious logical issues** — e.g. if the symptom
is "missing import", do not write "add the import." (A documentation gap is the exception —
its one-line corrective action, e.g. "change `[1]` to `[True]`" or "qualify the field-types
row per engine", IS the finding and belongs at the close of the `Issue:` paragraph.)
Non-obvious structural recommendations (naming, restructuring, renames) live in the local
Suggested Fixes file [`suggested-fixes.md`](../known-issues/suggested-fixes.md), not in the upstream filing.

Consolidated findings in the local log may need to be **split into multiple smaller
filings** upstream. Each filing tackles one symptom so maintainers can react to them
individually. Open each split with its sub-lettered ID, e.g. `PY-18-07a — …`, `PY-18-07b — …`.

## Convention Recap

Quick-reference summary of the conventions established across this protocol. Each
links back to where it's fully described.

| Convention | One-line rule |
|---|---|
| *— QA auditor stance —* | |
| **Read-only framework** | Never edit framework source (`tina4_python`, the `tina4` CLI, vendored code) — not even to fix a severe bug. Only OUR files (tests, probes, fixtures, mocks, logs) get written. See [Protocol](#protocol-chapter-based-evaluation) rule 10. |
| **Strict traceability** | Every test/demo carries the **exact quoted claim + doc file path** it verifies, in a docstring/comment. No test without a documented claim; no speculative edge cases the docs don't state. See [Protocol](#protocol-chapter-based-evaluation) rule 11. |
| **No test rigging** | Framework diverges from a faithful test → the test FAILS and stays red; record it. Never weaken/`xfail`/skip/`try-except` to go green. Change a test only to read the doc *more* faithfully. See [Protocol](#protocol-chapter-based-evaluation) rule 12. |
| **Discrepancy Report** | Test-run output per failing test: `Documented Claim (quote+path)` / `Expected` / `Actual`. Report only, then stop — no fixes. Confirmed ones graduate to `known-issues/ledger.md`. See [Issue Report Format](#issue-report-format). |
| **Certainty first (verdict > cause)** | The deliverable is an ironclad **works / doesn't-work** verdict — deterministic, reproduced, sentineled (flips when behavior changes). Rule out TEST artifacts on **both** sides (works-by-luck / in-isolation-only isn't *works*; a self-inflicted test bug isn't *broken*). Root cause / `Origin` is an optional bonus that never gates or delays the verdict; if the cause is unknown, still log the certain verdict. |
| *— Coverage & live mocks —* | |
| **Coverage ledger** | Never a bare "complete": enumerate every snippet + named option, mark each `✓`/`⚠ diverges`/`⛔ blocked`/`⏸ deferred`/`n/a`, version-stamp each sign-off; one ledger per chapter in `coverage-ledger/` (this directory), progress table links to it. See [Workflow](#standard-implementation-workflow) step 7. |
| **Exhaustive option coverage** | Docs name options a/b/c (engines, queue backends, cache/session stores, auth modes, …) → exercise **all** of them end-to-end, not just one. "Selectable" ≠ "works" — drive a real round-trip, standing up the broker/engine if needed. Can't stand one up → **logged blocker**, never a silent skip or a "covered". See [Protocol](#protocol-chapter-based-evaluation) rule 9. |
| **Live per-section mock** | Each implemented section ships a browser-navigable mock under `tina4 serve` (verbatim snippet + live result), reachable before the section is "done". Ref `src/routes/chapter_explorer.py` → `/chapters` + `/chapter/{num}`. See [Workflow](#standard-implementation-workflow) step 6. |
| *— Finding scope & evidence —* | |
| **One code block = one finding ID** | Each distinct code block in a chapter that has issues gets its own row in `known-issues/ledger.md`. Don't lump issues from two separate code blocks under one ID, even if they're in the same section. Use sub-letters (`PY-18-07a`, `PY-18-07b`) for splitting upstream filings within a single finding — see [Issue Report Format](#issue-report-format). |
| **Probe pattern as evidence + regression sentinel** | For every code-testable finding, write a probe that asserts the CORRECT state (FAILs pre-fix, PASSes post-fix, stays live as a regression sentinel); first line `# Probe — covers <ID>. <purpose>.`. See [Probes](#probes). |
| **Adversarial verification before filing** | Before any finding is filed upstream, actively try to disprove the claim across multiple angles — check for alternative code paths, hidden helpers, version-specific behaviour, framework's own internal docs, and inconsistent chapter usage that might excuse the symptom. Only file if every disproof attempt fails. The verification trail (what was tried, what was confirmed) goes into the upstream comment as part of the evidence. |
| *— Filing cadence & labels —* | |
| **Local-first, upstream-at-EOD** | Findings are logged locally throughout the day (ledger row). The USER batches the upstream filings at end of day. The assistant does not push to file mid-session. |
| **Report opening line** | Every report opens with a plain `<ID> — <short title>` line — no brackets/heading/bold; the ID leads so it stays greppable. Legacy `[<id>]` on filed threads only. See [Issue Report Format](#issue-report-format). |
| **Section notation: `S<n>` not `§<n>`** | When referring to chapter sections inline, use plain `S3`, `S12` (capital S + number). Never the `§` symbol. The spelled-out word *"Section"* is fine when starting a sentence or in a title that names a section. Applies to local logs, detailed evidence, and upstream filings. |
| *— Test files —* | |
| **Newest stays verbatim, older patched** | Within a chapter, only the most-recently-created test file stays unpatched. When moving to the next file, the USER triggers the patch on the previous one (see [Patching Convention](#patching-convention)). |
| *— Voice & shape of upstream reports —* | |
| **Neutral voice** | No "we" / "I" / "us" in prose. Local logs and upstream filings all use clinical, actor-free phrasing: "the chapter shows", "the framework returned", "the snippet fails because…". See [Issue Report Format](#issue-report-format) for the canonical wording. |
| **Report shape — location / Issue / Origin** | After the `<ID> — title` line: a one-line doc location, an `Issue:` paragraph, and `Origin:` **only for framework defects**; a doc gap stops at a one-line corrective action. Code/SQL/errors in their own blocks; clinical no-"we" voice. Full spec + legacy-format note in [Issue Report Format](#issue-report-format). |

