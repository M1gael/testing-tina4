# codex-skill-delivery — Do Tina4 Skills Work on OpenAI Codex?

**Question under test:** when a developer runs `tina4 ai` in a Tina4 project and then
works with **OpenAI Codex**, do the installed skills actually reach the model and
produce correct, framework-idiomatic code?

This is *not* a code-golf contest between models, and not a LOC comparison. It is a
delivery test: `tina4 ai` claims to install framework context for AI coding tools.
Codex is one of those tools. Does the mechanism work end to end?

---

## Why Codex specifically needs testing

`tina4 ai` writes seven context files, one per tool family:

| File | Consumed by |
|---|---|
| `AGENTS.md` | **Codex** |
| `CLAUDE.md` | Claude Code |
| `.clinerules` | Cline |
| `.cursorules` | Cursor |
| `.windsurfrules` | Windsurf |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `CONVENTIONS.md` | Aider |
| `.claude/skills/**` | Claude Code (skill loader) |

The size split is the crux:

- `AGENTS.md` — ~110 lines
- `.claude/skills/**` — ~7,400 lines across 3 skills + `references/`

`AGENTS.md` does **not** contain the API detail. It ends with a pointer block:

> `tina4-developer-python` — Read `.claude/skills/tina4-developer-python/SKILL.md`
> before building features.

So on Codex the skills only land **if Codex follows that pointer and opens the file.**
Claude Code loads `.claude/skills/` natively; Codex has no such loader. That single
behavioural difference is the primary thing this harness measures.

**Primary metric: does Codex read `.claude/skills/*/SKILL.md` unprompted?**
If it does not, `tina4 ai` is effectively shipping Codex a 110-line summary while
advertising a 7,400-line skill set.

> **Update 2026-08-04 — the premise above is half wrong, and the metric is now measurable
> directly.** Codex CLI 0.145.0 *does* have a native skill loader; it reads
> **`.agents/skills/`**, not `.claude/skills/`. And `codex debug prompt-input` renders the
> model-visible prompt as JSON, so delivery can be **byte-compared** instead of inferred
> from a reasoning trace. Measured on a fresh fixture: installing Tina4's skills changes
> the prompt by **zero bytes** (CODX-02). Full mechanism study, with the A/B/A measurement
> and the one-symlink fix, in [`codex/CODEX-CONTEXT-RESEARCH.md`](../../codex/CODEX-CONTEXT-RESEARCH.md).
> The `nosk`/`sk` arms below are still worth running — they measure whether a model *acts*
> on the context — but the delivery question itself is now settled without a model in the loop.

---

## Design: two arms, two directories

```
agent-testing/codex-skill-delivery/
├── README.md      ← this file
├── nosk/          ← arm A: bare `tina4 init`, no `tina4 ai`
└── sk/            ← arm B: `tina4 init` + `tina4 ai`
```

**Neither arm exists yet** — this file is the design, not a record of a run. Create
`nosk/` and `sk/` per the Protocol below before claiming any result.

**Separate directories, not git branches.** This is a hard rule, learned the
expensive way (see *Attempt 1*, below). `git checkout` **carries untracked files
across branches** — so an uncommitted run in one arm follows HEAD into the other and
can be committed under the wrong label. Branch-switching a single working tree
between arms is how attempt 1 destroyed itself. Two directories cannot cross-
contaminate.

Both arms are plain directories inside the `testing-tina4` repo. Neither gets its own
`.git` — everything is committed from the parent repo. This directory previously had a
nested `.git`, which hid its history from the parent entirely.

## Protocol

1. **Identical prompt to both arms**, recorded verbatim in `nosk/PROMPT.md` and
   `sk/PROMPT.md`. Same model, same reasoning effort, same task.
2. **Fresh state per arm** — no shared `data/*.db`, no shared `.env`, no shared
   `__pycache__`. A stale DB silently breaks migrations; a stale `.env` hands one arm
   the other's config contract.
3. **Commit each arm's output immediately when its run ends**, before touching the
   other arm. Untracked output is not evidence.
4. **One arm per commit.** Never a commit that touches both `nosk/` and `sk/`.
5. **Commit message names the arm and the model**, e.g.
   `test(codex-skill-delivery): nosk arm — codex gpt-5.4-mini medium`.
6. **Capture the reasoning trace**, not just the diff. Whether Codex opened
   `SKILL.md` is the finding; the code is secondary evidence.
7. **Record failures verbatim.** Framework errors go in the findings log below with
   the exact message.

## What to measure

| Measure | Why |
|---|---|
| Did Codex open `.claude/skills/*/SKILL.md`? | The primary question |
| Discovery behaviour | Reading `site-packages/tina4_python`, web searches = skills didn't land |
| Framework-idiom compliance | `service = {...}` auto-discovery, untouched `app.py`, `@noauth()` + in-handler auth, migrations vs inline DDL |
| Does it run? | Server boots, routes register, migrations apply, tests pass |
| Wall-clock + LOC | Supporting evidence only, never the headline |

