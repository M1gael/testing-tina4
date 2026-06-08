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
| **Probe pattern as evidence + regression sentinel** | Write a `tests/test_chNN_<topic>_probe.py` for every finding whose framework characteristic is testable in code. "Where possible" carves out narrative / structural findings (not expressible as an assertion). **Assert the CORRECT framework state, not the buggy state.** The probe FAILS before the fix (bug visible) and PASSES after (fix confirmed) without any edit. After the fix lands the probe stays live in the active suite — a steady-state PASS that flips to FAIL the moment the framework regresses. Existing patterns: trace-list inspection via direct dispatcher invocation (`pypy/tests/test_ch10_middleware_probe.py` for `PY-10-01/02/03`), positive contract assertions on framework objects (`pypy/tests/test_ch18_response_object_probe.py` for `PY-18-10`). One assertion = one observation; reference the probe filename from the KI Log row. File header records finding history + fix version. |
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
| Python | 02–09, 11–17, 19–38 | — | not-started | — |
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
tests and theories until root cause is nailed down."

**Where the code lives.** Investigation artifacts (probes, repro
models, fix patches, draft upstream comments) are committed to the
`bug-hunting` branch, NOT to `main`. This keeps `main` silver-lined
for documentation-fidelity work. This section on `main` is the
narrative log + index pointing at the `bug-hunting` branch.

