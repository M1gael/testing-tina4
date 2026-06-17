# Tina4 Framework Evaluation

A documentation-fidelity QA harness for the **Tina4** web framework. The official docs are
implemented verbatim across multiple languages, run, and every place the framework's actual
behavior deviates from what the docs say is logged.

## Goal

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

The ASSISTANT MUST follow these rules without exception:

1.  **Wait for Direction** — do NOT start any chapter until the USER explicitly names it
    (e.g., "Work on Python Chapter 3").
2.  **Strict Sequencing** — implement chapters only in the order requested. No skipping ahead.
3.  **Implementation Fidelity** — implement the documented example *exactly as written* in the
    correct language workspace (`pypy/`, `phph/`, `ruru/`).
4.  **No Proactive Fixes** — do NOT patch framework bugs or "improve" the documented code.
    The goal is to verify the docs work as-is.
5.  **Verbatim First, Then Diagnose** — the implementation pass always runs the chapter's
    code as written, even when a bug is already known or suspected. Discover the symptom
    fresh first; cross-reference the Known Issues Log after. Findings can land via any
    route (the verbatim run, source-code reading, a coworker question, a passing
    observation) — discovery path doesn't matter, what matters is that the finding is
    genuinely a framework or documentation issue and is empirically confirmed.
6.  **Strict Structural Testing** — all work happens inside the standard Tina4 project
    structure (`src/routes`, `src/orm`, `src/templates`, `migrations/`, `seeds/`).
    Throwaway scripts next to `app.py` are prohibited unless a feature genuinely cannot be
    tested any other way (e.g., CLI-internal logic).
7.  **Language-Specific Conversations** — one language per conversation. A Python session
    stays Python; it never drifts to Ruby or PHP.
