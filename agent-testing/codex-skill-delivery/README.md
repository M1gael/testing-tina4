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

| ID | Severity | Finding |
|---|---|---|
| CODX-01 | Bug | Broken code example in **all 7** `tina4 ai` context files |

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
