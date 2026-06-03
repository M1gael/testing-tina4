# Report: Proposed Layout for the "Getting Started" Top Section

**Page:** `https://tina4.com/python/01-getting-started.html`
**Scope:** Top portion of the page (everything before "Creating a New Project")
**Date:** 2026-06-03
**Status:** Draft — not yet filed

---

## Current state (what's wrong)

The existing page collapses three distinct concepts into one fuzzy "What You Need + Install" block:

- **External prerequisites** (Python, uv) — only one gets install instructions
- **The Tina4 CLI** (a Rust binary) — listed both as prereq #3 *and* given its own install section
- **The `tina4-python` framework package** — never named on the page; gets installed invisibly later

Side-effects of this muddle:

- Readers can't tell whether they're installing "the framework" or "a tool"
- `cargo install tina4` appears without Cargo as a listed prereq
- Python install is treated as assumed, but uv gets three platform-specific snippets

## Proposed layout — three sections that mirror the dependency chain

```
┌───────────────────────────────────────────────────┐
│  1. Prerequisites                                 │
│     ─ External tools you need before starting     │
│                                                   │
│     Python 3.12+  — the runtime that executes     │
│                     your app.                     │
│                     Install: python.org           │
│                                                   │
│     uv            — manages your project's deps;  │
│                     tina4 init uses it to add the │
│                     framework.                    │
│                     Install: docs.astral.sh/uv    │
│                                                   │
│     (Cargo / Rust — optional, only for            │
│      `cargo install tina4`. See rustup.rs)        │
└───────────────────────────────────────────────────┘
                       ↓
┌───────────────────────────────────────────────────┐
│  2. Install the Tina4 CLI                         │
│     ─ The Rust binary that scaffolds and runs     │
│       Tina4 projects. NOT the Python framework.   │
│                                                   │
│     macOS:    brew install tina4stack/tap/tina4   │
│     Linux:    curl -fsSL .../install.sh | bash    │
│     Windows:  irm .../install.ps1 | iex           │
│     Verify:   tina4 --version                     │
└───────────────────────────────────────────────────┘
                       ↓
┌───────────────────────────────────────────────────┐
│  3. Create your first project                     │
│     ─ Scaffolds the project + adds the framework  │
│                                                   │
│     tina4 init python my-app                      │
│     cd my-app                                     │
│     tina4 serve                                   │
│                                                   │
│     What just happened: tina4 init scaffolded     │
│     the project structure and added the           │
│     `tina4-python` package to your dependencies   │
│     via uv.                                       │
└───────────────────────────────────────────────────┘
```

## What the layout fixes

| Issue | How the layout fixes it |
|-------|-------------------------|
| **PY-01-01** — uv has 3 install snippets, Python has none | Both prereqs are listed with one-line link-outs. Consistent treatment. |
| **PY-01-02** — Tina4 CLI confused with framework | Sections 2 and 3 are visibly separate. Section 2 explicitly says *"NOT the Python framework."* Section 3 names the `tina4-python` package. |
| **PY-01-03** — cargo without Rust prereq | Cargo appears once, marked optional, tied to the specific install path that needs it. |
| **PY-01-04** — CLI listed as both prereq and install step | CLI is removed from prereqs entirely; lives only in section 2. |
| **PY-01-06** (partial) — framework name hidden | "What just happened" callout names the package by its PyPI name. |

## Design principles applied

1. **One concept per section.** Prereqs / tool / project — never mixed.
2. **Dependency chain top-to-bottom.** Language → tool → project, in that order.
3. **No install instructions for other people's tools.** Python and uv get link-outs only.
4. **Annotate every prerequisite.** Each entry has a "what it's for" line.
5. **Optional prereqs are labelled and scoped.** Cargo is parenthetical, tied to one install path.

## Acceptance criteria

- A reader who already has Python and uv can read sections 2→3 top-to-bottom, copy four commands, and reach a running Tina4 server without scrolling back.
- The page text mentions "Tina4 CLI" in exactly one heading scope and "tina4-python" in exactly one — and the page explicitly states they are different things.
- The Prerequisites section contains zero install commands — only link-outs.

---

## Logged Issues

The following findings on the Getting Started page top section were observed during
evaluation. IDs match the entries in the project's Known Issues Log (`readme.md`).