**ID convention:** `BH-<n>` where `<n>` is the upstream GitHub issue
number on the framework repo (e.g. `BH-46` ↔
[`tina4stack/tina4-python#46`](https://github.com/tina4stack/tina4-python/issues/46)).
Direct numeric mapping — no chapter-prefix translation as with the
`PY-NN-NN` doc-fidelity IDs.

**Upstream tracking.** All Bug Hunt findings link to a real GitHub
issue on [`tina4stack/tina4-python`](https://github.com/tina4stack/tina4-python/issues).
The issue thread itself is the "official log" of the framework
defect; this section is the local evidence map pointing at it.

### Tracking table

| ID | Language | Issue # | Status | Date | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| BH-46 | Python | [#46](https://github.com/tina4stack/tina4-python/issues/46) | open upstream, root-caused, live-reproduced, patches drafted + adversarially verified, comment posted to upstream | 2026-06-08 | **`PostgreSQLAdapter.fetch()` count-probe (`tina4_python/database/postgres.py:146-152` pristine 3.13.4) swallows exceptions without rollback or savepoint, poisoning the PG connection's transaction.** The bare `try: ... except Exception: total = 0` discards the original cause (e.g. `operator does not exist: boolean = integer` when a filter like `is_deleted = 0` hits a `BOOLEAN` column) and leaves `_conn.autocommit=False` (`postgres.py:70`) sitting on an aborted transaction. The next line's paginated SELECT then raises `InFailedSqlTransaction` ("current transaction is aborted, commands ignored until end of transaction block") — that cascade message is the only thing the caller sees. Visibility gap: `grep -rn "Log\." tina4_python/database/ tina4_python/orm/` returns zero matches in 3.13.4, and `Database.get_error()` returns `None` after a `fetch()` failure (only `Database.execute()` writes to `last_error`). Framework already has the fix pattern in-tree at `postgres.py:99-122` (`SAVEPOINT _t4_lastval_probe`, added for [#38](https://github.com/tina4stack/tina4-python/issues/38)) — the COUNT query needs the same wrapper. **See "BH-46 investigation log" below for the full narrative + continuation pointers.** |
| BH-47 | Python | [#47](https://github.com/tina4stack/tina4-python/issues/47) | open, doc gap, comment not yet posted | 2026-06-08 | **`psycopg2-binary` required for PostgreSQL but not installed by `tina4 init python .`.** Packaging is correct (`tina4-python` 3.13.4 METADATA declares PEP 621 extras for `postgres`, `mysql`, `mssql`, `firebird`, `mongo`, `odbc`, `memcache`, `redis`, `all-db`), but three things make this invisible: (a) `tina4 init python .` does not install any DB extra — scaffolded `pyproject.toml` adds bare `tina4-python`; (b) lazy-import error at `postgres.py:54-58` recommends `pip install psycopg2-binary` rather than `pip install 'tina4-python[postgres]'` — bare install bypasses lockfile; (c) Chapter 6 (Database) on tina4.com shows connection URLs for all 5 engines without a prerequisites callout. Author commented "by design — just needs documentation" on the upstream issue. Draft comment ready at `bug-hunting/issue-47-psycopg2-dep-gap.md`; not yet posted. |

### BH-46 — investigation log

Filed upstream by **`SAB13711`** on the framework repo as
[`tina4stack/tina4-python#46`](https://github.com/tina4stack/tina4-python/issues/46),
title *"No database error visibility"*. Investigated **2026-06-08**;
findings comment posted to the upstream thread the same day by
**`MichaelC8E`** (not the original reporter — investigation done on
their behalf). Patches drafted, adversarially verified locally, not
yet opened as a PR; the comment ends with a code snippet showing
the fix shape that a maintainer can implement directly.

#### Reporter's symptom (verbatim from issue body)

```
2026-06-08T09:16:47.722Z [ERROR  ] [b83e41207149e7ea80c873ca9353e0dd]
  [get_gift_cards_for_user] returning failed result:
  code:500, msg:Could not get gift cards for user,
  error:current transaction is aborted, commands ignored until end of transaction block
2026-06-08T09:16:47.718Z [DEBUG  ] Getting created gift cards for user
  {"email": "schalk@codeinfinity.co.za"}
```

> *"There are no logs after that point and it is the first point that a
> database call is made. It seems the very first call is already
> saying that the database connection is blocked."*

Triggering call: `GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])`.

#### Investigation timeline

1. **Source-read of `tina4_python/database/postgres.py`** — identified
   the bare `try/except: total = 0` at lines 146-152 (pristine 3.13.4)
   wrapping the COUNT query inside `PostgreSQLAdapter.fetch()`. No
   rollback, no savepoint, no log call.
2. **Source-read of connection setup** — confirmed `_conn.autocommit = False`
   at `postgres.py:70`. Combined with the swallow path, the cascade
   mechanism was clear: a failed COUNT poisons the transaction, the
   next statement raises `InFailedSqlTransaction`, the original cause
   is gone.
3. **Adversarial verification of the hypothesis (4 disproof angles, all failed):**
   - Searched for a `rollback()` call inside `Database.execute()`'s except block — none.
   - `grep -rn "Log\." tina4_python/database/ tina4_python/orm/` — returned zero matches; the entire DB+ORM layer has no structured-log calls on swallow paths.
   - Verified `TINA4_AUTOCOMMIT=true` does NOT escape the cascade — the env var only flips the adapter's Python-side `_autocommit` flag (`adapter.py:307`); `_conn.autocommit` is hardcoded `False` at `postgres.py:70` so PG remains in implicit-txn mode.
   - Re-read `postgres.py:148-152` for any SAVEPOINT/rollback the patch series might have missed — none present; SAVEPOINT only exists at `postgres.py:99-122` for the `lastval()` query (added for upstream issue #38).
4. **Local infrastructure setup** — installed PostgreSQL 18.4 via
   `winget install PostgreSQL.PostgreSQL.18 --silent` with
   `--superpassword tina4test`, added `psycopg2-binary==2.9.12` to
   the `pypy/` venv via `uv add psycopg2-binary`, created
   `tina4_bug46` database with a `gift_cards` table whose
   `is_deleted` column is `BOOLEAN` (matching the typical PG idiom
   inferred from the reporter's filter).
5. **Live reproduction** — ran the reporter's filter via `Model.where()`
   against the live DB; captured byte-identical `InFailedSqlTransaction:
   current transaction is aborted, commands ignored until end of
   transaction block` message. Raw psycopg2 call against the same DB
   raised `psycopg2.errors.UndefinedFunction: operator does not exist:
   boolean = integer` with line/column pointer at the failing filter.
   Bottom-layer string matches the reporter's log byte-for-byte.
   `Database.get_error()` returned `None` after the failure — confirmed
   the visibility gap is total (no log, no `last_error`, no preserved
   trace).
6. **Fix design** — cloned the existing #38 pattern at `postgres.py:99-122`
   (`SAVEPOINT _t4_lastval_probe` → ROLLBACK TO on failure) and applied
   the same shape to the COUNT query. Decision to also wrap the
   paginated SELECT in its own SAVEPOINT was made after adversarial
   testing exposed a paginated-query cascade gap (see step 9).
7. **Patches applied to the venv copy of the framework (3 files):**
   - `postgres.py` — SAVEPOINT around both the COUNT and the paginated SELECT; `Log.error` on count-probe failure with cause + outer SQL.
   - `connection.py` — `Log.error` before the existing `return False` in `Database.execute()`'s except (no flow change).
   - `orm/model.py` — `Log.error` in 4 ORM CRUD except blocks (`save` / `delete` / `force_delete` / `restore`). No contract change — `save()` still returns `False`; the others still re-raise.
   - Every `from tina4_python.debug import Log; Log.error(...)` call is itself wrapped in `try / except Exception: pass` so a broken/absent logger cannot break the data path.
8. **Probe development (3 files, 19 tests total, all gated to skip when PG infrastructure is absent):**
   - **Live PG repro** (5 tests) — psycopg2 raw error capture, framework-surfaced cascade capture, `Log.error` capture via `capfd`, baseline fixture sanity, `db.last_error` is None check.
   - **Mock-cursor source-read probe** (4 tests) — synthetic psycopg2 cursor that mimics aborted-txn semantics; exercises the real `PostgreSQLAdapter.fetch()` code path without needing a live PG. Asserts SAVEPOINT issued, ROLLBACK TO on failure, paginated query proceeds, `Log.error` emitted.
   - **Adversarial sweep** (10 tests, see step 10).
9. **First adversarial run revealed a real fix gap.** 4 of 10 attacks
   failed against the count-probe-only fix because the paginated SELECT
   was still running raw — its own failure poisoned the connection on
   the way out. Expanded the postgres.py patch to wrap the paginated
   SELECT in its own SAVEPOINT too. Second adversarial run: 10/10 pass.
   This is documented in the patch commit message: *"adversarial finding
   — count-probe SAVEPOINT alone left paginated failures poisoning the
   conn for subsequent statements."*
10. **Adversarial attacks tried (the fix-breaking sweep):**
    - Repeated identical failures — must not compound.
    - Alternating valid/invalid queries — must leave no residue.
    - Failures inside a user-driven `start_transaction()` block — outer transaction must survive (verified by INSERT + rollback() after the failure).
    - SAVEPOINT name collision with a user-named SAVEPOINT of the same name — informational; framework's `_t4_count` is unlikely to collide in practice, flagged as a separate adjacent finding.
    - Credential leak check — connection-string password must not appear in any Log payload.
    - Very long SQL (50-clause OR chain) — Log line must not crash or truncate.
    - `ORM.save()` contract preservation — must return `False`, not raise, after the Log.error addition.
    - Paginated-query failure on an unrelated bad table — must still propagate (no over-eager swallow).
    - Sabotaged `Log.error` (monkeypatched to raise) — data path must not break because logging broke.
    - Healthy non-failing queries — must still report correct counts (the SAVEPOINT must not always trigger the fallback).
11. **Adjacent bugs surfaced during adversarial testing (NOT yet filed
    upstream — separate issues recommended):**
    - **`SQLTranslator.boolean_to_int`** (`tina4_python/database/adapter.py:538-542`)
      unconditionally rewrites `\bTRUE\b` → `1` and `\bFALSE\b` → `0` on
      the PG translation path. Against a real `BOOLEAN` column this
      reintroduces the BOOLEAN-vs-integer mismatch in framework-generated
      SQL — a caller writing `is_deleted = FALSE` to dodge this issue
      still hits the operator error, because the translator rewrites the
      literal before psycopg2 sees it. Translator should skip the
      rewrite on engines with native boolean support.
    - **SAVEPOINT name collision** — the proposed fix uses fixed names
      (`_t4_count`, `_t4_paginated`). If a caller has an outer
      SAVEPOINT with the same name, the framework's `RELEASE SAVEPOINT`
      will end the caller's SAVEPOINT too. Low practical impact;
      trivially fixed with a unique-per-call suffix (e.g. `id(cursor)`).
12. **Final suite state on `bug-hunting` branch:** 69 passed, 2 skipped.
    19 new tests (5 live PG + 4 mock probe + 10 adversarial) pass against
    the patched framework; the same tests' bug-direction assertions FAIL
    against pristine 3.13.4 — regression-sentinel pattern works as
    designed. No regressions on the 50 pre-existing chapter-fidelity
    tests.
13. **Upstream comment posted** to issue #46 on 2026-06-08 by
    `MichaelC8E`. Structure: 5 numbered findings (bug location, cascade
    mechanism, reproduction output, visibility gap, fix-pattern-already-in-tree),
    "Worth noting" with the BOOLEAN/integer trigger framing + the
    boolean_to_int adjacent bug, and a "Potential fix" code block
    showing the count-probe SAVEPOINT shape. Final comment text saved
    at `bug-hunting/issue-46-comment.md` on the `bug-hunting` branch.
14. **Patches NOT yet attached to the upstream thread or opened as a
    PR.** Three unified diffs ready at
    `bug-hunting/fix-issue-46-patches/` that `git apply --check`-pass
    cleanly against a pristine 3.13.4 checkout. If the maintainer
    requests them, attach or open a PR referencing #46.

#### Where the code lives (`bug-hunting` branch)

| Path | Purpose |
|---|---|
| `bug-hunting/README.md` | Branch-purpose index, pointers to the canonical Bug Hunt section here |
| `bug-hunting/issue-46-pg-silent-abort.md` | Long-form analysis (root cause, adversarial verification, recommended fix shape) |
| `bug-hunting/issue-46-comment.md` | Final upstream-posted comment text — what was pasted into #46 on 2026-06-08 |
| `bug-hunting/fix-issue-46-patches/01-postgres-savepoint-count-and-paginated.patch` | Primary fix — both SAVEPOINTs + Log.error |
| `bug-hunting/fix-issue-46-patches/02-connection-execute-log.patch` | `Log.error` in `Database.execute()` swallow |
| `bug-hunting/fix-issue-46-patches/03-model-orm-log.patch` | `Log.error` in 4 ORM CRUD swallows |
| `bug-hunting/fix-issue-46-patches/README.md` | Patch series overview + apply instructions |
| `pypy/tests/test_issue_46_live_repro.py` | 5 live PG reproduction tests |
| `pypy/tests/test_issue_46_pg_silent_abort_probe.py` | 4 mock-cursor source-read tests |
| `pypy/tests/test_issue_46_fix_adversarial.py` | 10 hostile-input fix-breaking tests |
| `pypy/src/orm/GiftCard.py` | Repro ORM model (mirrors the reporter's column layout) |
| `pypy/pyproject.toml` + `uv.lock` | Adds `psycopg2-binary` as a dev dep (NOT brought to `main`) |

#### Continuation pointers (for any LLM picking this up)

If you need to revisit BH-46:

1. **Check upstream status first.** `gh issue view 46 --repo tina4stack/tina4-python --comments` — see if the issue has progressed (closed, merge linked, maintainer response, etc.). The state recorded here is as of 2026-06-08.
2. **To re-run the tests / reproduce locally:** `git checkout bug-hunting`. This restores all artifacts. Requirements: PostgreSQL 18.4+ reachable on `localhost:5432` with superuser `postgres` / password `tina4test`, a database named `tina4_bug46` with the `gift_cards` schema in step 4 of the timeline above, and `psycopg2-binary` in the `pypy/` venv. Tests skip cleanly when these are missing (gated via `pytest.importorskip("psycopg2")` + a PG-reachability probe).
3. **Schema for the fixture** (recreate if lost):
   ```sql
   CREATE DATABASE tina4_bug46;
   \c tina4_bug46
   CREATE TABLE gift_cards (
       id SERIAL PRIMARY KEY,
       created_by_email VARCHAR(200) NOT NULL,
       owned_by_email VARCHAR(200),
       amount NUMERIC(10,2) NOT NULL,
       is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   INSERT INTO gift_cards (created_by_email, owned_by_email, amount, is_deleted) VALUES
   ('schalk@codeinfinity.co.za', 'alice@example.com', 100.00, FALSE),
   ('schalk@codeinfinity.co.za', 'bob@example.com',   50.00, FALSE),
   ('alice@example.com',        'schalk@codeinfinity.co.za', 25.00, TRUE);
   ```
4. **To switch between pre- and post-fix states for verification:**
   - **Pristine baseline (bug-active):** from `pypy/`, run
     `uv pip install --force-reinstall --no-deps tina4-python==3.13.4`.
     Bug-direction assertions in `test_issue_46_live_repro.py` should
     FAIL (cascade message + zero log emitted), proving the bug exists
     in the released framework.
   - **Patched (bug-closed):** from project root, run
     ```
     git apply --directory=pypy/.venv/Lib/site-packages/ bug-hunting/fix-issue-46-patches/01-postgres-savepoint-count-and-paginated.patch
     git apply --directory=pypy/.venv/Lib/site-packages/ bug-hunting/fix-issue-46-patches/02-connection-execute-log.patch
     git apply --directory=pypy/.venv/Lib/site-packages/ bug-hunting/fix-issue-46-patches/03-model-orm-log.patch
     ```
     Then all 19 BH-46 tests should PASS (regression-sentinel flip).
   - The patches are line-ending-clean as committed in the git tree; if `git apply` complains about CRLF on Windows, `tr -d '\r' < file.patch > tmp && mv tmp file.patch` normalises it.
5. **Open follow-up work to consider:**
   - File the two adjacent bugs (boolean_to_int translator + SAVEPOINT name collision) as separate upstream issues if the maintainer hasn't already addressed them via the BH-46 fix.
   - If the upstream maintainer wants patches, the patches in `bug-hunting/fix-issue-46-patches/` are ready to attach or open as a PR. Suggested PR title: `Fix #46: SAVEPOINT around COUNT probe and paginated SELECT + Log.error on swallow paths`.
   - The other DB adapters (`mysql.py`, `mssql.py`, `firebird.py`, `mongodb.py`) have analogous `except Exception` swallow patterns that were NOT investigated. Whether they cascade the same way depends on the underlying driver's transaction semantics — worth a follow-up sweep if cross-driver parity matters.
   - Doc-fidelity work (PY-NN-NN findings on `main`) continues independently of this bug. Ch18 S11/S12 auth-flow scaffold was paused mid-investigation per the user's "we will come back to 11" directive and remains the natural resume point on `main`.

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
