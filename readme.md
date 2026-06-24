# Tina4 Framework Evaluation

A documentation-fidelity QA harness for the **Tina4** web framework. The official docs are
implemented verbatim across multiple languages, run, and every place the framework's actual
behavior deviates from what the docs say is logged.

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
    documented example *exactly as written* in the correct language workspace (`pypy/`,
    `phph/`, `ruru/`). Use **only what the chapter literally shows** — not framework source,
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
| `pypy/` | Python | `tina4 init python .` |
| `phph/` | PHP | `tina4 init php .` |
| `ruru/` | Ruby | `tina4 init ruby .` |

Every workspace follows the same layout: `src/{routes,orm,templates}/`, `migrations/`,
`seeds/`, plus a `tests/` directory for chapter test files. Always bootstrap via the
`tina4` CLI — never hand-create the structure.

**Test filename prefix is non-negotiable.** `tina4 test` is a thin pytest wrapper
(see [PY-18-04](findings-log.md#known-issues-log)) and inherits pytest's default discovery rules:
files must be named `test_*.py` or `*_test.py` to be collected. A file named
`ch18_basic.py` is silently skipped (`collected 0 items`, no warning). Combine the
required prefix with the chapter-prefix convention: `tests/test_ch18_basic.py`,
`tests/test_ch10_middleware.py`, etc.

## Standard Implementation Workflow

1.  **Isolation** — all implementation occurs inside the current language's workspace.
2.  **Naming** — files are chapter-prefixed and zero-padded:
    `src/routes/ch01_routing.py`, `src/orm/ch06_author.rb`, etc. One file per documented
    feature/section.
3.  **In-file context** — start each file with a lowercase, space-prefixed comment describing
    the test case.
4.  **Verification** — run the project via `tina4 serve`. Exercise routes via CLI/browser.
    Watch `logs/tina4.log` (or equivalent) for registration and execution errors.
5.  **Reporting** — when behavior diverges from docs, capture it in the Known Issues Log
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
    installed), or `⏸ deferred` (USER-deferred, with a pointer). The ledgers live in
    **`coverage-ledger/`**, one markdown per chapter — `coverage-ledger/<lang>-ch<NN>-<topic>.md`
    (e.g. `py-ch12-queues.md`). The Evaluation Progress table in `findings-log.md` carries only a
    one-line status + a link to the ledger, and that status must name the open dimensions
    explicitly — e.g. "file-backend complete; rabbitmq/kafka/mongo open", never just "complete".
    **Every sign-off is version-stamped:** each section records the date and the tina4 versions it
    was verified on — `tina4-python <framework> · CLI <cli>` — so it is always clear *when* and
    against *which* versions a section was exercised. Re-stamp (don't overwrite) when a section is
    re-run on a newer version. This closes the gap where coverage is asserted from memory and an
    option or a hard-to-test snippet silently slips. (Operationalises rule 9 + *Coverage bar* —
    turns the principle into a checklist that can't be skipped.)

## Patching Convention

**Patching is user-triggered, not automatic.** Default behaviour is verbatim implementation
(per Protocol rules 3, 4, and 5 — implement as documented, no proactive fixes, verbatim
first then diagnose). When the user explicitly asks to patch — typically because a
broken snippet must run so evaluation can continue into subsequent sections — the
following convention applies.

The convention exists so that patches can be reverted later to verify the original docs
bugs are still present in future framework versions.

**Rules (apply only when the USER has asked to patch):**

1.  **Every patch references an existing finding ID** in the Known Issues Log. If no
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
discrepancies then graduate to the Known Issues Log for durable tracking.

**2. Known Issues Log row — the durable record.** When you find a discrepancy, append a row
to the Known Issues Log (in [`findings-log.md`](findings-log.md)) using this six-column format:

```
| <ID> | <Status> | <Filed> | <Found> | <Suggested fix> | <Note> |
```

The first four columns are **always populated**. Note carries as much (or as little)
context as the issue needs; Suggested fix may be `—`.

- **ID** — `<LANG>-<CH>-<NN>` where LANG = `PY` | `PH` | `RB` | `CLI`, CH = zero-padded
  chapter, NN = sequence within that chapter (e.g. `PY-03-02`). The ID encodes language and
  chapter, so there are **no separate Lang/Chapter columns**. Assigned bug-hunt investigations
  use `BH-<n>` instead, where `<n>` is the upstream `tina4-python` issue number — same table,
  same schema, just a different ID prefix.
- **Status** — `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.
- **Filed** — the upstream GitHub issue/PR link, or `no` if not yet filed. **Filing
  destination depends on the ID type:** doc-fidelity findings (`PY-`/`PH-`/`RB-`) are filed
  against the book repo **[`tina4stack/tina4-book`](https://github.com/tina4stack/tina4-book/issues)**
  (e.g. [#142](https://github.com/tina4stack/tina4-book/issues/142)); bug-hunt
  investigations (`BH-<n>`) are filed against the framework repo
  **[`tina4stack/tina4-python`](https://github.com/tina4stack/tina4-python/issues)** — the
  issue number *is* the `<n>`. **Chapter-evaluation findings all live on the chapter's
  `tina4-book` thread — a `PY-`/`PH-`/`RB-` finding that turns out to be a *framework*
  defect (not just a doc gap) still files there, not on `tina4-python`. `BH-<n>` is
  reserved for standalone framework bug-hunts opened directly against `tina4-python`.**
  The USER files (see *Local-first, upstream-at-EOD* in the
  Convention Recap); the assistant only records the link here once it's filed.
- **Found** — `<YYYY-MM-DD>` the issue was logged · the framework version it was found on
  (e.g. `2026-06-17 · 3.13.30`). Version may be omitted only for pre-convention rows where it
  wasn't recorded. A logged issue's *fix* is tracked by its probe/test, not by re-verifying on
  every version bump.
- **Suggested fix** — a short inline fix, a `→ FIX-NN` pointer to a long-form write-up in the
  Suggested Fixes section, or `—`.
- **Note** — the detail, as deep as the issue needs (or nothing): docs-say vs. actual, how/whether
  it was tested, how certain the cause is, the smallest repro hint (file/line, function, exact
  error), and the probe/test filename(s) if any.
- **Sub-letter notation** (e.g. `PY-18-08b`, `PY-18-07a`) refers to *bullets within* a single
  finding row — informal pointers used in PATCH comments and upstream filing titles to
  isolate one of several symptoms grouped under one ID. Sub-letters are **not** separate
  rows in this table. Search by the parent ID (`PY-18-08`) to find the row.

Bug-hunt rows (`BH-<n>`) live in the **same** Known Issues Log under this schema — not a
separate table. For them, **Filed** is the `tina4-python` issue link (the BH-ID's own number)
and **Note** opens with what's being investigated. See `findings-log.md` → *Bug Hunt* for the
PY-vs-BH distinction.

**Terminal-output snippet format.** When the finding is about code that doesn't run, add
a subsection under the `### Observed terminal output` heading (h3, nested inside
`## Known Issues Log`) using the canonical neutral format below — same format used in
the upstream filing body template further down, only the heading level changes:

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
Known Issues Log without manual cross-linking.

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
Suggested Fixes section of [`findings-log.md`](findings-log.md), not in the upstream filing.

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
| **Discrepancy Report** | Test-run output per failing test: `Documented Claim (quote+path)` / `Expected` / `Actual`. Report only, then stop — no fixes. Confirmed ones graduate to the KI Log. See [Issue Report Format](#issue-report-format). |
| **Certainty first (verdict > cause)** | The deliverable is an ironclad **works / doesn't-work** verdict — deterministic, reproduced, sentineled (flips when behavior changes). Rule out TEST artifacts on **both** sides (works-by-luck / in-isolation-only isn't *works*; a self-inflicted test bug isn't *broken*). Root cause / `Origin` is an optional bonus that never gates or delays the verdict; if the cause is unknown, still log the certain verdict. |
| *— Coverage & live mocks —* | |
| **Coverage ledger** | A section is never tagged a bare "complete". Before marking it done, enumerate **every snippet + every named option** and mark each `✓ tested` (test/probe/demo name) · `⛔ blocked` (reason) · `⏸ deferred` (pointer). Ledgers live in **`coverage-ledger/`**, one markdown per chapter (`<lang>-ch<NN>-<topic>.md`); the progress table carries only a one-line status + link. **Every sign-off is version-stamped** (`tina4-python <v> · CLI <v>` + date). See [Workflow](#standard-implementation-workflow) step 7. |
| **Exhaustive option coverage** | Docs name options a/b/c (engines, queue backends, cache/session stores, auth modes, …) → exercise **all** of them end-to-end, not just one. "Selectable" ≠ "works" — drive a real round-trip, standing up the broker/engine if needed. Can't stand one up → **logged blocker**, never a silent skip or a "covered". See [Protocol](#protocol-chapter-based-evaluation) rule 9. |
| **Live per-section mock** | Each implemented section also ships a browser-navigable mock under `tina4 serve`, built from that section's docs, so the USER tests it by hand. One chapter page, a block per section, verbatim snippet + live result. A section isn't done until its mock is reachable. Ref: `src/routes/chapter_explorer.py` → `/chapters` (index) + `/chapter/{num}`; registry-driven, one `build(demo)` fn per chapter (`/queue` → ch12). See [Workflow](#standard-implementation-workflow) step 6. |
| *— Finding scope & evidence —* | |
| **One code block = one finding ID** | Each distinct code block in a chapter that has issues gets its own row in the Known Issues Log. Don't lump issues from two separate code blocks under one ID, even if they're in the same section. Use sub-letters (`PY-18-07a`, `PY-18-07b`) for splitting upstream filings within a single finding — see [Issue Report Format](#issue-report-format). |
| **Probe pattern as evidence + regression sentinel** | Write a `tests/test_chNN_<topic>_probe.py` for every finding whose framework characteristic is testable in code. "Where possible" carves out narrative / structural findings (not expressible as an assertion). **Assert the CORRECT framework state, not the buggy state.** A probe *tries to trigger the bug*; if it succeeds in triggering it, the probe outcome must read as a FAIL (the functionality goal is unmet). So the probe FAILS before the fix (bug visible) and PASSES after (fix confirmed) without any edit. After the fix lands the probe stays live in the active suite — a steady-state PASS that flips to FAIL the moment the framework regresses. Existing patterns: trace-list inspection via direct dispatcher invocation (`pypy/tests/test_ch10_middleware_probe.py` for `PY-10-01/02/03`), positive contract assertions on framework objects (`pypy/tests/test_ch18_response_object_probe.py` for `PY-18-10`). One assertion = one observation; reference the probe filename from the KI Log row. File header records finding history + fix version, and the **first line is always a one-line tag stating what the probe covers** — `# Probe — covers <ID(s)>. <one-line purpose>.` — so doc-fidelity probes (`PY-NN-NN`) and bug-hunt probes (`BH-NN`, named `test_issue_<n>_*.py`) are distinguishable at a glance while living together in `tests/`. |
| **Adversarial verification before filing** | Before any finding is filed upstream, actively try to disprove the claim across multiple angles — check for alternative code paths, hidden helpers, version-specific behaviour, framework's own internal docs, and inconsistent chapter usage that might excuse the symptom. Only file if every disproof attempt fails. The verification trail (what was tried, what was confirmed) goes into the upstream comment as part of the evidence. |
| *— Filing cadence & labels —* | |
| **Local-first, upstream-at-EOD** | Findings are logged locally throughout the day (Known Issues Log row + detailed evidence section). The USER batches the upstream filings at end of day. The assistant does not push to file mid-session. |
| **Report opening line** | Every report opens with a plain `<ID> — <short title>` line — no brackets, no `##` heading, no bold, no decorations. The ID leads so it stays greppable upstream. The legacy `[<id>]`-bracket style is preserved on filed threads only. See [Issue Report Format](#issue-report-format). |
| **Section notation: `S<n>` not `§<n>`** | When referring to chapter sections inline, use plain `S3`, `S12` (capital S + number). Never the `§` symbol. The spelled-out word *"Section"* is fine when starting a sentence or in a title that names a section. Applies to local logs, detailed evidence, and upstream filings. |
| *— Test files —* | |
| **Newest stays verbatim, older patched** | Within a chapter, only the most-recently-created test file stays unpatched. When moving to the next file, the USER triggers the patch on the previous one (see [Patching Convention](#patching-convention)). |
| *— Voice & shape of upstream reports —* | |
| **Neutral voice** | No "we" / "I" / "us" in prose. Local logs, detailed evidence sections, and upstream filings all use clinical, actor-free phrasing: "the chapter shows", "the framework returned", "the snippet fails because…". See [Issue Report Format](#issue-report-format) for the canonical wording. |
| **Report shape — location / Issue / Origin** | After the `<ID> — title` line: a one-line doc location (`Ch<N> <Name>, S<n> "<Section>"` — no line numbers, no "book", no `.md`), an `Issue:` paragraph (docs-say vs. actual), and an `Origin:` paragraph **only for framework defects** (narrows the cause with source `file:line`). A plain doc gap stops after a one-line corrective action — no `Origin:`. Verbatim calls/SQL/error output each go in their own code block; prose explains, the block carries the literal text. No narration, clinical actor-free voice. The older three-section *Documentation shows / Actual output / Issues* template is legacy. See [Issue Report Format](#issue-report-format). |

