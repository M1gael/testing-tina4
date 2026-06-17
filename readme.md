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

When you find a discrepancy, append a row to the Known Issues Log (in
[`findings-log.md`](findings-log.md)) using this six-column format:

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
- **Filed** — the upstream GitHub issue/PR link, or `no` if not yet filed.
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

