# Suggested Fixes

**Not a bug log.** Confirmed issues live in [`ledger.md`](ledger.md). This file is the long-form `FIX-NN` proposals that the ledger's Suggested-fix column points at (`→ FIX-NN`).

Each fix tags one or more issue IDs and includes rationale, concrete edits, and acceptance criteria.

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

### FIX-04 — `tina4 test` output formatter (relocated)

Speculative UI spec for a `tina4 test` output formatter (per-file bar, right-anchored status, bottom printer line). **PY-18-04 is CLOSED (fixed 3.13.4 — `tina4 test` cleanly wraps pytest);** the maintainer never requested this formatter. Full spec relocated to [`notes/FIX-04-test-output-formatter.md`](notes/FIX-04-test-output-formatter.md).

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

---

### FIX-07 — Lead the Quick Reference with an Installation / Update section; rename it "Getting Started / Quick Reference"

**Tags:** PY-01-10 (primary); relates to PY-01-09, PY-01-01
**Page:** the existing **Quick Reference** page — to be renamed **"Getting Started / Quick Reference"**. The broken landing quickstart (`/python/#installation`, PY-01-10) links here instead of carrying its own commands. Pattern repeats per language.
**Thread:** [#143](https://github.com/tina4stack/tina4-book/issues/143) — Tina4 Chapter Quick Reference (PY-01-10 report filed here 2026-06-19).
**Status:** proposed

**The problem in one sentence.** Install commands are scattered (a four-line quickstart on the landing page, a fuller flow in the Getting Started chapter) and no single place lists *every* command a from-zero reader runs, in order — and the landing quickstart is the broken one (PY-01-10): it shows `pip install tina4-python → tina4 init → cd → tina4 serve`, never installs the `tina4` CLI, so a brand-new reader dies at step 2 with `'tina4' is not recognized`.

**Proposed structure.** Don't add a new page. Make the existing **Quick Reference** the canonical home: add an **Installation / Update** block as its **first section**, and rename the page **"Getting Started / Quick Reference"** so a newcomer recognizes it as the entry point. A reader who has *only their OS* — no project, no CLI, no framework — follows that first section top-down and reaches a running server. Headings follow the dependency chain (Editorial principle 4); the CLI and the framework package stay in separate sub-sections (principle 3); other tools link out, never embedded (principle 1).

```
## Prerequisites   (Tina4 links out — it does not bundle these)
   Python 3.12+  — the runtime that executes your app.   → python.org/downloads
   uv            — manages your project's dependencies.   → docs.astral.sh/uv

## Install the Tina4 CLI   (one Rust binary; serves all four languages)
   What it is:   the tool that scaffolds and runs projects. NOT the Python
                 framework — that lives inside your project (next section).
   macOS:        brew install tina4stack/tap/tina4
   Linux/macOS:  curl -fsSL https://raw.githubusercontent.com/tina4stack/tina4/main/install.sh | bash
   Windows:      irm https://raw.githubusercontent.com/tina4stack/tina4/main/install.ps1 | iex
   Verify:       tina4 --version

## Create and run a project
   tina4 init python my-app
   cd my-app
   tina4 serve            # → http://localhost:7145

## Update   (returning users)
   tina4 update                       # upgrade the CLI
   uv pip install -U tina4-python     # upgrade the framework, inside a project
```

**What changes elsewhere.**

- **Landing "Get Started" becomes the *what*, not the *how*** — what Tina4 is, what you need (concepts), and "pick a language." It links to the Installation / Update section of **Getting Started / Quick Reference** instead of carrying its own command list.
- **Delete the broken four-line quickstart** (`pip install tina4-python → tina4 init → …`) from the landing page. Its `pip install tina4-python` lead is the trap: it yields the framework package + the `tina4python` script, not the `tina4` CLI the next line calls (and that script then crashes on a cp1252 Windows console — PY-01-09).
- **Bare `pip install tina4-python` appears only in the separate, clearly-labelled "Manual Setup (No CLI)" route** — the one that ends in `python app.py` and never invokes `tina4`. It must not lead any CLI-based flow.
- **The Getting Started chapter narrative references Getting Started / Quick Reference** rather than re-listing the commands, so setup commands live in exactly one place.

**Relationship to FIX-01.** FIX-01 restructures the Getting Started *chapter* in place (Prerequisites / Install the CLI / Create project). FIX-07 puts those same canonical commands in the first section of **Getting Started / Quick Reference** so they exist once and other pages link to them. Both share the three-concept model; FIX-07 supersedes the *install portion* of any page that currently re-lists commands.

**Acceptance criteria.**

- A reader with only their OS installed follows the Installation / Update section top-down and reaches a running server — no scroll-back, no missing-tool error, no missing-command error (`tina4 init` never runs before the CLI is installed).
- No page presents a CLI-based flow whose first command is `pip install tina4-python`. That command appears only in the "Manual Setup (No CLI)" route.
- The words "Tina4 CLI" and "tina4-python" each live in one heading scope, with an explicit "these are different things" call-out.
- An Update sub-section lets a returning user upgrade the CLI (`tina4 update`) and the framework package, each labelled for its target.
- The Quick Reference page is titled **"Getting Started / Quick Reference"** with Installation / Update as its first section; the landing page's old four-line quickstart no longer exists and links here instead.
