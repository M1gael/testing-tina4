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
| **Probe pattern as evidence** | When a code-block-level claim is ambiguous or hard to argue from prose alone, write a small test file that pits the doc's claim against the framework's actual API — each `test_doc_*` asserts the chapter's wording verbatim, each `test_real_*` asserts the framework's truth. The PASS/FAIL split is the receipt. Example: `pypy/tests/test_ch18_response_object_probe.py` for `PY-18-10`. |
| *— Filing cadence & labels —* | |
| **Local-first, upstream-at-EOD** | Findings are logged locally throughout the day (Known Issues Log row + detailed evidence section). The USER batches the upstream filings at end of day. The assistant does not push to file mid-session. |
| **Upstream label** | Every upstream issue/comment title prefixed with `[<finding-id>]`, e.g. `[PY-18-10] Section 5 — Response Object reference doesn't match TestResponse`. |
| *— Test files —* | |
| **Newest stays verbatim, older patched** | Within a chapter, only the most-recently-created test file stays unpatched. When moving to the next file, the USER triggers the patch on the previous one (see [Patching Convention](#patching-convention)). |
| *— Voice —* | |
| **Neutral voice** | No "we" / "I" / "us" in prose. Local logs, detailed evidence sections, and upstream filings all use clinical, actor-free phrasing: "the chapter shows", "the framework returned", "the snippet fails because…". See [Issue Report Format](#issue-report-format) for the canonical wording. |

## Evaluation Progress

Refreshed whenever a new test file is added or a finding ID is logged. Status values:
`in-progress` (some sections touched) | `complete` (all sections implemented) | `not-started`.

| Language | Chapter | Sections covered | Status | Findings |
| :--- | :--- | :--- | :--- | :--- |
| Python | 01 — Getting Started | (whole chapter, narrative) | in-progress | PY-01-01, PY-01-03, PY-01-05, PY-01-06, PY-01-07, PY-01-08 |
| Python | 10 — Middleware & Security | §3, §4, §9, §10, §12 (source + coworker incident — not yet implemented verbatim) | findings logged, impl pending | PY-10-01, PY-10-02, PY-10-03 |
| Python | 18 — Testing | §2, §3, §4, §5, §6 (of 13) | in-progress | PY-18-01, PY-18-02, PY-18-03, PY-18-04, PY-18-07, PY-18-08, PY-18-10 |
| Python | 02–09, 11–17, 19–38 | — | not-started | — |
| PHP | all | — | not-started (workspace not bootstrapped) | — |
| Ruby | all | — | not-started (workspace not bootstrapped) | — |

## Known Issues Log

All confirmed framework bugs and documentation discrepancies are tracked here.
Status values: `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.

**Upstream tracking:**
- [tina4stack/tina4-book#140](https://github.com/tina4stack/tina4-book/issues/140) — Testing chapter issues. Comments filed so far: `[PY-18-04]`, `[PY-18-07a]`, `[PY-18-08]`. Other PY-18-* findings are queued for the next EOD batch.
- [tina4stack/tina4-book#141](https://github.com/tina4stack/tina4-book/issues/141) — Middleware chapter issues. Comments filed so far: `[PY-10-01]`, `[PY-10-02]`, `[PY-10-03]`.

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
| PY-18-03 | Python | 18 | open | 2026-06-03 | Section 8 documents CLI flags `--file`, `--method`, `--verbose`, and (Section 9) `--cov`/`--cov-report` — **none of these flags exist**. `tina4 test --help` shows zero options besides `--help`. Either the flags need to be implemented in the CLI, or the docs need to be reduced to "run all tests" with no flag examples. |
| PY-18-04 | Python | 18 | open | 2026-06-03 | **Tina4's "inline testing framework" is actually a thin pytest wrapper, and the chapter misrepresents it as standalone.** Three concrete symptoms a reader hits: (a) Section 1 frames it as *"an inline testing framework. No external packages. No configuration."* — but it's pytest underneath, requiring pytest to be installed (see PY-18-02) and inheriting all of pytest's discovery/config/output behavior. (b) Section 2's claim *"Every `.py` file in that directory is auto-discovered when you run `tina4 test`"* is false — pytest's default requires `test_*.py` or `*_test.py` prefix; a file named `ch18_basic.py` is silently skipped (`collected 0 items`, no warning). (c) Every output example in the chapter (Sections 1, 2, 4, 8 PASS examples, 8 FAIL example) shows a fictional Tina4-styled format (`Running tests...`, `BasicTest`, `[PASS] test_addition`, `N tests, N passed, 0 failed (Ns)`). Actual output is raw pytest (`================ test session starts ================`, dots, `N passed in Ns`). Recommend: rewrite Section 1 to acknowledge `tina4 test` is a pytest wrapper, state that pytest's discovery rules / config / output format apply, and reframe Tina4's value-add as the `Test` base class (with `self.get`/`self.post`/etc.) plus the `assert_*` helpers. Either replace every output example with real pytest output, or implement a custom output formatter to match what the docs show. |
| PY-18-07 | Python | 18 | open | 2026-06-03 | **Section 4 (Testing ORM Models) is broken end-to-end as written.** A reader copy-pasting the snippet hits a cascade of failures: (1) `NameError: name 'Product' is not defined` — `Product` is used throughout but never imported; the chapter only imports `Test` and `assert_*` from `tina4_python.test`. (2) After adding `from src.orm.product import Product`, the next failure is `RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env` — but Section 4 explicitly promises *"By default, `tina4 test` uses a separate test database... created at `data/test.db` (SQLite) and is reset before each test run."* That default does not exist. `tina4 init` does not set `TINA4_DATABASE_URL`. The chapter frames the env var as optional ("If you want to use a different database for tests, set it in `.env`") but it's actually required. (3) Even with both fixed, the snippet relies on ORM APIs the section never documents: `Product.find(id)` returns model-or-None (contract not stated), `Product.where(sql, params)` returns the unusual tuple `(records, count)` (no explanation), `product.in_stock = True` assumes a boolean field type but Chapter 6 documents no `BooleanField`, and `save()`/`delete()` return semantics aren't specified anywhere. (4) Reset-between-runs claim is also unverified — even with a bound DB there's no evidence the framework wipes it. **Recommend: rewrite Section 4 to be self-contained.** Include the `Product` import, show the required `.env` line, define the Product model inline (or recap from Ch 6), and document each ORM method's contract. Or, alternatively, make the framework actually deliver the "auto test DB, just write a test" experience the section promises. |
| PY-18-08 | Python | 18 | open | 2026-06-03 | **Section 5 (Testing Routes) documents a test client API that doesn't match what the framework actually exposes.** Three concrete mismatches a reader hits when copy-pasting the snippet: (a) **Body argument is keyword-only, docs show positional.** Docs example: `self.post("/api/products", {"name": "Widget", ...})`. Actual signature: `Test.post(self, path: str, *, json=None, body=None, headers=None)` — the body must be passed as `json=` or `body=`, never positionally. Result: every `self.post(path, dict)` call in the chapter raises `TypeError: Test.post() takes 2 positional arguments but 3 were given`. Same applies to `self.put()` and `self.patch()`. (b) **`TestResponse` has no `status_code` attribute.** Section 5's "Response Object" subsection explicitly lists `resp.status_code` as a property. Real attribute is `resp.status`. Every `assert_equal(resp.status_code, 200, ...)` from the docs raises `AttributeError: 'TestResponse' object has no attribute 'status_code'`. (c) **Two undocumented convenience attributes exist.** Real `TestResponse` exposes `resp.json` (parsed JSON body) and `resp.text` — the chapter never mentions them. Readers manually do `json.loads(resp.body)` when `resp.json` would be simpler. Recommend: rewrite Section 5 to match the real API — (1) show keyword form `self.post("/api/products", json={...})`, (2) replace every `resp.status_code` with `resp.status`, (3) document `resp.json` and `resp.text` alongside the other Response Object attributes. |
| PY-10-01 | Python | 10 | open | 2026-06-04 | **Function-based middleware is documented but not implemented.** Section 3 ("Writing Custom Middleware") states *"Tina4 Python supports two styles of middleware: function-based and class-based"* and shows the canonical signature `async def fn(request, response, next_handler): ... result = await next_handler(request, response); return result`. The chapter has 8+ examples using this pattern across §3, §4, §6, §7, §8, §10 (`log_middleware`, `require_json`, `maintenance_mode`, `require_api_key`, `inject_user_agent`, `add_security_headers`, `api_key_middleware`, `auth_middleware`). Empirically the framework dispatcher (`server.py:1154-1185`) only handles class-based middleware — it iterates `dir(instance)` looking for attributes starting with `before_` / `after_`. A function passed to `@middleware(fn)` is stored in `route["middleware"]` but its body never executes because `dir(fn)` returns no `before_*` attributes. `grep -rn next_handler tina4_python/` returns 0 hits across the entire framework. Recommend either implementing the documented function-based path or removing §3 "Function-Based Middleware" + all `next_handler` examples from the chapter. Source: framework read + coworker incident (a developer wrote a JWT auth middleware following §3 verbatim; the body never ran, the route was silently unauthenticated). |
| PY-10-02 | Python | 10 | open | 2026-06-04 | **`@middleware(...)` silently disables the framework's built-in Bearer-token gate.** `router.py:689-704` — when `@middleware(...)` decorates a POST/PUT/PATCH/DELETE route, the decorator sets `route["auth_required"] = False` *"unless @secured() was explicitly set"*, on the assumption that "developer handles auth — disable built-in gate." This is undocumented in the chapter. Combined with PY-10-01, applying a function-based middleware intended to enforce auth produces a route with **zero authentication**: neither the custom middleware (never runs, per PY-10-01) nor the framework default (disabled by the decorator). A developer reading Ch10 alone would not know to add `@secured()` to restore the default gate. Recommend either documenting this behaviour explicitly in §4 ("The @middleware Decorator") with a security-implications callout, or making the auth-required default sticky unless explicitly overridden with `@noauth()`. |
| PY-10-03 | Python | 10 | open | 2026-06-04 | **Header-key casing mismatch in chapter examples.** `request.py:55` stores all incoming headers under lowercase keys: `req.headers[name.decode().lower()] = value.decode()`. So `request.headers.get("Authorization")` returns `None` — the key is actually `"authorization"`. Several chapter examples use mixed-case keys against this dict — §9 line 500 uses `"authorization"` (correct), §10 line 546 + §12 line 677 use `"X-API-Key"` (broken — returns None), §12 line 664 uses `"Authorization"` (broken — returns None). The chapter never states that `request.headers` is lowercase-keyed, nor mentions the convenience helpers: `request.header(name)` does case-insensitive lookup (`request.py:128`), and `request.bearer_token()` extracts the raw token (`request.py:132`). Recommend: (a) add a one-line callout in §3 or §8 that `request.headers` is lowercase-keyed, (b) normalise all chapter examples to either lowercase keys or the `request.header()` helper, (c) document `request.bearer_token()` as the canonical way to read the auth header. |
| PY-18-10 | Python | 18 | open | 2026-06-04 | **Section 5 "Response Object" subsection (`18-testing.md:384-393`) reference table doesn't match `TestResponse`.** The code block lists four properties — `resp.status_code`, `resp.body` (string), `resp.headers`, `resp.content_type`. Empirically verified against `tina4_python.test_client.TestResponse` (`__slots__ = ("status", "body", "headers", "content_type")`) via probe in `pypy/tests/test_ch18_response_object_probe.py`: (a) `resp.status_code` does not exist — the real attribute is `resp.status`. Probe `test_doc_resp_status_code_attribute_exists` fails with `AttributeError`. (b) `resp.body` documented as "string" — actual type is `bytes`. Probe `test_doc_resp_body_is_a_string` fails; `test_real_resp_body_is_bytes` passes. Side-effect: chapter's `json.loads(resp.body)` calls work by luck (since Python 3.6 `json.loads` accepts bytes), but any user who does `resp.body.startswith(...)` or string-concatenates the body will hit `TypeError`. (c) Helper methods `resp.json()` and `resp.text()` exist on the class but are absent from the reference table. (Note: PY-18-08(b) and PY-18-08(c) overlap with parts of this finding — they were lumped under the test-client signature filing before the "one code block = one finding" convention was set. PY-18-10 is the canonical row for the Response Object code block; PY-18-08 keeps the test-client methods block.) |

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