Idiom compliance is the useful signal. A no-skills run reaches correct APIs
eventually by reading framework source — API correctness alone does **not** prove the
skills were used. Architecture does: hand-wiring `app.py` and writing a custom runner
loop is what no-skills looks like; trusting framework auto-wiring is what skills look
like.

---

## Findings

> **The rows moved 2026-08-13** to [`known-issues/ledger.md`](../../known-issues/ledger.md),
> re-coded `CLI-FW-05`..`CLI-FW-11` (CODX-01..07 in order). Original IDs are preserved in each
> row's note, since they are quoted in the study below. The mechanism study and the seven-tool
> scorecard stay here — the table below is kept as the study's own summary.

| ID | Severity | Finding |
|---|---|---|
| CODX-01 | Bug | Broken code example in **all 7** `tina4 ai` context files |
| CODX-02 | Bug | Skills install to `.claude/skills/` only — **invisible to Codex**, which reads `.agents/skills/` |
| CODX-03 | Bug | `tina4 ai` dies with unhandled `EOFError` when stdin is not a TTY |
| CODX-04 | Bug | Rust CLI `--all` / `--force` flags not forwarded to the Python `ai` handler |
| CODX-05 | Cosmetic | `tina4 ai` creates an empty `.cursor/` directory it never writes into |
| CODX-06 | Bug | **`.cursorules` is a typo** — Cursor reads `.cursorrules` (two r's) or `.cursor/rules/*.mdc`. Cursor receives nothing |
| CODX-07 | Gap | `CONVENTIONS.md` is the right name for Aider but is **not auto-loaded** — needs `--read` / `/read` / `.aider.conf.yml`, which nothing tells the user |

All verified against **tina4 CLI 3.8.64 / tina4-python 3.13.94 / codex-cli 0.145.0**
on the `codex/` fixture, 2026-08-04.

### Per-tool delivery scorecard

`tina4 ai` writes 7 context files + a skill tree. Whether each lands:

| Tool | `tina4 ai` writes | Tool actually reads | Verdict |
|---|---|---|---|
| Claude Code | `CLAUDE.md` + `.claude/skills/**` | same | **works** — verified: a Claude Code session in this fixture lists all three tina4 skills |
| OpenAI Codex | `AGENTS.md` | `AGENTS.md` ✓, skills from `.agents/skills/` ✗ | **half** — prose lands, 158 KB of skills do not (CODX-02) |
| GitHub Copilot | `.github/copilot-instructions.md` | same | path correct — *untested here* |
| Cline | `.clinerules` | `.clinerules` | path correct — *untested here* |
| Windsurf | `.windsurfrules` | `.windsurfrules` (legacy name) | path correct — *untested here* |
| Aider | `CONVENTIONS.md` | correct name, **needs `--read`** | **gap** (CODX-07) |
| Cursor | `.cursorules` | `.cursorrules` / `.cursor/rules/*.mdc` | **misses entirely** (CODX-06) |

Only **Claude Code** receives the skills. Every other tool gets a 2–3 KB summary of a
2961-line skill set — and all 7 summaries carry the CODX-01 broken example.

### CODX-06 — `.cursorules` reaches no tool

`tina4_python/ai/__init__.py:22` hardcodes `"context_file": ".cursorules"` — one `r`.
Cursor's legacy filename is `.cursorrules` and its current one is `.cursor/rules/*.mdc`.
`.cursorules` matches neither, so the file is inert. Also referenced at
`ai/__init__.py:254` and `tina4_python/CLAUDE.md:1451`, so a fix has three sites.

The same table entry already declares `"config_dir": ".cursor"` and creates that directory
(CODX-05), so the correct target is one line away: write `.cursor/rules/tina4.mdc` instead,
which is Cursor's current convention and supports conditional loading via frontmatter globs.

### CODX-07 — `CONVENTIONS.md` is not auto-loaded by Aider

Aider reads it only when passed explicitly: `aider --read CONVENTIONS.md`, `/read
CONVENTIONS.md` in-session, or a persistent `read: CONVENTIONS.md` in `.aider.conf.yml`.
`tina4 ai` writes the file and prints `✓ Installed CONVENTIONS.md`, implying it is active.
Writing `.aider.conf.yml` with the `read:` entry, or printing the required flag, would close
this.

### Note — the authors already know about `.agents/`

`ai/__init__.py:34-37` reasons about Google Antigravity and concludes it reads `AGENTS.md`,
adding: *"If you also want Antigravity-specific tuning, write to `.agents/rules/tina4.md` by
hand."* So `.agents/` is on the authors' radar as a rules location; the connection to
`.agents/skills/` as Codex's **skill** root was simply never made.

### CODX-01 — doubled braces in the canonical route example

`tina4 ai` emits an unrendered template escape, so the route example it teaches every
AI tool is broken Python:

```python
return response({{"users": []}})
return response({{"created": request.body["name"]}}, 201)
```

`{{...}}` is a set containing a dict, not a dict literal:

```
TypeError: cannot use 'dict' as a set element (unhashable type: 'dict')
```

Should be `response({"users": []})`. Present twice in each of `AGENTS.md`,
`CLAUDE.md`, `CONVENTIONS.md`, `.clinerules`, `.cursorules`, `.windsurfrules`,
`.github/copilot-instructions.md` — verified in `tina4-python 3.13.92`. Any agent
copying the pattern emits code that raises at runtime.

**Still present in `tina4-python 3.13.94`** (re-verified 2026-08-04): all 7 files, 2
occurrences each, unchanged.

### CODX-02 — skills install where Codex cannot see them

`tina4 ai` writes the skill tree to `.claude/skills/` (project *and* `~/.claude/skills/`
global). Codex CLI 0.145.0 has a native skill loader, but it scans `.agents/skills/` —
`$CWD`, `$CWD/..`, `$REPO_ROOT`, `$HOME` — plus `/etc/codex/skills` and the bundled
`$CODEX_HOME/skills/.system/*`. `.claude/skills` is in none of those.

Measured with `codex debug prompt-input`, which renders the model-visible prompt as JSON.
Same prompt, developer-message length as the metric:

| State | Developer msg | Tina4 skills in catalogue |
|---|---|---|
| after `tina4 init python .` | 14279 | 0 |
| after `echo all \| tina4 ai` | **14279** | **0** |
| after `ln -s ../.claude/skills .agents/skills` | 16412 | 3 |
| symlink removed again | 14279 | 0 |

The first two rows are **byte-identical** — installing the skills changed the prompt by
zero bytes. On Codex, `tina4 ai` delivers a 3.2 KB `AGENTS.md` and **0 of 158 KB of
skills** (`SKILL.md` bodies 47632 + 47211 + 63920, plus 15 `references/*.md`).

Corroborated on the same machine: the `caveman*` skills are real directories in
`~/.agents/skills/` symlinked *into* `~/.claude/skills/`, and Codex lists all seven. The
three Tina4 skills are real directories in `~/.claude/skills/` with no `.agents`
counterpart, and Codex lists none. Only the directory name differs.

The `<!-- tina4-skills:start -->` pointer block in `AGENTS.md` is not equivalent: it is
prose in a user message, so there is no description-based implicit triggering, no
`$SkillName` invocation, and no enforcement that the body is read before work begins.

Fix is one symlink per project (`mkdir -p .agents && ln -s ../.claude/skills
.agents/skills`); better still, make `.agents/skills/` the real location and point
`.claude/skills` at it, since `.agents/skills` is the cross-tool convention. Full study:
[`codex/CODEX-CONTEXT-RESEARCH.md`](../../codex/CODEX-CONTEXT-RESEARCH.md).

### CODX-03 — `tina4 ai` crashes on non-TTY stdin

Piping or redirecting stdin (CI, scripted setup, an agent shell) produces a traceback
rather than a message:

```
  Select (comma-separated, or 'all'): Traceback (most recent call last):
  File ".../tina4_python/ai/__init__.py", line 173, in show_menu
    return input("  Select (comma-separated, or 'all'): ").strip()
EOFError: EOF when reading a line
```

Any non-interactive `tina4 ai` fails. Workaround: `echo all | tina4 ai`.

### CODX-04 — `--all` / `--force` are not forwarded to the Python handler

`tina4 ai --help` (Rust CLI) documents `--all` ("Install context for ALL known AI tools")
and `--force`. `tina4 ai --all` still renders the interactive menu and still calls
`show_menu(".")`, so it hits CODX-03 and installs nothing. The flags are parsed by the
Rust CLI and dropped before reaching `tina4_python/cli/__init__.py::_ai`.

### CODX-05 — empty `.cursor/` directory

`tina4_python/ai/__init__.py:22` declares `"config_dir": ".cursor"` for the Cursor entry.
The directory is created but nothing is ever written into it — Cursor's context goes to
`.cursorules` in the project root. Leaves an empty `.cursor/` in every project.

---

## Attempt 1 (2026-07-28/29) — void, do not cite

An earlier attempt in this directory produced no usable result. Recorded so the
failure modes are not repeated:

- Both arms ran in **one working tree**, switched by `git checkout`. Untracked output
  followed HEAD, and one run's code was committed onto the other arm's branch under
  that arm's label.
- A later agent hard-reset both branches, destroying five commits, then cherry-picked
  one arm's implementation onto the other branch and wrote audit reports crediting
  each arm with the other's work. LOC tables in those reports were fabricated.
- Net: two implementations existed, neither reliably attributable. Both branches and
  all recovered artefacts were deleted on 2026-07-29 to start clean.

Lesson encoded as protocol rules 3–5 and the two-directory layout above.
