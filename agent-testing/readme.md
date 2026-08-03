# `agent-testing/`

Evaluations of **whether AI coding tools can build with Tina4** — a different question
from the rest of this repo. `documentation-testing/` asks *do the docs work for a human
reader*; this directory asks *does the framework's AI-facing context work for a model*.

The subject under test is the delivery mechanism (`tina4 ai`, the installed skills, the
`.tina4/` agent) — never the model's raw talent. A model failing a task is only a finding
when the cause traces to context Tina4 shipped, or failed to ship.

| Dir | Question under test | State |
|---|---|---|
| `codex-skill-delivery/` | Does `tina4 ai` context actually reach **OpenAI Codex**? Codex has no `.claude/skills/` loader, so the skills land only if it follows the pointer in `AGENTS.md` and opens `SKILL.md` itself. | Design only — neither arm run |
| `ai-context-delivery/` | Scaffolded Tina4 Python app carrying all seven `tina4 ai` context files (`AGENTS.md`, `CLAUDE.md`, `.clinerules`, `.cursorules`, `.windsurfrules`, `.github/copilot-instructions.md`, `CONVENTIONS.md`) plus `.claude/skills/**`. The fixture the delivery tests point at. | Scaffolded, `src/routes/` empty |
| `small-model-tiers/` | Can the **built-in `.tina4/` agent driving a small local model** (Qwen 27B–36B) build working Tina4 apps across three difficulty tiers? | Level 1 run; levels 2–3 not built |

## Relationship to the harness protocol

**These evaluations are outside the doc-fidelity Protocol.** They do not walk chapters,
so their observations carry no quoted-documented-claim trace and are **not** eligible for
the Known Issues Log in `findings-log.md` as-written (`documentation-testing/readme.md`
rules 11–12: strict traceability, no test rigging).

Observations that surface here land in [`unverified-leads.md`](unverified-leads.md). To
promote one into the KI Log it must first be **re-tested inside `documentation-testing/`
against a quoted claim from a real chapter** and earn a `PY-NN-NN` ID — or be filed
upstream and tracked as `BH-<n>`. Nothing is promoted on the strength of an agent run alone.

## Conventions

- **One directory per arm, never git branches.** `git checkout` carries untracked files
  across branches, which silently attributes one arm's output to the other. See the
  cautionary write-up in `codex-skill-delivery/README.md` → *Attempt 1*.
- **No nested `.git`.** Everything commits from the parent repo. A nested repo hides its
  history from `testing-tina4` entirely.
- **The reasoning trace is the evidence**, not the diff. Whether the model opened
  `SKILL.md` is the finding; the code it produced is secondary.
- **Record failures verbatim** — exact error text, model name, and reasoning effort.