| ID | Status | Date Found | Description |
| :--- | :--- | :--- | :--- |
| PY-01-01 | open | 2026-06-03 | Getting Started page (`/python/01-getting-started.html`) provides `uv` install snippets for 3 platforms (macOS/Linux curl, Windows PowerShell, Cargo) but no Python install snippets — only a `python3 --version` check. Inconsistent: either both prereqs get install instructions or neither does. Recommend trimming `uv` snippets to a one-line link-out, matching how Python is handled. |
| PY-01-02 | open | 2026-06-03 | Getting Started page lists "the Tina4 CLI" as a prerequisite but never distinguishes it from the `tina4-python` framework package. A first-time reader can't tell whether they're installing a framework or a tool — the actual `tina4-python` package only surfaces buried in `uv` output during `tina4 init`. Recommend a two-sentence clarification up top: (1) `tina4` is the Rust CLI binary that scaffolds and runs projects; (2) each language has its own framework package (`tina4-python`, etc.) pulled in automatically by `tina4 init`. |
| PY-01-03 | open | 2026-06-03 | Getting Started page offers `cargo install tina4` as a CLI install option and describes the CLI as "Rust-based", but Cargo (Rust toolchain) is never listed as a prerequisite and there is no link to install it. A reader who picks the cargo path without Rust installed hits a wall with no doc support. Recommend either removing the cargo option (Homebrew/curl/PowerShell already cover all platforms) or moving it under an "Advanced / from source" section with a note about needing Rust ([rustup.rs](https://rustup.rs)). |
| PY-01-04 | open | 2026-06-03 | Getting Started page lists "Tina4 CLI" as prereq #3 in the "What You Need" list, then immediately below has a full "Installing the Tina4 CLI" section. The CLI is framed as both an external prerequisite and as something you install in step 1 — contradictory. Prereqs should be external deps only (Python, uv); the CLI belongs purely in the install section. Recommend removing item #3 from "What You Need" since the section directly below covers it. |
| PY-01-05 | open | 2026-06-03 | (Light suggestion.) The CLI/framework version decoupling is not explained anywhere in the docs. The `tina4` CLI is installed globally and updated by re-running the installer; the `tina4-python` framework is per-project and updated via `uv add tina4-python@latest`. Users have to derive this from first principles. Nice-to-have: a short "Versioning & updates" subsection on the Getting Started page covering (1) which version is which, (2) how to update each, (3) that they evolve independently. |
| PY-01-06 | open | 2026-06-03 | Docs only show the greenfield happy path (`tina4 init python my-app`) and never reveal the underlying package name or direct install commands. Consequences: (1) `uv` is listed as a hard prerequisite but the reader never types a `uv` command — the CLI invokes it invisibly. (2) The PyPI package name (`tina4-python`) does not match the framework's marketing name (`tina4`), and a Python dev's natural reflex `pip install tina4` fails with `No matching distribution found for tina4`. Import path is also `tina4_python`, not `tina4`. (3) A reader migrating an existing project, or troubleshooting, has no fallback path documented. Recommend a one-line note on the Getting Started page: *"On PyPI the package is `tina4-python` (imported as `tina4_python`). `tina4 init` adds it for you; if you're adding it to an existing project use `uv add tina4-python` (or `pip install tina4-python`)."* |
| PY-01-07 | open | 2026-06-03 | `tina4 install <lang>` subcommand naming is ambiguous: it installs the *language runtime* (Python itself), but a reader's intuition reads "install python = install the Python edition of Tina4." The framework install actually happens during `tina4 init python .` (as a per-project `uv add tina4-python`). Recommend either renaming `tina4 install` → `tina4 install-runtime` / `tina4 setup-runtime` for clarity, or making the help text explicit: *"Install a missing LANGUAGE runtime (not Tina4 itself — `tina4 init` installs the framework per project)."* |
| PY-01-08 | open | 2026-06-03 | `tina4 doctor` exposes a section titled **"Tina4 CLIs"** listing `tina4python`, `tina4php`, `tina4ruby`, `tina4nodejs`, `vite` and reporting them as "not found" with manual install commands (`pip install tina4-python` etc.). Three problems: (1) **The section title is wrong** — these are not CLIs in any meaningful sense, they are the framework packages themselves (`tina4-python` and friends). The CLI face each one exposes is plumbing the main `tina4` Rust CLI delegates to; users should never invoke `tina4python` directly. Better label: **"Language-Specific Frameworks"** — names what these actually are (the Tina4 framework, one per language) without exposing the plumbing CLI face. (2) **The "not found" warning is misleading** outside a project context — these packages are *expected* to be absent until `tina4 init` adds them to a project's `.venv`. (3) **The suggested install commands pollute global runtimes** when run outside a venv. Recommend: doctor should hide the section entirely outside a project, OR retitle it and add a note that the entries auto-install via `tina4 init`. The "four-names" confusion (`tina4`, `tina4-python`, `tina4python`, `tina4_python`) is largely caused by exposing this row as if it were a separate user-installable thing — it's not, it's the framework. |

## Issue coverage

| Issue | Resolved by this layout | Notes |
| :--- | :--- | :--- |
| PY-01-01 | ✅ Full | Both prereqs treated equally as link-outs. |
| PY-01-02 | ✅ Full | CLI and framework in separate sections, with explicit "NOT the Python framework" callout. |
| PY-01-03 | ✅ Full | Cargo marked optional, scoped to its specific install path. |
| PY-01-04 | ✅ Full | CLI removed from prereqs; lives only in section 2. |
| PY-01-05 | ❌ Out of scope | Versioning subsection would live elsewhere on the page. Not addressed by this layout. |
| PY-01-06 | ⚠️ Partial | "What just happened" line names `tina4-python`. A separate one-line note about manual install (`uv add tina4-python`) for existing projects is still needed. |
| PY-01-07 | ❌ Out of scope | CLI subcommand naming — not a doc-layout fix. Needs a help-text / rename change in the CLI itself. |
| PY-01-08 | ❌ Out of scope | `tina4 doctor` output — not part of the Getting Started page layout. Separate fix needed. |