8.  **Issue Reporting** — report each discrepancy in the plain-text block format below for
    the USER to track.

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
(see [PY-18-04](#known-issues-log)) and inherits pytest's default discovery rules:
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

When you find a discrepancy, append a row to the Known Issues Log using this format:

```
| <ID> | <Lang> | <Chapter> | <Status> | <YYYY-MM-DD> | <Short description of the doc-vs-behavior gap.> |
```

- **ID** — `<LANG>-<CH>-<NN>` where LANG = `PY` | `PH` | `RB` | `CLI`, CH = zero-padded
  chapter, NN = sequence within that chapter (e.g. `PY-03-02`).
- **Status** — `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.
- **Description** — what the docs say vs. what actually happens. Include the smallest repro
  hint (file/line, function name, or exact error).
- **Sub-letter notation** (e.g. `PY-18-08b`, `PY-18-07a`) refers to *bullets within* a single
  finding row — informal pointers used in PATCH comments and upstream filing titles to
  isolate one of several symptoms grouped under one ID. Sub-letters are **not** separate
  rows in this table. Search by the parent ID (`PY-18-08`) to find the row.

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

**Upstream filing — title and label convention.** Every GitHub issue or comment filed
upstream is prefixed with the local finding ID in square brackets so the mapping between
the local log and the upstream thread is unambiguous:

```
[PY-18-04] Chapter 18 — documented "tina4 test" output format doesn't match actual output
[PY-18-02] Chapter 18 — "No external packages" wrong; pytest required but tina4 init doesn't install it
```

If multiple findings are filed together in one comment, list all IDs:
`[PY-01-01, PY-01-03] Getting Started — top section structurally confused + cargo prereq missing`.

Maintainers can grep upstream by the ID and trace it back to a row in the local Known
Issues Log without manual cross-linking. The bracket prefix is also short enough not to
bloat the title.

**Upstream filing — body template.** Same three-section neutral format as the
Terminal-output snippet above; only the heading level changes (h2 here because GitHub
comments don't have a separate title field, h4 in the local log because it nests under
`### Observed terminal output` which nests under `## Known Issues Log`). For **comments
on an existing issue**, the title becomes the `##` header on the first line of the
comment body. For **new issues**, the title goes in the title field and the body starts
directly with "Documentation shows:".

Use clinical, actor-free language. No "we" / "I" / "us" — let the docs and error speak.

````
## [<ID>] <short title>

**Documentation shows:**

```<lang>
<verbatim snippet from the chapter>
```

**Actual output:**

```
<minimal error output>
```

**Issues:**
- one bullet per concrete observation
- factual, short
````

**No "Suggested fix" sections for logical issues** — e.g. if the symptom is "missing
import", do not write "add the import." The fix is obvious to the maintainer and the
prose just bloats the issue. Suggested fixes are reserved for non-obvious structural
recommendations (naming, restructuring, renames) and live in the local Suggested Fixes
section of `readme.md`, not in the upstream filing.

Consolidated findings in the local log may need to be **split into multiple smaller
filings** upstream. Each filing tackles one symptom so maintainers can react to them
individually. Title each split with a sub-letter, e.g. `[PY-18-07a]`, `[PY-18-07b]`.

## Convention Recap

Quick-reference summary of the conventions established across this protocol. Each
links back to where it's fully described.

| Convention | One-line rule |
|---|---|
| *— Finding scope & evidence —* | |
| **One code block = one finding ID** | Each distinct code block in a chapter that has issues gets its own row in the Known Issues Log. Don't lump issues from two separate code blocks under one ID, even if they're in the same section. Use sub-letters (`PY-18-07a`, `PY-18-07b`) for splitting upstream filings within a single finding — see [Issue Report Format](#issue-report-format). |
| **Probe pattern as evidence + regression sentinel** | Write a `tests/test_chNN_<topic>_probe.py` for every finding whose framework characteristic is testable in code. "Where possible" carves out narrative / structural findings (not expressible as an assertion). **Assert the CORRECT framework state, not the buggy state.** The probe FAILS before the fix (bug visible) and PASSES after (fix confirmed) without any edit. After the fix lands the probe stays live in the active suite — a steady-state PASS that flips to FAIL the moment the framework regresses. Existing patterns: trace-list inspection via direct dispatcher invocation (`pypy/tests/test_ch10_middleware_probe.py` for `PY-10-01/02/03`), positive contract assertions on framework objects (`pypy/tests/test_ch18_response_object_probe.py` for `PY-18-10`). One assertion = one observation; reference the probe filename from the KI Log row. File header records finding history + fix version, and the **first line is always a one-line tag stating what the probe covers** — `# Probe — covers <ID(s)>. <one-line purpose>.` — so doc-fidelity probes (`PY-NN-NN`) and bug-hunt probes (`BH-NN`, named `test_issue_<n>_*.py`) are distinguishable at a glance while living together in `tests/`. |
| **Adversarial verification before filing** | Before any finding is filed upstream, actively try to disprove the claim across multiple angles — check for alternative code paths, hidden helpers, version-specific behaviour, framework's own internal docs, and inconsistent chapter usage that might excuse the symptom. Only file if every disproof attempt fails. The verification trail (what was tried, what was confirmed) goes into the upstream comment as part of the evidence. |
| *— Filing cadence & labels —* | |
| **Local-first, upstream-at-EOD** | Findings are logged locally throughout the day (Known Issues Log row + detailed evidence section). The USER batches the upstream filings at end of day. The assistant does not push to file mid-session. |
| **Upstream label** | Every upstream issue/comment title prefixed with `[<finding-id>]`, e.g. `[PY-10-01] Chapter 10 S3 — function-based middleware documented but not implemented`. |
| **Section notation: `S<n>` not `§<n>`** | When referring to chapter sections inline, use plain `S3`, `S12` (capital S + number). Never the `§` symbol. The spelled-out word *"Section"* is fine when starting a sentence or in a title that names a section. Applies to local logs, detailed evidence, and upstream filings. |
| *— Test files —* | |
| **Newest stays verbatim, older patched** | Within a chapter, only the most-recently-created test file stays unpatched. When moving to the next file, the USER triggers the patch on the previous one (see [Patching Convention](#patching-convention)). |
| *— Voice & shape of upstream reports —* | |
| **Neutral voice** | No "we" / "I" / "us" in prose. Local logs, detailed evidence sections, and upstream filings all use clinical, actor-free phrasing: "the chapter shows", "the framework returned", "the snippet fails because…". See [Issue Report Format](#issue-report-format) for the canonical wording. |
| **Tight reports — evidence over prose** | Upstream comments stick to three sections: **Documentation shows / Actual behaviour / Issues**. No fourth section. No narration around the evidence — the chapter snippet, source line, and observed output speak for themselves. Tables for repeated evidence (e.g. "6 broken lines"). Smallest source quote that shows the bug. "Issues" bullets are one observation each, factual, no extrapolation unless the consequence isn't obvious. |

## Evaluation Progress

Refreshed whenever a new test file is added or a finding ID is logged. Status values:
`in-progress` (some sections touched) | `complete` (all sections implemented) | `not-started`.

| Language | Chapter | Sections covered | Status | Findings |
| :--- | :--- | :--- | :--- | :--- |
| Python | 01 — Getting Started | (whole chapter, narrative) | in-progress | PY-01-01, PY-01-03, PY-01-05, PY-01-06, PY-01-07, PY-01-08 |
| Python | 10 — Middleware & Security | S3, S4, S9, S10, S12 (source + coworker incident — not yet implemented verbatim) | findings logged, impl pending | ✅ PY-10-01, ✅ PY-10-02, ✅ PY-10-03 (all fixed in 3.13.4) |
| Python | 18 — Testing | S2, S3, S4, S5, S6, S7, S8, S9, S10, S11/S12 (of 13) | in-progress | PY-18-01, PY-18-02, PY-18-03 (re-verified open across S8 + S9), ✅ PY-18-04, PY-18-07 (-07a fixed; -07b/-07c open), ✅ PY-18-08, ✅ PY-18-10, PY-18-11, PY-18-12, PY-18-13 (5 sub-symptoms a–e). S10 clean. S11/S12 user model exercise: 5/5 pass after 4 PATCH blocks. |
| Python | 06 — ORM | S2, S3, S4, S6 (of 15) | in-progress | PY-06-01 (no DB-binding callout), PY-06-02 (no create_table shown past S3), PY-06-03 (multi-language content in the Python book). S2–S4 CRUD 7/7; S6 has_many/belongs_to 2/2 — all pass once DB bound + tables created. |
| Python | 02–05, 07–09, 11–17, 19–38 | — | not-started | — |
| PHP | all | — | not-started (workspace not bootstrapped) | — |
| Ruby | all | — | not-started (workspace not bootstrapped) | — |

## Known Issues Log

All confirmed framework bugs and documentation discrepancies are tracked here.
Status values: `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.

**Upstream tracking:**
- [tina4stack/tina4-book#140](https://github.com/tina4stack/tina4-book/issues/140) — Testing chapter issues. Filings landed and fixed in **tina4-python 3.13.4 (2026-06-05)**: `[PY-18-04]`, `[PY-18-07a]`, `[PY-18-08]`, plus `[PY-18-10]` (bundled into the 18-08 release — the new S5 "Response Object" subsection now matches the real `TestResponse` class). Filed 2026-06-05: `[PY-18-03]`, `[PY-18-11]`, `[PY-18-12]`, plus feature suggestion for custom output formatter. Remaining open findings still queued: PY-18-01, PY-18-02, PY-18-07b, PY-18-07c.
- [tina4stack/tina4-book#141](https://github.com/tina4stack/tina4-book/issues/141) — Middleware chapter issues. All three filings landed and fixed in **tina4-python 3.13.4 (2026-06-05)**: `[PY-10-01]`, `[PY-10-02]`, `[PY-10-03]`. Cross-framework parity fixes shipped at the same time for tina4-php, tina4-ruby, tina4-nodejs.

**Verification of fixes.** Re-running the existing probes against 3.13.4 inverts the bug-direction assertions (regression sentinels per the probe convention). PY-10-01 also has a dedicated end-to-end probe (`Ch10FunctionMiddlewareEndToEndProbe` in `pypy/tests/test_ch10_middleware_probe.py`) driving the new `_invoke_handler_with_middleware` dispatcher — all three assertions pass, confirming function middleware now runs in Russian-doll continuation order and can short-circuit by omitting `await next_handler(...)`.

| ID | Language | Chapter | Status | Date Found | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PY-01-01 | Python | 01 | open | 2026-06-03 | **The Getting Started page's top section is structurally confused — three distinct concepts (external prerequisites, the Tina4 CLI, and the `tina4-python` framework package) are collapsed into a single "What You Need / Install" block.** Three concrete symptoms a reader hits: (a) **Inconsistent prereq treatment** — Python is only verified via `python3 --version`, but `uv` gets three platform-specific install snippets (macOS/Linux curl, Windows PowerShell, Cargo). Either both prereqs get install instructions or neither does. (b) **Tina4 CLI vs. `tina4-python` framework package not distinguished** — a reader can't tell whether "Tina4 CLI" is the framework or just a tool. The actual `tina4-python` PyPI package only surfaces buried in `uv` output during `tina4 init`. (c) **The Tina4 CLI is listed as prereq #3 in "What You Need" AND has its own "Installing the Tina4 CLI" section directly below** — framed as both an external prerequisite and as something you install in step 1, contradictory. Prereqs should be external deps only (Python, uv); the CLI belongs purely in the install section. Single structural fix in Suggested Fixes: see **FIX-01** — restructure the page into three top-level headings (Prerequisites / Install the Tina4 CLI / Create your first project) that mirror the actual dependency chain. |
| PY-01-03 | Python | 01 | open | 2026-06-03 | Getting Started page offers `cargo install tina4` as a CLI install option and describes the CLI as "Rust-based", but Cargo (Rust toolchain) is never listed as a prerequisite and there is no link to install it. A reader who picks the cargo path without Rust installed hits a wall with no doc support. Recommend either removing the cargo option (Homebrew/curl/PowerShell already cover all platforms) or moving it under an "Advanced / from source" section with a note about needing Rust ([rustup.rs](https://rustup.rs)). |
| PY-01-05 | Python | 01 | open | 2026-06-03 | (Light suggestion.) The CLI/framework version decoupling is not explained anywhere in the docs. The `tina4` CLI is installed globally and updated by re-running the installer; the `tina4-python` framework is per-project and updated via `uv add tina4-python@latest`. Users have to derive this from first principles. Nice-to-have: a short "Versioning & updates" subsection on the Getting Started page covering (1) which version is which, (2) how to update each, (3) that they evolve independently. |
| PY-01-06 | Python | 01 | open | 2026-06-03 | Docs only show the greenfield happy path (`tina4 init python my-app`) and never reveal the underlying package name or direct install commands. Consequences: (1) `uv` is listed as a hard prerequisite but the reader never types a `uv` command — the CLI invokes it invisibly. (2) The PyPI package name (`tina4-python`) does not match the framework's marketing name (`tina4`), and a Python dev's natural reflex `pip install tina4` fails with `No matching distribution found for tina4`. Import path is also `tina4_python`, not `tina4`. (3) A reader migrating an existing project, or troubleshooting, has no fallback path documented. Recommend a one-line note on the Getting Started page: *"On PyPI the package is `tina4-python` (imported as `tina4_python`). `tina4 init` adds it for you; if you're adding it to an existing project use `uv add tina4-python` (or `pip install tina4-python`)."* |
| PY-01-07 | Python | 01 | open | 2026-06-03 | `tina4 install <lang>` subcommand naming is ambiguous: it installs the *language runtime* (Python itself), but a reader's intuition reads "install python = install the Python edition of Tina4." The framework install actually happens during `tina4 init python .` (as a per-project `uv add tina4-python`). Recommend either renaming `tina4 install` → `tina4 install-runtime` / `tina4 setup-runtime` for clarity, or making the help text explicit: *"Install a missing LANGUAGE runtime (not Tina4 itself — `tina4 init` installs the framework per project)."* |
| PY-01-08 | Python | 01 | open | 2026-06-03 | `tina4 doctor` exposes a section titled **"Tina4 CLIs"** listing `tina4python`, `tina4php`, `tina4ruby`, `tina4nodejs`, `vite` and reporting them as "not found" with manual install commands (`pip install tina4-python` etc.). Three problems: (1) **The section title is wrong** — these are not CLIs in any meaningful sense, they are the framework packages themselves (`tina4-python` and friends). The CLI face each one exposes is plumbing the main `tina4` Rust CLI delegates to; users should never invoke `tina4python` directly. Better label: **"Language-Specific Frameworks"** — names what these actually are (the Tina4 framework, one per language) without exposing the plumbing CLI face. (2) **The "not found" warning is misleading** outside a project context — these packages are *expected* to be absent until `tina4 init` adds them to a project's `.venv`. (3) **The suggested install commands pollute global runtimes** when run outside a venv. Recommend: doctor should hide the section entirely outside a project, OR retitle it and add a note that the entries auto-install via `tina4 init`. The "four-names" confusion (`tina4`, `tina4-python`, `tina4python`, `tina4_python`) is largely caused by exposing this row as if it were a separate user-installable thing — it's not, it's the framework. |
| PY-18-01 | Python | 18 | open | 2026-06-03 | **Section 3 (Assertion Methods) misdocuments existing assertions and omits six others entirely.** (1) Signature inconsistency: documented signatures show `assert_true/false/none/not_none(actual, expected, message)` — 3 args — but every example call uses 2 args: `assert_true(True, "Should be true")`. Confirmed runtime signatures (via `inspect.signature`): `assert_true(actual, expected=<sentinel>, message='')`. The function accepts both 2-arg `(actual, message)` and 3-arg `(actual, expected, message)` calls via sentinel detection — but `expected` is **semantically meaningless** for single-value assertions. The 2-arg examples are the intended usage; the signature heading is misleading. Recommend deprecating the `expected` parameter and updating docs to the honest signature `assert_true(actual, message='')`. (2) `assert_raises` has an undocumented overload — runtime signature is `(callable_or_exception, exception_class=None, message='')`, suggesting it accepts either a callable OR an exception class as the first arg, but the docs show only the `(callable, exception_class, message)` form. (3) **The module exports six undocumented assertion functions.** Chapter Section 3 documents 7 (`assert_equal`, `assert_true`, `assert_false`, `assert_raises`, `assert_not_equal`, `assert_none`, `assert_not_none`). Actual exports from `tina4_python.test`: those 7 plus `assert_almost_equal`, `assert_greater`, `assert_less`, `assert_in`, `assert_not_in`, `assert_is_instance` — six common assertions that aren't mentioned anywhere in the chapter. Recommend extending Section 3 to cover all 13. |
| PY-18-02 | Python | 18 | open | 2026-06-03 | Section 1 claims: *"Tina4 includes an inline testing framework. **No external packages.** No configuration. Write a test. Run it. Done."* But `tina4 test` on a fresh `tina4 init python .` scaffold fails with `No module named pytest`. Pytest is a hard requirement — the CLI invokes it directly. The `pyproject.toml` scaffolded by `tina4 init` does declare `pytest>=9.0.3` in `[dependency-groups] dev`, but the dep is not actually installed into `.venv` during init, so the first `tina4 test` invocation breaks. Two bugs in one: (a) docs claim "no external packages" but pytest is required; (b) `tina4 init` declares pytest but doesn't install it. Workaround: `uv add --dev pytest` after init. |
| PY-18-03 | Python | 18 | open | 2026-06-03 | Section 8 documents CLI flags `--file`, `--method`, `--verbose`, and (Section 9) `--cov`/`--cov-report` — **none of these flags exist**. `tina4 test --help` shows zero options besides `--help`. Either the flags need to be implemented in the CLI, or the docs need to be reduced to "run all tests" with no flag examples. **Re-verified 2026-06-05 on CLI 3.8.28 + tina4-python 3.13.4 — still open.** `--verbose` and `--file` both raise `error: unexpected argument '--<flag>' found`. S9 re-verification 2026-06-05: `--cov=src` and `--cov-report=term`/`=html` reject with the same error; `uv run python -m pytest --cov=src --cov-report=term` works against the same suite (73 statements, 97% covered), so the underlying tool path is fine — the wrapper just drops the flags. |
| PY-18-04 | Python | 18 | fixed | 2026-06-03 | **Fixed in tina4-python 3.13.4 (2026-06-05) via doc update — chapter S1 now says *"Tina4 ships a `Test` class layered on top of pytest"* and every output example shows real pytest output.** Originally: **Tina4's "inline testing framework" is actually a thin pytest wrapper, and the chapter misrepresents it as standalone.** Three concrete symptoms a reader hits: (a) Section 1 frames it as *"an inline testing framework. No external packages. No configuration."* — but it's pytest underneath, requiring pytest to be installed (see PY-18-02) and inheriting all of pytest's discovery/config/output behavior. (b) Section 2's claim *"Every `.py` file in that directory is auto-discovered when you run `tina4 test`"* is false — pytest's default requires `test_*.py` or `*_test.py` prefix; a file named `ch18_basic.py` is silently skipped (`collected 0 items`, no warning). (c) Every output example in the chapter (Sections 1, 2, 4, 8 PASS examples, 8 FAIL example) shows a fictional Tina4-styled format (`Running tests...`, `BasicTest`, `[PASS] test_addition`, `N tests, N passed, 0 failed (Ns)`). Actual output is raw pytest (`================ test session starts ================`, dots, `N passed in Ns`). Recommend: rewrite Section 1 to acknowledge `tina4 test` is a pytest wrapper, state that pytest's discovery rules / config / output format apply, and reframe Tina4's value-add as the `Test` base class (with `self.get`/`self.post`/etc.) plus the `assert_*` helpers. Either replace every output example with real pytest output, or implement a custom output formatter to match what the docs show. |
| PY-18-07 | Python | 18 | open | 2026-06-03 | **PY-18-07a fixed in tina4-python 3.13.4 (2026-06-05) — `from src.orm.Product import Product` is now in S4 of the chapter (line 170 of refreshed `18-testing.md`). Sub-symptoms -07b (claimed auto test DB) and -07c (`Product.where` 2-tuple unpack without `with_count=True`) remain open.** Originally: **Section 4 (Testing ORM Models) is broken end-to-end as written.** A reader copy-pasting the snippet hits a cascade of failures: (1) `NameError: name 'Product' is not defined` — `Product` is used throughout but never imported; the chapter only imports `Test` and `assert_*` from `tina4_python.test`. (2) After adding `from src.orm.product import Product`, the next failure is `RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env` — but Section 4 explicitly promises *"By default, `tina4 test` uses a separate test database... created at `data/test.db` (SQLite) and is reset before each test run."* That default does not exist. `tina4 init` does not set `TINA4_DATABASE_URL`. The chapter frames the env var as optional ("If you want to use a different database for tests, set it in `.env`") but it's actually required. (3) Even with both fixed, the snippet relies on ORM APIs the section never documents: `Product.find(id)` returns model-or-None (contract not stated), `Product.where(sql, params)` returns the unusual tuple `(records, count)` (no explanation), `product.in_stock = True` assumes a boolean field type but Chapter 6 documents no `BooleanField`, and `save()`/`delete()` return semantics aren't specified anywhere. (4) Reset-between-runs claim is also unverified — even with a bound DB there's no evidence the framework wipes it. **Recommend: rewrite Section 4 to be self-contained.** Include the `Product` import, show the required `.env` line, define the Product model inline (or recap from Ch 6), and document each ORM method's contract. Or, alternatively, make the framework actually deliver the "auto test DB, just write a test" experience the section promises. |
| PY-18-08 | Python | 18 | fixed | 2026-06-03 | **Fixed in tina4-python 3.13.4 (2026-06-05) via doc update — all three sub-symptoms addressed across the chapter: positional body → `json=` keyword, `resp.status_code` → `resp.status` (~14 sites), and S5 "Response Object" reference rewritten to list `resp.status`, `resp.body` (bytes), `resp.text()`, `resp.json()`, lowercased headers.** Originally: **Section 5 (Testing Routes) documents a test client API that doesn't match what the framework actually exposes.** Three concrete mismatches a reader hits when copy-pasting the snippet: (a) **Body argument is keyword-only, docs show positional.** Docs example: `self.post("/api/products", {"name": "Widget", ...})`. Actual signature: `Test.post(self, path: str, *, json=None, body=None, headers=None)` — the body must be passed as `json=` or `body=`, never positionally. Result: every `self.post(path, dict)` call in the chapter raises `TypeError: Test.post() takes 2 positional arguments but 3 were given`. Same applies to `self.put()` and `self.patch()`. (b) **`TestResponse` has no `status_code` attribute.** Section 5's "Response Object" subsection explicitly lists `resp.status_code` as a property. Real attribute is `resp.status`. Every `assert_equal(resp.status_code, 200, ...)` from the docs raises `AttributeError: 'TestResponse' object has no attribute 'status_code'`. (c) **Two undocumented convenience attributes exist.** Real `TestResponse` exposes `resp.json` (parsed JSON body) and `resp.text` — the chapter never mentions them. Readers manually do `json.loads(resp.body)` when `resp.json` would be simpler. Recommend: rewrite Section 5 to match the real API — (1) show keyword form `self.post("/api/products", json={...})`, (2) replace every `resp.status_code` with `resp.status`, (3) document `resp.json` and `resp.text` alongside the other Response Object attributes. |
| PY-10-01 | Python | 10 | fixed | 2026-06-04 | **Fixed in tina4-python 3.13.4 (2026-06-05) — framework now ships `_invoke_handler_with_middleware` (`server.py:1238`) and `_is_function_middleware` (`server.py:1154`), forming a Russian-doll continuation chain. Verified end-to-end by `Ch10FunctionMiddlewareEndToEndProbe`: function middleware body runs before/after the handler, multi-layer chains nest in declaration order, and omitting `await next_handler(...)` short-circuits the chain.** Originally: **Function-based middleware is documented but not implemented.** Section 3 ("Writing Custom Middleware") states *"Tina4 Python supports two styles of middleware: function-based and class-based"* and shows the canonical signature `async def fn(request, response, next_handler): ... result = await next_handler(request, response); return result`. The chapter has 8+ examples using this pattern across S3, S4, S6, S7, S8, S10 (`log_middleware`, `require_json`, `maintenance_mode`, `require_api_key`, `inject_user_agent`, `add_security_headers`, `api_key_middleware`, `auth_middleware`). Empirically the framework dispatcher (`server.py:1154-1185`) only handles class-based middleware — it iterates `dir(instance)` looking for attributes starting with `before_` / `after_`. A function passed to `@middleware(fn)` is stored in `route["middleware"]` but its body never executes because `dir(fn)` returns no `before_*` attributes. `grep -rn next_handler tina4_python/` returns 0 hits across the entire framework. Recommend either implementing the documented function-based path or removing S3 "Function-Based Middleware" + all `next_handler` examples from the chapter. Source: framework read + coworker incident (a developer wrote a JWT auth middleware following S3 verbatim; the body never ran, the route was silently unauthenticated). |
| PY-10-02 | Python | 10 | fixed | 2026-06-04 | **Fixed in tina4-python 3.13.4 (2026-06-05) — `@middleware()` is now purely additive. POST/PUT/PATCH/DELETE routes stay Bearer-gated even with custom middleware attached; use `@noauth()` to open a write route explicitly. Verified by the existing probe assertion `test_decorated_post_route_silently_unauthenticated` flipping from PASS to FAIL (the bug-direction assertion is the regression sentinel).** Originally: **`@middleware(...)` silently disables the framework's built-in Bearer-token gate.** `router.py:689-704` — when `@middleware(...)` decorates a POST/PUT/PATCH/DELETE route, the decorator sets `route["auth_required"] = False` *"unless @secured() was explicitly set"*, on the assumption that "developer handles auth — disable built-in gate." This is undocumented in the chapter. Combined with PY-10-01, applying a function-based middleware intended to enforce auth produces a route with **zero authentication**: neither the custom middleware (never runs, per PY-10-01) nor the framework default (disabled by the decorator). A developer reading Ch10 alone would not know to add `@secured()` to restore the default gate. Recommend either documenting this behaviour explicitly in S4 ("The @middleware Decorator") with a security-implications callout, or making the auth-required default sticky unless explicitly overridden with `@noauth()`. |
| PY-10-03 | Python | 10 | fixed | 2026-06-04 | **Fixed in tina4-python 3.13.4 (2026-06-05) — `request.headers` is now a `CaseInsensitiveDict` (`request.py:18`). `headers.get("Content-Type")`, `headers.get("content-type")`, `headers.get("CONTENT-TYPE")` all return the same value. The 6 mixed-case chapter examples now work as written. Verified by the existing probe assertion `test_docs_pattern_capital_A_returns_None` flipping from PASS to FAIL (regression sentinel).** Originally: **Header-key casing mismatch in chapter examples.** `request.py:55` stores all incoming headers under lowercase keys: `req.headers[name.decode().lower()] = value.decode()`. So `request.headers.get("Authorization")` returns `None` — the key is actually `"authorization"`. Several chapter examples use mixed-case keys against this dict — S9 line 500 uses `"authorization"` (correct), S10 line 546 + S12 line 677 use `"X-API-Key"` (broken — returns None), S12 line 664 uses `"Authorization"` (broken — returns None). The chapter never states that `request.headers` is lowercase-keyed, nor mentions the convenience helpers: `request.header(name)` does case-insensitive lookup (`request.py:128`), and `request.bearer_token()` extracts the raw token (`request.py:132`). Recommend: (a) add a one-line callout in S3 or S8 that `request.headers` is lowercase-keyed, (b) normalise all chapter examples to either lowercase keys or the `request.header()` helper, (c) document `request.bearer_token()` as the canonical way to read the auth header. |
| PY-18-12 | Python | 18 | open | 2026-06-05 | **S7 (Setup and Teardown) example references `User` with no import and no model definition — same defect class as PY-18-07a in S4 before the 3.13.4 fix.** S7 snippet uses `User()`, `User.find(self.user_id)`, `user.save()`, `user.delete()` across `set_up`, `tear_down`, and both test methods. Chapter imports only `Test, assert_equal, assert_not_none` from `tina4_python.test`. No `User` ORM model defined in Ch18 or referenced from Ch06. Empirically: `NameError: name 'User' is not defined` on every test before any framework code runs. The 3.13.4 fix for PY-18-07a added `from src.orm.Product import Product` to S4; the parallel fix is missing for S7. Recommend: add `from src.orm.User import User   # assumes src/orm/User.py exists` to the snippet, mirroring the S4 fix. (Combined with the broader scaffold-gap pattern PY-18-11: a one-line callout that S7 assumes Ch06 ORM territory would also help.) |
| PY-18-11 | Python | 18 | open | 2026-06-05 | **S6 (Testing Authentication) assumes prior-chapter scaffold with no callout.** S6 test code references `/api/auth/login` POST + `/api/profile` GET, hardcoded credentials `admin@example.com` / `correct-password`, and expects a JWT in the response. None of these routes/users/credentials are shown in Ch18 or earlier sections of Ch18. A reader following the chapter top-down hits 6 consecutive 404s with no hint why. S5 has the same shape gap (`/api/products` not shown) but at least appears alongside S4's ORM model, which makes the link to Ch06 implicit. S6 has no equivalent anchor — the auth setup lives in Ch08 (not yet read by a sequential reader). Recommend: add a one-paragraph callout at the top of S6 stating "this section assumes Ch08 (Authentication) has been implemented and the `/api/auth/login` + `/api/profile` routes exist; minimal setup below," followed by a 10-line auth route + user fixture. Verified locally: building a minimal `src/routes/ch18_auth.py` using `Auth.get_token()` / `@secured()` flips all 6 S6 tests from 404 to PASS, confirming the framework is fine — only the chapter scaffolding is missing. |
| PY-18-13 | Python | 18 | open | 2026-06-08 | **S11 exercise + S12 solution (`tests/test_user_model.py`) broken in 5 independent ways before the first assertion runs.** (a) **PY-18-13a — missing `User` import.** S12 `test_user_model.py` uses `User()` throughout but imports only `Test, assert_equal, assert_true, assert_not_none, assert_raises`. `NameError: name 'User' is not defined` on every test. Same defect class as PY-18-07a (Product) and PY-18-12 (S7 User). Fix: add `from src.orm.User import User`. (b) **PY-18-13b — no DB binding or table creation.** S12 never calls `orm_bind()`, sets `TINA4_DATABASE_URL`, or runs DDL. `RuntimeError: No database bound` on first `user.save()`. Same defect class as PY-18-07b. Fix: `os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")` + `User.create_table()`. (c) **PY-18-13c — `StringField` has no `unique` kwarg; no uniqueness mechanism shown.** S11 requirement 2 + S12 `test_duplicate_email` expects an exception or error on duplicate email save. `Field.__init__` (fields.py:19-34) accepts no `unique` parameter — verified. The chapter shows no migration, no `save()` override, and no mechanism to enforce uniqueness. A UNIQUE INDEX must be created manually (e.g. `db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email)")`), but this is not in the chapter. (d) **PY-18-13d — `User.where("1=1")` unpacked as 2-tuple raises `ValueError`.** S12 line 808: `users, count = User.where("1=1")`. `Model.where()` returns `list[Self]` by default; `(list, int)` tuple requires `with_count=True` (model.py:624). As written: `ValueError: too many values to unpack (expected 2)`. Fix: `User.where("1=1", with_count=True)`. Same defect class as PY-18-07c. (e) **PY-18-13e — `assert_raises(create_duplicate, Exception, ...)` cannot fire; `ORM.save()` swallows all exceptions.** `ORM.save()` (model.py:336-338) wraps every insert/update in `except Exception: db.rollback(); return False`. A UNIQUE constraint violation is caught internally and returns `False` — it never propagates. S12's `assert_raises` test therefore always fails with `AssertionError: Should reject duplicate email` even when a UNIQUE INDEX is present. The framework's actual contract is "duplicate save returns `False`"; the test must assert `assert_false(user2.save(), ...)` not `assert_raises(...)`. Recommend: S11/S12 rewrite to (1) include `from src.orm.User import User` and DB-setup lines, (2) either add `unique=True` to `StringField` or show the migration/index step, (3) fix the `where()` call to use `with_count=True`, (4) fix `test_duplicate_email` to assert `save()` returns `False` rather than raises. Evidence: `pypy/tests/test_user_model.py` — 4 PATCH markers (PY-18-13a–e) required to reach 5/5 pass. |
| PY-06-01 | Python | 06 | open | 2026-06-17 | **Chapter 6 (ORM) shows no database-binding step anywhere — a reader exercising the chapter in isolation hits `RuntimeError: No database bound. Call bind_database(db) or set TINA4_DATABASE_URL in .env` on the first ORM call (`Note.create_table()`, S3).** Grep of `06-orm.md`: zero mentions of `TINA4_DATABASE_URL`, `Database(`, `.env`, `bind_database`, or `orm_bind`. Binding is established only in Ch05 (`05-database.md:20` sets `TINA4_DATABASE_URL=sqlite:///data/app.db`; L7 notes *"No ORM required (Chapter 6 adds that)"*). So Ch06 silently assumes the reader completed Ch05's `.env` setup — same scaffold-dependency-callout class as PY-18-11, not the false "auto test DB" promise of PY-18-07b. Once a DB is bound (verified via `os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")`), the full S2–S4 documented API works: model definition, `create_table()`, `save()`, `create()` (dict + kwargs), `find_by_id()`, `find()` filter dict, `where()`, `count()`, `delete()` — 7/7 pass (`pypy/tests/test_ch06_note_crud.py`). Recommend a one-line callout at the top of S2 or S3: *"This chapter assumes a database is configured per Chapter 5 (`TINA4_DATABASE_URL` in `.env`). The ORM auto-binds to it."* Evidence: `pypy/tests/test_ch06_note_crud.py` — 1 PATCH block (PY-06-01) to bind the DB. |
| PY-06-02 | Python | 06 | open | 2026-06-17 | **Chapter 6 shows `create_table()` only once (for `Note`, S3 line 255) — every later section then defines a model and immediately queries/saves it with no table-creation step.** The ORM requires the backing table to exist (named by `table_name` or the lowercased class name); `save()` does not auto-create it. Affected: S6 (`Author`/`BlogPost` relationships), S8 (`Task` soft delete), S12 (`Product` validation), and the S13/14 blog exercise + solution (`src/routes/blog.py` saves `Author`/`BlogPost`/`Comment` with no `create_table` or migration anywhere). Empirically: running S6 verbatim raises `UndefinedTable: relation "authors" does not exist` on the first `author.save()` (PG), `no such table: authors` (SQLite). Once the tables are created (`Author.create_table()` + `BlogPost.create_table()`), the documented relationship API works — `has_many`/`belongs_to` 2/2 pass (`pypy/tests/test_ch06_relationships.py`). Recommend: either a one-line note at S3 that `create_table()` (or a migration) must be run for every model before use, or a per-section "assuming the `<x>` table exists" callout, or fold the table-creation step into each section's example. Same defect family as PY-06-01 (chapter omits its own DB setup). Evidence: `pypy/tests/test_ch06_relationships.py` — 1 PATCH block (PY-06-02). |
| PY-06-03 | Python | 06 | open | 2026-06-17 | **The Python ORM chapter carries multi-language content that doesn't belong in the Python book.** The "ORM at a Glance: Four Languages, One Shape" section (`06-orm.md:13-98`) shows the same model in Python, PHP (native typed properties), Ruby (DSL), and Node.js (TypeScript config objects), plus a "Common Query Operations" comparison table (`06-orm.md:85-94`) with PHP/Ruby/Node columns and prose like *"PHP needs `(new Post())` for instance methods"* and *"Ruby methods drop the parentheses"*. A reader in the Python book gets ~85 lines of PHP/Ruby/Node code and cross-language caveats before the Python material proper (S2) begins. Recommend: strip the chapter to Python only — drop the PHP/Ruby/Node code blocks and the four-language table (or reduce it to the Python column). The cross-language parity story, if wanted, belongs in a shared/overview page, not inside each language's chapter. (Worth checking whether the same multi-language interludes appear in other Python chapters.) Documentation-only; no code to run. |
| PY-18-10 | Python | 18 | fixed | 2026-06-04 | **Fixed in tina4-python 3.13.4 (2026-06-05) via doc update — bundled into the PY-18-08 release. New S5 "Response Object" subsection (refreshed `18-testing.md:379-386`) correctly lists `resp.status`, `resp.body` (raw bytes), `resp.text()`, `resp.json()`, lowercased headers, `resp.content_type`. The framework itself is unchanged — the docs were brought into line with the real `TestResponse` class.** Originally: **Section 5 "Response Object" subsection (`18-testing.md:384-393`) reference table doesn't match `TestResponse`.** The code block lists four properties — `resp.status_code`, `resp.body` (string), `resp.headers`, `resp.content_type`. Empirically verified against `tina4_python.test_client.TestResponse` (`__slots__ = ("status", "body", "headers", "content_type")`) via probe in `pypy/tests/test_ch18_response_object_probe.py`: (a) `resp.status_code` does not exist — the real attribute is `resp.status`. Probe `test_doc_resp_status_code_attribute_exists` fails with `AttributeError`. (b) `resp.body` documented as "string" — actual type is `bytes`. Probe `test_doc_resp_body_is_a_string` fails; `test_real_resp_body_is_bytes` passes. Side-effect: chapter's `json.loads(resp.body)` calls work by luck (since Python 3.6 `json.loads` accepts bytes), but any user who does `resp.body.startswith(...)` or string-concatenates the body will hit `TypeError`. (c) Helper methods `resp.json()` and `resp.text()` exist on the class but are absent from the reference table. (Note: PY-18-08(b) and PY-18-08(c) overlap with parts of this finding — they were lumped under the test-client signature filing before the "one code block = one finding" convention was set. PY-18-10 is the canonical row for the Response Object code block; PY-18-08 keeps the test-client methods block.) |

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

Probe (`pypy/tests/test_ch18_response_object_probe.py`):

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

## Bug Hunt

Distinct from the Known Issues Log above. The KI Log records what the
documentation-fidelity protocol surfaces while walking chapters
sequentially. **Bug Hunt** is the log of bugs the user *assigned* —
typically a reproduction request against an existing GitHub issue on
the framework repo, where the work is "go investigate this, dig with
tests and theories until root cause is nailed down." The work
happens on the `bug-hunting` branch so `main` stays silver-lined;
this section is the index of what was investigated and what was
found.

**ID convention:** `BH-<n>` where `<n>` is the upstream GitHub issue
number on the framework repo (e.g. `BH-46` ↔
[`tina4stack/tina4-python#46`](https://github.com/tina4stack/tina4-python/issues/46)).
Direct numeric mapping — no chapter-prefix translation as with the
`PY-NN-NN` doc-fidelity IDs.

**Layout per finding:**
- One row in the table below — same column shape as the KI Log
  (`ID | Language | Issue # | Status | Date | Description`).
- A deep-dive analysis file under `bug-hunting/issue-<n>-<slug>.md`
  on the `bug-hunting` branch — root cause, source-line evidence,
  adversarial verification, recommended fix, and a draft upstream
  comment ready to paste.
- One or more probe files under `pypy/tests/test_issue_<n>_*.py` —
  bug-direction assertions PASS in the buggy steady state and FAIL
  once the upstream fix lands (regression sentinel, same pattern
  as the `PY-NN-NN` probes).

**Upstream tracking:** all Bug Hunt findings link to a real GitHub
issue on [`tina4stack/tina4-python`](https://github.com/tina4stack/tina4-python/issues).
The issue thread itself is the "official log" of the framework
defect; this section is the local evidence map pointing at it.

| ID | Language | Issue # | Status | Date | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| BH-49 | Python | [#49](https://github.com/tina4stack/tina4-python/issues/49) | open, **filed upstream 2026-06-10T13:31:43Z** (MichaelC8E) — follow-on to BH-46 covering 3 residual gaps on 3.13.8 | 2026-06-10 | **Three paths still surface BH-46 symptom (cascade hides original cause) on 3.13.8** — all inside-explicit-transaction or `fetch()`-asymmetry. (Gap 1) `fetch()` inside `db.start_transaction()` cascades — `_heal_aborted_txn()` (postgres.py:79) + `_on_query_error` auto-rollback (postgres.py:162) defer by design (postgres.py:127-130 *"user owns that transaction"*); (Gap 2) `execute()` inside explicit txn cascades AND `Database.execute()` (connection.py:412-414) silently catches and returns `False` — caller has no signal; second poisoned call's `db.last_error` overwrites original cause with cascade message; (Gap 3) `db.last_error` asymmetric — `Database.fetch()` (connection.py:438-439) doesn't capture, `Database.execute()` (connection.py:412-414) does. Adapter has data on `adapter.last_error` (postgres.py:154) either way. **Suggested fixes (in filed body):** Gaps 1+2 → `Log.warning` from `_on_query_error` even inside-txn (preserves SAVEPOINT/retry contract, closes visibility); Gap 3 → one-line capture in `Database.fetch()` mirroring `Database.execute()`. **Verification (in repo, not in filed body — stripped per user during draft review):** 13-test matrix probe `pypy/tests/test_issue_46_matrix_probe.py` covers `{fetch, execute} × {outside txn, inside txn} × {fresh, post-failure, pre-poisoned}`. 5 gap assertions written as positive-direction regression sentinels — flip to fail (XPASS) when maintainer extends fix. Evidence: `bug-hunting/issue-49-comment.md` (posted body), `bug-hunting/issue-46-pg-silent-abort.md` (full analysis + disproof matrix). |
| BH-46 | Python | [#46](https://github.com/tina4stack/tina4-python/issues/46) | **closed upstream 2026-06-09** by maintainer (v3.13.6 + v3.13.8 follow-on); **partial fix verified locally on 3.13.8 — 3 residual gaps filed as #49** | 2026-06-08 | **Original symptom for reporter's exact call shape: FIXED in 3.13.8.** `GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])` now raises the original `UndefinedFunction: operator does not exist: boolean = integer` with LINE/HINT pointer, and `Log.error` emits with full sql+params context. Cascade message no longer surfaces for the documented call path. Verified empirically against live PG 18 — exception type `psycopg2.errors.UndefinedFunction`, full ERROR log line carrying sql + params + LINE + HINT, no `"current transaction is aborted"` anywhere in the surfaced output. **Maintainer's fix shape differs from patches drafted at `bug-hunting/fix-issue-46-patches/`:** instead of SAVEPOINT around the count probe (the original suggestion mirroring lastval probe at `postgres.py:240-248`), maintainer used full `self._conn.rollback()` (postgres.py:288-292) outside explicit txn, routed `Log.error` via a new `_exec_with_handling` wrapper → `_on_query_error` (postgres.py:106-167) on the paginated query path. v3.13.8 added `_heal_aborted_txn()` pre-flight check (postgres.py:52-104) using `psycopg2 transaction_status == TRANSACTION_STATUS_INERROR` to recover connections that arrived poisoned from anywhere — broader coverage than the original suggestion. Both shapes solve the reporter's symptom; maintainer's is simpler at the count-probe site. **Residual gaps verified on 3.13.8 via 13-test matrix probe** (`pypy/tests/test_issue_46_matrix_probe.py`): (Gap 1) `fetch()` inside `db.start_transaction()` still cascades, original cause lost — heal step defers to explicit txns by design (postgres.py:79 + 127-130: *"Inside an explicit transaction we do NOT auto-rollback — the user owns that transaction"*); (Gap 2) `execute()` inside explicit txn cascades AND `Database.execute()` (connection.py:412-414) silently catches the exception and returns `False` — caller has no signal at all without polling `db.get_error()`, which on a second poisoned call returns the cascade message, not the original cause; (Gap 3) `db.last_error` asymmetry — `Database.fetch()` (connection.py:438-439) routes straight to `adapter.fetch()` with no `last_error` capture, while `Database.execute()` does capture. After `fetch()` failure, `db.get_error()` returns `None` even though `adapter.last_error` has the original cause — trivial one-line fix maintainer-side. **Empirical verification:** 22 BH-46 assertions pass on 3.13.8 across 3 files — `test_issue_46_pg_silent_abort_probe.py` (4 mocked, fix-direction code-path shape), `test_issue_46_live_repro.py` (5 live PG, reporter's call + log/last_error), `test_issue_46_matrix_probe.py` (13 live PG — 6 fix-direction + 5 residual-gap + 2 asymmetry, all positive-direction regression sentinels if maintainer extends fix to txn paths). **Adversarial disproof outcomes:** tried to break each fix claim — confirmed fix survives second valid call outside txn (heal works), survives different error types (`UndefinedFunction`, `DatatypeMismatch`, `UndefinedTable` all behave identically), confirmed `_heal_aborted_txn` fires correctly on raw-psycopg2-poisoned connections (WARNING log + ROLLBACK + cleared `transaction_status`), confirmed explicit-txn cascade reproduces on FRESH `Database()` instance with no prior pollution (gap is design choice, not stale state), confirmed `Database.execute()` swallow-and-return-False path makes silent-failure detection impossible inside txn without polling `last_error`. Two adjacent bugs still on backlog: (a) `SQLTranslator.boolean_to_int` (adapter.py:538-542) unconditionally rewrites `TRUE`/`FALSE` → `1`/`0` on PG, re-introducing the boolean/integer hazard — confirmed during matrix probe (valid `is_deleted IS FALSE` becomes invalid `is_deleted IS 0`); (b) framework's SAVEPOINT names (`_t4_lastval_probe` remains as fixed name in postgres.py:240-248) can collide with user-named savepoints — less urgent since maintainer chose ROLLBACK over SAVEPOINT for count probe. Evidence: `bug-hunting/issue-46-pg-silent-abort.md` (full post-fix analysis + disproof matrix + maintainer's actual fix shape + source-read of new wrappers), `bug-hunting/fix-issue-46-patches/` (3 original patches + README, kept for reference even though maintainer chose different shape), `pypy/tests/test_issue_46_*.py` (3 files, 22 assertions passing on 3.13.8). |
| BH-48 | Python | [#48](https://github.com/tina4stack/tina4-python/issues/48) | open, **pivoted 2026-06-10 after OP response** — initial "user typo" hypothesis broken; now investigating connection-target mismatch (pgAdmin on `staging` DB vs framework on `giftcard-service-dev` DB); awaiting OP env-confirmation reply | 2026-06-10 | **Reporter (same as #46/#47) hits `UndefinedTable: relation "gift_cards.gift_card" does not exist` against a table they claim exists.** Error log uses the new `_on_query_error` wrapper format from BH-46's v3.13.6 fix — pre-3.13.6 this error would have been hidden behind the cascade message. SQL emits `SELECT * FROM gift_cards.gift_card WHERE ...` — PG parses as schema-qualified (schema=`gift_cards`, table=`gift_card`). **Empirical reproduction (trial matrix against live PG 18, table `gift_cards` in `public` schema):** setting `table_name = "gift_cards.gift_card"` literally on a `GiftCard` ORM class produces byte-identical SQL + error to the reporter's log. Framework table-name resolution at `model.py:246-258` (`_get_table()`) returns `cls.table_name` verbatim with no transformation, no quoting, no schema-prefix injection. `where()` at `model.py:613-615` interpolates into `SELECT * FROM {table}` literally. **Thorough adversarial disproof attempts (11 angles tested):** (1) broader repo-wide grep across `tina4_python/` for f-string dot-concatenation between table-like names — 0 hits in framework code; (2) no schema env var exists (`TINA4_DB_SCHEMA`/`TINA4_SCHEMA`/`PGSCHEMA`); (3) `_translate_sql` empirically verified untouched table refs (all 3 transforms preserve `my_table` in `SELECT * FROM my_table`); (4) `ORMMeta` source-read — only collects fields/relationships/auto_crud, never modifies `table_name`; (5) `tina4 generate model` scaffold contains no `table_name` line at all; (6) default class-name resolution (`GiftCard` → `giftcard` via `.lower()`, or `giftcards` with `TINA4_ORM_PLURAL_TABLE_NAMES=true`) never generates dots; (7) 17 `_get_table()` call sites in `model.py` + 2 in `orm/fields.py` + 2 in `crud/` — all use same method, no alternative path; (8) PG `search_path` empirically confirmed NOT to help — created `CREATE SCHEMA gift_cards` + `SET search_path TO gift_cards, public`, query `SELECT * FROM gift_cards.gift_card` still fails (search_path only resolves unqualified names, dotted schema.table parsed literally); (9) `TINA4_DATABASE_URL` query string empirically confirmed IGNORED — connected with `?options=-csearch_path%3Dgift_cards`, resulting connection's search_path stays default `"$user", public` (urlparse extracts only host/port/user/password/dbname, query string dropped — separate gap); (10) PG error normalization confirmed — all three dotted forms (unquoted, double-quoted schema-qualified, single-quoted identifier with dot) produce byte-identical PG error text, but framework's logged `"sql": ...` payload preserves the SOURCE form, and reporter's log shows UNQUOTED → pins to `table_name = "gift_cards.gift_card"` (no quotes); (11) `soft_delete` default = `False` (verified empirically) and reporter's logged SQL has no parens or `OR is_deleted IS NULL` → their `is_deleted = 0` is explicit, not auto-injected. **Hypothesis stands.** **Disproof byproduct — BH-46 recalibration:** BH-46 and BH-48 are likely the SAME underlying user-side bug. The BH-46 cascade was hiding `UndefinedTable: relation "gift_cards.gift_card" does not exist`, NOT `operator does not exist: boolean = integer` as my BH-46 reproduction assumed. My BH-46 live_repro happened to work because I used `table_name = "gift_cards"` (sensible default) and built `CREATE TABLE gift_cards`, which triggers boolean=integer on reporter's WHERE clause. Reporter's actual trigger was missing-table — surfaced only after v3.13.6's cascade fix. **Doesn't invalidate BH-46 fix verification** — fix solves cascade for ANY trigger error, not specifically boolean=integer. **Not a framework bug strictly**, but issue surfaces 4 adjacent doc/UX gaps worth flagging: (a) Ch6 `table_name` paragraph (line 125) never mentions PG schema-qualified syntax / quoting / `search_path` interaction; (b) default class-name resolution is naive — `.lower()` only, no snake_case despite `camel_to_snake` utility existing at `model.py:67`. `GiftCard` → `giftcard`, not `gift_card`/`gift_cards`. Concrete UX consequence: scaffolding flow (`tina4 generate model GiftCard` + migration `CREATE TABLE gift_cards`) breaks because resolved name is `giftcard`; (c) `Log.error` output doesn't include model class name — could add `model=cls.__name__` at ORM call sites; (d) `TINA4_DATABASE_URL` query string ignored — users wanting non-public schema have to use `PGOPTIONS` env or manual `SET search_path` (undocumented). **Reply will:** acknowledge error visibility comes from BH-46 fix; walk reporter through empirical reproduction matrix; ask for `src/orm/GiftCard.py` to confirm `table_name` literal; flag the 4 adjacent gaps as separate concerns. Evidence: `bug-hunting/issue-48-undefined-table-relation.md` (full investigation + trial matrix + 11-angle disproof + BH-46 recalibration note + adjacent gaps + reply guidance). No probe — investigation-only at this stage. |
| BH-47 | Python | [#47](https://github.com/tina4stack/tina4-python/issues/47) | open, **comment posted 2026-06-09** (MichaelC8E) | 2026-06-08 | **`psycopg2-binary` (and the other 5 DB drivers) is required at runtime but not bundled by default.** Verified on tina4-python **3.13.5** (upgraded from 3.13.4 on 2026-06-09; bug-direction behaviour identical). OP's claim is correct on all 4 parts: (a) `psycopg2` required — `postgres.py:54-58` lazy-imports + raises; (b) not bundled — METADATA only declares it under `Requires-Dist: psycopg2-binary>=2.9; extra == 'postgres'`, no unconditional Requires-Dist; (c) "by design" matches the zero-dep framing in Ch1 line 5 + 8 declared extras (postgres/mysql/mssql/firebird/mongo/odbc/all-db/dev-reload), same pattern at all 6 adapters; (d) "needs documenting" — partially true. **Where the requirement IS documented:** METADATA lines 145-155 + PyPI page + repo README (full extras list); Book Ch5 Database flags it but only with bare `uv add psycopg2-binary` (no extras syntax). **Where it ISN'T:** Book Ch1 Getting Started — zero hits on postgres / psycopg / mysql / driver / extras / optional across all 1132 lines, despite Ch1 line 152's *"One package. No dependency tree. Just `tina4-python`."* claim. Plus the 6 lazy-import ImportError messages all recommend bare `pip install <driver>` rather than the canonical `tina4-python[<extra>]` form from METADATA itself. Plus `tina4 init python .` scaffolded `pyproject.toml` comments suggest bare `uv add psycopg2-binary`. Repo-wide grep for `tina4-python[` across `documentation/tina4-book/` and `pypy/.venv/Lib/site-packages/tina4_python/`: zero matches outside METADATA. **Adversarial disproof attempts (2026-06-09):** checked for hidden DB-driver mention later in Ch1 (none); checked for separate `/python/installation` or `/python/getting-started.html` docs (404); checked for CHANGELOG mentioning extras (no CHANGELOG in dist-info); confirmed pip absent from uv-scaffolded `.venv/Scripts/` (bare `pip install` literal advice would fail). Dropped "version pin bypass" angle (pin is `>=2.9`, loose); real cost = maintainer can't redirect driver choice (e.g. psycopg2 → psycopg3) without rewriting 6 ImportError sites + book chapter. Softened Ch1 framing from "contradicts" to "no callout". **Recommendations (in posted comment):** primary = docs-only (Ch1 prerequisites callout + Ch5 switch to extras syntax + rewrite 6 ImportError texts); alternatives if maintainer wants a UX change = bundle all 6 into base deps (kills zero-dep claim), baseline subset like `[postgres,mysql]` pre-included, or `tina4 init python --db=postgres` scaffolder flag (lowest-disruption). Evidence: `bug-hunting/issue-47-psycopg2-dep-gap.md` (full analysis + adversarial disproof results), `bug-hunting/issue-47-comment.md` (exact posted body). No probe — pure doc gap. |

## Suggested Fixes

Proposed remedies for entries in the Known Issues Log. Each fix tags one or more issue IDs
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

### FIX-04 — `tina4 test` output formatter: per-file bar, right-anchored status, bottom printer line

**Tags:** PY-18-04
**Page:** `https://tina4.com/python/18-testing.html` S1, S2, S4, S8 output
examples, plus the CLI implementation in the Rust binary.
**Status:** proposed

**The problem in one sentence.** S1's framing of `tina4 test` as having its
own readable output format was honest-on-paper but fictional in practice;
the 3.13.4 fix corrected the docs to acknowledge pytest. A real custom
formatter would let the chapter's *original* visual intent ship, and would
read better than raw pytest dots for the typical Tina4 workflow.

**Proposed layout — two modes.** Both modes share: per-file fill-bar (fills
as the file's tests complete), bottom "printer line" updating in place with
the running test ID, final failure list showing exact failing test IDs.

**Normal mode** (default): per-file row only. PASS/FAIL right-anchored to a
fixed column so status doesn't drift with varying filename widths. Bar
leftmost, filename middle. No per-file counts, no per-file times.

```
================================= Tina4 test run =================================

 ████████████████████  test_ch18_basic.py                                     PASS
 ████████████████████  test_ch18_assertions.py                                PASS
 ████████████████████  test_ch18_product.py                                   PASS
 ████████████░░░░░░░░  test_ch18_routes.py                                    ····
 ░░░░░░░░░░░░░░░░░░░░  test_ch18_client_methods.py                              -
 ░░░░░░░░░░░░░░░░░░░░  test_ch18_auth.py                                        -

──────────────────────────────────────────────────────────────────────────────────
 [█████████████████░░░░░░░░░░░░░░░]  26/59  •  test_ch18_routes::test_create_product
```

Final state of normal mode:

```
================================= Tina4 test run =================================

 ████████████████████  test_ch18_basic.py                                     PASS
 ████████████████████  test_ch18_assertions.py                                PASS
 ████████████████████  test_ch18_product.py                                   PASS
 ██████░░░░░░░░░░░░░░  test_ch18_routes.py                                    FAIL
 ████████████████████  test_ch18_client_methods.py                            PASS
 ████████████████████  test_ch18_auth.py                                      PASS
 ████████████████████  test_ch18_setup_teardown.py                            PASS

──────────────────────────────────────────────────────────────────────────────────
 [████████████████████████████████]  55/59 passed  •  4 failed  •  0.33s

 Failures (4):
   FAIL  test_ch18_routes::test_get_products       AssertionError: Should return 200
   FAIL  test_ch18_routes::test_create_product     TypeError: Test.post() takes ...
   FAIL  test_ch18_routes::test_delete_product     KeyError: 'id'
   FAIL  test_ch18_routes::test_validation         AssertionError: empty body
```

**Verbose mode** (`--verbose`, see FIX-03 / PY-18-03): per-file header
unchanged in shape but adds counts (`n/m`) and per-file time on the right;
each test rendered as an indented row underneath with its own PASS/FAIL
and time. Status left-anchored on the per-file row so the indented per-test
rows line up under it.

```
========================== Tina4 test run (verbose) ==========================

 PASS   ████████████████████  test_ch18_basic.py                    3/3    0.02s
        PASS  test_addition                                                0.001s
        PASS  test_string_contains                                         0.000s
        PASS  test_array_length                                            0.001s

 PASS   ████████████████████  test_ch18_assertions.py             13/13    0.03s
        PASS  AssertEqualTest::test_equal_numbers                          0.000s
        ...

 ····   ████████████░░░░░░░░  test_ch18_routes.py                   4/6    ...
        PASS  test_health_endpoint                                         0.005s
        PASS  test_get_products                                            0.012s
        FAIL  test_create_product                                          0.008s
              TypeError: Test.post() takes 2 positional arguments but 3 given
        PASS  test_get_product_not_found                                   0.003s

──────────────────────────────────────────────────────────────────────────────────
 [█████████████████░░░░░░░░░░░░░░░]  26/59  •  test_ch18_routes::test_create_product
```

**What each mode does and doesn't surface.**

| Element                              | Normal | Verbose |
|--------------------------------------|:------:|:-------:|
| Per-file fill-bar + PASS/FAIL        |   ✓    |    ✓    |
| Per-file counts (n/m tests)          |   ✗    |    ✓    |
| Per-file time                        |   ✗    |    ✓    |
| Per-test indented rows               |   ✗    |    ✓    |
| Per-test time                        |   ✗    |    ✓    |
| Bottom printer line (current test)   |   ✓    |    ✓    |
| Bottom failure list (exact test IDs) |   ✓    |    ✓    |

The failure list at the bottom of normal mode is the key trade-off — normal
mode hides per-test detail in the body but never hides which specific tests
failed. A reader scanning the right-hand column for `FAIL` knows which file
broke; the failure list tells them exactly which test inside.

**Rationale.**

- Right-anchored status in normal mode = the rightmost column becomes a
  fail roll-call. Eye finds failures at a fixed x-coordinate regardless of
  filename length.
- Fill-bar per file = real progress signal (fills as the file's tests run),
  not pytest's "% of total collected" which jumps unpredictably across files.
- Bottom printer line in place of file-by-file dot stream = one moving
  cursor showing the current test ID. Friendlier than the percentage
  progress at the end of each pytest file line.
- Mode split = readers who only want "did anything break" use normal;
  readers debugging a specific test use verbose. Pytest's `-q` / `-v` split
  is the same split; this is the same idea with a Tina4-native skin.

**Doc updates once implemented.** S1, S2, S4 output examples currently
show raw pytest output (post-PY-18-04 fix). Replace those with the normal-
mode mock above. S8 currently mentions `--verbose` (rejected by the CLI per
PY-18-03); once the formatter ships, the `--verbose` example should output
the verbose-mode mock above.

**Acceptance criteria.**

- `tina4 test` (default) emits the normal-mode layout: per-file bar +
  right-anchored PASS/FAIL, bottom printer line, bottom failure list with
  exact failing test IDs.
- `tina4 test --verbose` emits the verbose-mode layout: same per-file row
  but with counts + time, plus per-test indented rows.
- Both modes share the same final failure list format.
- S1, S2, S4, S8 doc examples updated to match the actual output.
- Raw pytest output remains accessible (e.g. `tina4 test --raw` or
  `uv run python -m pytest`) so users who need the underlying tool aren't
  blocked.

#### Implementation specification — exact characters, widths, and rules

This section nails down the visual primitives so an implementer can build
the formatter without guessing. Mocks above are illustrative; the rules
below are normative.

**Character set (Unicode codepoints).**

| Glyph | Codepoint | Name             | Where used                                              |
|-------|-----------|------------------|---------------------------------------------------------|
| `█`   | U+2588    | FULL BLOCK       | Bar — filled cell (per-file bar and bottom overall bar) |
| `░`   | U+2591    | LIGHT SHADE      | Bar — empty cell                                        |
| `·`   | U+00B7    | MIDDLE DOT       | "Running" status glyph (four of them: `····`)           |
| `─`   | U+2500    | BOX DRAWINGS LIGHT HORIZONTAL | Section separator above the bottom bar     |
| `=`   | U+003D    | EQUALS SIGN (ASCII) | Run header rule (`=== Tina4 test run ===`)           |
| `•`   | U+2022    | BULLET           | Inline separator in the bottom line (e.g. `26/59 • test_…`) |
| ` `   | U+0020    | SPACE            | All padding (NEVER tab / U+0009)                        |
| `-`   | U+002D    | HYPHEN-MINUS (ASCII) | Not-started status placeholder in normal mode       |

Do **not** substitute visually-similar glyphs:
- `█` ≠ `■` (U+25A0 BLACK SQUARE) — squares mis-render half-height in some terminals.
- `░` ≠ `▒` (U+2592 MEDIUM SHADE) — medium shade reads as 50% fill, not "empty".
- `·` ≠ `•` ≠ `.` — middle dot is the running glyph, bullet is the inline
  separator, full stop is never used.
- `─` ≠ `—` (em dash) ≠ `-` (hyphen-minus) — the separator must be
  U+2500 box drawing.
- ASCII `=` is correct for the header rule. Do NOT use `═` (U+2550 DOUBLE
  HORIZONTAL) — pytest uses `=` and the header reads as the Tina4 layer
  above pytest; keeping `=` reinforces continuity.

**Fallback for non-UTF8 / Windows legacy code-page terminals.** Detect
encoding at startup; if the stream can't encode U+2588/U+2591/U+00B7, fall
back to:

| Unicode | ASCII fallback |
|---------|----------------|
| `█`     | `#`            |
| `░`     | `.`            |
| `····`  | `....` (four ASCII full stops) |
| `─`     | `-`            |
| `•`     | `*`            |

No mixing — either pure-Unicode or pure-ASCII for a given run. A
`TINA4_TEST_ASCII=1` env var forces the ASCII set.

**Column widths.** Fixed for both modes. Lengths are in display cells, not
bytes (every glyph above is single-cell width — no double-wide CJK chars
in the format itself).

| Column                                | Width | Mode      |
|---------------------------------------|------:|-----------|
| Left edge gutter (space)              |   1   | both      |
| Bar                                   |  20   | both      |
| Bar→filename gutter (spaces)          |   2   | both      |
| Filename                              |  50   | both (left-padded with spaces) |
| Filename→status gutter (spaces)       |   2   | normal — status on right       |
| Status (`PASS`/`FAIL`/`····`/`-`)     |   4   | normal — right-aligned in the 4-cell slot |
| Status before bar (per-file row)      |   4   | verbose — left, *before* bar  |
| Status→bar gutter (verbose)           |   2   | verbose                       |
| n/m count                             |   5   | verbose (right-aligned, e.g. ` 3/3 `, `13/13`) |
| count→time gutter                     |   3   | verbose                       |
| Time                                  |   6   | verbose (right-aligned, e.g. `0.02s`, `0.001s`)|

Total line widths come out to 82 cells normal, 82 cells verbose — keep
them equal so the separator rule below renders the same length in both.

**Bar fill rule.**

```
filled_cells = round(20 * tests_completed_in_file / tests_total_in_file)
empty_cells  = 20 - filled_cells
bar = "█" * filled_cells + "░" * empty_cells
```

Rounding is half-to-even (banker's rounding) — avoid surprise full bars
when one test in many is still pending. If `tests_total_in_file` is
unknown during collection, render `░` × 20 with status `-`.

**Status glyph rules.**

- `PASS` — every test in the file passed.
- `FAIL` — at least one test in the file failed OR errored (collection
  error counts as FAIL on the file row).
- `····` (four U+00B7) — file currently running, at least one test started.
- `-` — file not yet started (collected but waiting).
- Status string is exactly 4 cells; right-pad with spaces if any future
  status is shorter (e.g. `OK` would render as `OK  `, never `OK`).

**Right-alignment (normal mode).** The status column ends at cell 82 of
the line. Compute:

```
status_left_edge = 82 - 4 = 78
filename_right_edge = 78 - 2 = 76   # 2-cell gutter
```

Pad filename column with trailing spaces so its right edge sits at cell 76.
For the not-started rows, render `-` right-aligned in the 4-cell slot
(`   -`) — the same column as `PASS`/`FAIL` — so the rightmost column reads
cleanly top-to-bottom.

**Bottom printer line.** Single line, rewritten in place via ANSI
`\r` + `\x1b[2K` (carriage return + erase line). No newline at end while
running. Once the run completes, emit a newline and replace with the
final summary line. Format:

```
 [<bar32>]  <done>/<total>  •  <current_test_id>
```

Where `<bar32>` is 32 cells using the same `█`/`░` chars; `<done>` and
`<total>` are integers (no padding); `<current_test_id>` is
`file_stem::class::method` (no `tests/` prefix, no `.py` suffix), truncated
to fit terminal width minus the prefix using middle-ellipsis (e.g.
`test_ch18_routes::…::test_create_product`).

**Final summary line** (replaces the printer line on completion):

```
 [████████████████████████████████]  <p> passed  •  <f> failed  •  <T>s
```

Bar always full (32 `█`). `<p>` and `<f>` are integer counts; `<T>` is
total wall-clock seconds to 2 decimal places (e.g. `0.33`). Drop the
`• <f> failed` clause entirely when `<f> == 0`.

**Failure list** (appears after the summary line, when `<f> > 0`):

```
 Failures (<f>):
   FAIL  <file_stem>::<class>::<method>   <ExceptionType>: <single-line message>
   ...
```

Rules:
- `Failures (N):` heading line, exactly one space before `Failures`.
- Each failure row: 3-space indent, `FAIL  ` (status + 2 spaces),
  test ID, 3 spaces, exception class + colon + first line of message.
- Truncate the message to keep the row at ≤ 100 cells; suffix `…` if
  truncated. Full traceback available via `--verbose` or in a written
  log file at `logs/tina4-test-<timestamp>.log`.
- No blank line between failure rows. One blank line before the heading,
  one blank line after the last row.

**Time format.**

- Per-test time (verbose only): seconds to 3 decimals, e.g. `0.001s`,
  always 5 chars + `s` = 6 cells. Under 1ms shows `0.000s` (not `<0.001s`).
- Per-file time (verbose only): seconds to 2 decimals, e.g. `0.02s`,
  always 4 chars + `s` = 5 cells (allow up to 99.99s; over that, switch to
  `XXm` for whole minutes with no decimals).
- Total run time (summary): same as per-file but unbounded — render
  `0.33s`, `12.45s`, `1m23s`, `5m04s` as the magnitude requires.

**Colour scheme** (when stdout is a TTY and `NO_COLOR` env var is unset):

| Element                            | ANSI                                |
|------------------------------------|-------------------------------------|
| `PASS`                             | bright green (`\x1b[92m`)           |
| `FAIL`                             | bright red (`\x1b[91m`)             |
| `····` running                     | bright yellow (`\x1b[93m`)          |
| `-` not started                    | dim grey (`\x1b[2m\x1b[37m`)        |
| Bar filled cells                   | inherit terminal default (no colour) |
| Bar empty cells                    | dim grey                            |
| Bottom bar filled                  | inherit                             |
| Filename                           | inherit                             |
| Failure rows `FAIL` glyph + ID     | bright red                          |
| Failure exception line             | inherit                             |
| Run header / separator rules       | dim grey                            |

When `NO_COLOR` is set, or stdout is not a TTY, emit plain ASCII/Unicode
with no escape sequences. The fallback in this case is the same layout —
colour is decorative only.

**Indentation in verbose mode per-test rows.** 8 spaces (matches the
length of the per-file row's "status + gutter + bar start"), then 4-cell
`PASS`/`FAIL` (left-aligned), then 2-space gutter, then test name
(class-qualified), then padding to time column. Time format same as
per-file time but 3 decimals (per-test rule above).

**Things to NOT do (anti-patterns seen elsewhere):**

- Don't use ANSI cursor-up to overwrite the per-file rows — the running
  file's row gets its bar updated in place, but completed rows above
  must stay put. Use a single bottom-line cursor pattern only.
- Don't right-trim trailing whitespace on a row before emitting it —
  the trailing spaces are load-bearing for the right-aligned status
  column. Trimming breaks alignment in terminals that auto-trim.
- Don't print the run header until after collection completes — the
  count `26/59` in the printer line needs the total. Show a single-line
  "Collecting tests…" stub during collection, then redraw.
- Don't substitute the four middle dots `····` with three (`···`) or an
  ellipsis `…` — the running glyph is always exactly 4 cells to match
  `PASS`/`FAIL` width.
- Don't render the per-file bar live-updating cell-by-cell as each test
  finishes if the file completes in under 100 ms — the flicker reads as
  glitchy. Batch updates at 100 ms minimum cadence, or render the file
  row only on file completion if the whole file ran under that threshold.

---

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
