# How OpenAI Codex reads context files — and what that means for Tina4 skills

**Date:** 2026-08-04
**Codex CLI:** `codex-cli 0.145.0` (`~/.codex/packages/standalone/current/bin/codex`)
**Codex model config:** `gpt-5.4-mini`, `model_reasoning_effort = "medium"` (`~/.codex/config.toml`)
**Tina4 CLI:** `3.8.64` · **tina4-python:** `3.13.94`
**Fixture:** this directory — `tina4 init python .` then `echo all | tina4 ai`

This is a **mechanism study**, not an agent run. No model was asked to build anything. Every
claim below was measured against the Codex binary and its own prompt dump, so it holds
regardless of how any given model behaves on a given day.

---

## The instrument: `codex debug prompt-input`

Codex 0.145.0 ships a subcommand that renders the exact model-visible prompt as JSON:

```bash
codex debug prompt-input "build a users route" > prompt.json
```

That makes context delivery **directly measurable** instead of inferred from reasoning
traces. Every number in this document comes from diffing that output. This is the single
most useful discovery here: the `codex-skill-delivery` arm no longer has to guess whether
the skills landed — it can byte-compare the prompt.

The dump is a 3-element list:

| # | Role | Contains |
|---|---|---|
| 0 | `developer` | `<skills_instructions>` (skill catalogue), `<permissions instructions>`, `<apps_instructions>` |
| 1 | `user` | `<recommended_plugins>`, **`<INSTRUCTIONS>` ← AGENTS.md goes here**, `<environment_context>` |
| 2 | `user` | the actual prompt |

Note the split: **AGENTS.md is a user message; the skill catalogue is a developer message.**
Two independent prose channels, and Tina4 currently reaches only one of them. A third
channel — MCP, which carries *executable* tools rather than prose and so never appears in
this dump — is covered further down.

---

## Channel 1 — `AGENTS.md` (works)

### Discovery and merge order

Codex walks from the global config down to `cwd`, taking **at most one file per directory**,
and concatenates them root-first joined by blank lines. Deeper files override shallower ones.

1. `$CODEX_HOME/AGENTS.override.md`, else `$CODEX_HOME/AGENTS.md` (i.e. `~/.codex/`)
2. `<git-root>/AGENTS.override.md`, else `<git-root>/AGENTS.md`
3. each intermediate directory between git root and `cwd`, same override-then-plain rule
4. `<cwd>/AGENTS.override.md`, else `<cwd>/AGENTS.md`

Config keys present in this build (confirmed in the binary's symbol strings):
`project_doc_max_bytes` (default 32 KiB, combined — truncates past that),
`project_doc_fallback_filenames`, `model_instructions_file`,
`experimental_instructions_file`.

### Measured result

Tina4's `AGENTS.md` is **3217 bytes**. It arrives whole inside `<INSTRUCTIONS>` (block length
3185 chars — the delta is the trimmed wrapper). Well under the 32 KiB ceiling. No truncation,
no competition.

`project_doc_fallback_filenames` is worth knowing about: it is the supported way to make
Codex treat `CLAUDE.md` as an AGENTS.md-class file. Tina4 doesn't need it (it writes a real
`AGENTS.md`), but it is the escape hatch if a project only has `CLAUDE.md`.

### Trap for this repo specifically

`git rev-parse --show-toplevel` from here is `/var/home/work/gitdir/testing-tina4` — the
harness repo, not this project. If anyone ever drops an `AGENTS.md` at the harness root, it
gets **prepended to every arm's context**, silently. Any `nosk`/`sk` comparison would be
contaminated and the diff would look like a framework change. Keep the harness root free of
`AGENTS.md`, or run arms outside the harness repo.

---

## Channel 2 — Skills (does **not** work)

### Codex has a native skill loader. It is not Claude's.

The premise in `agent-testing/codex-skill-delivery/README.md` — *"Codex has no
`.claude/skills/` loader"* — is right about `.claude/`, but the conclusion drawn from it is
now wrong. Codex 0.145.0 has a **first-class skill system** with its own root, its own
injected catalogue, and its own progressive-disclosure contract. Feature flags in this build:

```
skill_search                    stable   true
skill_mcp_dependency_install    stable   true
plugins                         stable   true
hooks                           stable   true
```

Scan order (documented, and consistent with what this fixture produced):

1. `$CWD/.agents/skills`
2. `$CWD/../.agents/skills`
3. `$REPO_ROOT/.agents/skills`
4. `$HOME/.agents/skills`
5. `/etc/codex/skills` + bundled OpenAI skills (`$CODEX_HOME/skills/.system/*`)

Symlinked skill folders are followed. `.claude/skills` appears **nowhere** in that list.

Tina4's `SKILL.md` files are otherwise **fully conformant** — each opens with valid YAML
frontmatter carrying `name` and a folded-scalar `description`, which is exactly what Codex's
loader needs, and the descriptions render correctly in the catalogue once the directory is
reachable (state C below). Nothing about the skills' *content or format* is the problem. The
directory name is the entire defect.

Corroborating evidence from the prompt dump's own permission profile — Codex pre-grants read
access to exactly two project dot-directories, and `.claude` is not one of them:

```xml
<entry access="read"><path>/var/home/work/gitdir/testing-tina4/codex/.agents</path></entry>
<entry access="read"><path>/var/home/work/gitdir/testing-tina4/codex/.codex</path></entry>
```

### How a skill is delivered

Codex injects **name + description + file locator only**, inside `<skills_instructions>` in
the developer message — capped at "at most 2% of the model's context window, or 8,000
characters when the context window is unknown." The full `SKILL.md` is read on demand, and
the contract is strict about it:

> After deciding to use a skill, the main agent must read its `SKILL.md` completely before
> taking task actions. […] If a read is truncated or paginated, continue until EOF.

and

> Do not delegate reading, summarizing, or interpreting skill instructions to a subagent.

So the delivery model matches Claude Code's: descriptions always in context, body on
selection. The only difference is the directory name.

### Measured result: zero delivery

A/B/A on this fixture, same prompt each time, developer-message length as the metric:

| State | `.agents/skills` present | Developer msg length | Tina4 skills in catalogue |
|---|---|---|---|
| A — after `tina4 init`, before `tina4 ai` | no | **14279** | 0 |
| B — after `echo all \| tina4 ai` | no | **14279** | **0** |
| C — after `ln -s ../.claude/skills .agents/skills` | yes | **16412** | **3** |
| A′ — symlink removed | no | **14279** | 0 |

**State A and state B are byte-identical.** Installing Tina4's skills changed the
model-visible prompt by exactly zero bytes. `tina4 ai` reports:

```
✓ Installed .claude/skills/tina4-developer-python  (project + global)
✓ Installed .claude/skills/tina4-js  (project + global)
✓ Installed .claude/skills/tina4-maintainer  (project + global)
```

…and Codex sees none of it. The global copy in `~/.claude/skills/` is equally invisible: the
user-level root Codex scans is `~/.agents/skills`.

Independent confirmation from this machine's pre-existing setup — the `caveman*` skills are
real directories in `~/.agents/skills/` that are **symlinked into** `~/.claude/skills/`.
Codex lists all seven of them. The three Tina4 skills are real directories in
`~/.claude/skills/` with no `.agents` counterpart. Codex lists none. Same machine, same
session, opposite outcome, and the only variable is the directory name.

So the headline for the delivery test:

> On Codex, `tina4 ai` delivers a 3.2 KB `AGENTS.md` summary and **0 of 158 KB of skills**
> (`SKILL.md` bodies: 47632 + 47211 + 63920 bytes, plus 15 `references/*.md` files,
> 7394 lines total).

### The pointer in AGENTS.md is not a substitute

`AGENTS.md` ends with a `<!-- tina4-skills:start -->` block naming the three skills and their
`.claude/skills/*/SKILL.md` paths. Those paths are real and readable, so a model that follows
the pointer does get the content. But this is a **prose request inside a user message**,
competing with the task, not a registered capability. It differs from real skill delivery in
every way that matters:

- no entry in `<skills_instructions>`, so no description-based implicit triggering
- no "must read completely before taking task actions" enforcement
- no `$SkillName` invocation, no skill selector entry
- no protection against a subagent doing the reading (which the skills contract forbids)
- discovery depends on the model choosing to spend three file reads before starting work

Whether a given model follows it is a coin flip and a per-model, per-effort property. Whether
the skill is *registered* is a fact. Right now the fact is: not registered.

---

## The fix

One symlink per project, and it is measurably sufficient — that is state C above:

```bash
mkdir -p .agents && ln -s ../.claude/skills .agents/skills
```

Codex resolves through the symlink and reports the real paths
(`…/codex/.claude/skills/tina4-developer-python/SKILL.md`), so there is no duplicate-path
confusion and no second copy to keep in sync.

### Options for `tina4 ai`, in order of preference

1. **Symlink `.agents/skills` → `.claude/skills`** when installing Codex context. One
   filesystem object, no duplication, no drift. Needs a copy fallback on Windows without
   developer mode, where `os.symlink` raises `OSError`.
2. **Write skills to `.agents/skills/` as the primary location and symlink `.claude/skills`
   at it.** Strictly better long-term: `.agents/skills` is the cross-tool convention that
   Claude Code, Cursor, Gemini CLI and Copilot also read, so one real directory serves every
   tool and `.claude/skills` becomes the compatibility shim rather than the source.
3. **Copy the tree to both.** Works everywhere, but 158 KB duplicated per project and two
   copies to keep in step across `tina4 ai --force` runs.

Global install should mirror this: `~/.agents/skills/tina4-*` alongside `~/.claude/skills/`.
Per-skill symlinks there, not a directory-level one — `~/.agents/skills/` may already hold
other tools' skills (it does on this machine).

### One caveat before adopting a global install

Codex injects every discovered skill's description into **every session**, tina4 project or
not. The three Tina4 descriptions are 736 + 737 + 657 = 2130 chars, against a stated budget
of ~8000 chars or 2% of context. Adding them globally spends that on unrelated work. The
per-project symlink is the better hygiene, and it is also what `tina4 ai` is already
positioned to do since it already writes a project-local `.claude/skills/`.

### Secondary: split the large `SKILL.md` bodies

Codex reads a selected `SKILL.md` **to EOF**, so selection costs the whole file.
`tina4-maintainer/SKILL.md` is 63920 bytes (~10k words) and
`tina4-developer-python/SKILL.md` is 47632 bytes. Codex's own skill-authoring guidance sets
the threshold at 10k words and says to include grep patterns for anything larger. All three
skills already have `references/` subdirectories, so the structure exists — the top-level
bodies are just carrying more than they need to. Not a delivery bug; a token-efficiency one
that only starts to bite once delivery works.

---

---

## Behavioural probe — inconclusive, and why

Delivery is settled by measurement. Whether registration *changes what a model does* is a
separate question, and one attempt at it did **not** produce a usable answer. Recorded so it
isn't re-run blind.

Two disposable copies of this fixture in a scratch dir, identical prompt with no mention of
skills — *"Add a GET /widgets route that returns a JSON list of widgets. Follow this project's
conventions."* — `gpt-5.4-mini`, medium effort. `sk` had the `.agents/skills` symlink; `nosk`
did not.

| | `nosk` | `sk` |
|---|---|---|
| Reached `SKILL.md` | yes, at step 5 — `rg --files` discovery pass, read `AGENTS.md`, then `sed -n '1,240p'` | yes, at step 1 — `sed -n '1,220p'` straight from the catalogue's absolute path |
| Shell commands | 7 | 17 |
| Tokens | 14846 | 42680 |
| Output | `src/routes/widgets.py` + `tests/test_widgets_route.py`, correct decorator order, no doubled braces | **nothing — killed mid-run** |

```
ERROR: You've hit your usage limit. Upgrade to Plus to continue using Codex, or try again at Aug 27th, 2026 2:04 PM.
```

**The `sk` arm died on an account quota, not on the experiment.** Before dying it was reading
framework source at length — which is the arm README's stated signature for *skills didn't
land* — but that reading is confounded by whatever pushed it to 42k tokens, so nothing can be
attributed. No conclusion either way. The Codex account is rate-limited until **2026-08-27
14:04**, so this cannot be re-run before then.

Two things the pair *does* establish, independent of the quota:

1. **The `AGENTS.md` pointer worked in `nosk`.** It cost a discovery detour (an `rg --files`
   pass, then `AGENTS.md`, then the file) and arrived at step 5 instead of step 1, but it did
   arrive, and the resulting code was clean and idiomatic. So "the pointer is unreliable"
   remains an untested worry, not a demonstrated failure — the honest claim is narrower:
   the skill is not *registered*, and discovery is left to the model's judgement.
2. **Neither arm read `SKILL.md` to EOF.** Both stopped at ~220–240 lines of a **913-line**
   file (~24%), despite the skills contract's explicit *"read completely […] continue until
   EOF"*. That is a genuine argument for splitting the top-level bodies into `references/` —
   see the token-efficiency note above — and it applies to the registered path too.

---

## Channel 3 — MCP (untouched by `tina4 ai`, and a different kind of thing)

The two channels above carry **prose**: procedures, conventions, domain knowledge, loaded as
text. Anything that has to *execute* — run a query, introspect a live schema, call an API —
goes through MCP instead, which Codex integrates as native tool calls rather than
instructions.

### Codex side

```bash
codex mcp add <NAME> --url <URL> [--bearer-token-env-var <ENV_VAR>]   # streamable HTTP
codex mcp add <NAME> [--env K=V]... -- <COMMAND>...                   # stdio
codex mcp list | get | remove | login | logout
```
Servers persist into `~/.codex/config.toml` under `[mcp_servers.*]`. (Note: `opencode.json`
is a *different* tool's config file, not Codex's — Codex reads `~/.codex/config.toml`, or
`$CODEX_HOME/config.toml`.)

### Tina4 side — it exists, but it is not a knowledge server

`tina4_python/mcp/__init__.py` (628 lines) ships a full MCP implementation. Two things to be
clear about before treating this as a skills-delivery route:

**It is an app-exposure server, not a framework-knowledge server.** Its documented purpose is
letting *the developer's app* publish *its own* tools:

```python
from tina4_python.mcp import McpServer, mcp_tool, mcp_resource

mcp = McpServer("/my-mcp", name="My App Tools")

@mcp_tool("lookup_invoice", description="Find invoice by number")
def lookup_invoice(invoice_no: str):
    return db.fetch_one("SELECT * FROM invoices WHERE invoice_no = ?", [invoice_no])
```

So it does **not** substitute for the skills in Channel 2 — those are conventions and
workflows, which are prose by nature. MCP is complementary, not an alternative path for the
same payload.

**It is HTTP/SSE and in-process**, so it only exists while the app is running:

| Property | Value |
|---|---|
| Enable gate | `TINA4_MCP` env override; else `TINA4_DEBUG=true`; else off |
| Port | `TINA4_MCP_PORT`, default framework port **+ 2000** → `9145` |
| Transport | HTTP + SSE on a mounted path (`McpServer("/my-mcp")`) |
| Per-request gate | `is_request_allowed()` checks the real socket peer for loopback, or a valid token |

This fixture's `.env` sets `TINA4_DEBUG=true`, so the built-in dev tools are enabled here by
default. Worth knowing what they are: **DB query/execute and file read/write**. The
per-request loopback check (added in 3.13.40, after an earlier version gated on the
*configured* host name instead of the caller) is the only thing standing between those tools
and a remote caller on a box bound to `0.0.0.0`. Do not register this against a
non-loopback URL without a token.

No `tina4 mcp` CLI subcommand exists — the server is a runtime feature of a serving app, so
Codex can only reach it while `tina4 serve` is up. That makes it unsuitable as the primary
context channel (Codex would see zero tina4 tools in a cold repo) but a genuine addition on
top of it.

### Verdict for `tina4 ai`

`tina4 ai` currently touches Channel 1 only. Channel 2 is a one-symlink fix. Channel 3 is a
separate feature request — *offer to register the app's MCP endpoint with detected tools* —
and should be judged on its own merits, not folded into the skills fix.

---

## Other Codex surfaces worth knowing about

- **Plugins** — `codex plugin add/list/marketplace`. A plugin is a directory with
  `.codex-plugin/plugin.json` plus optional `skills/`, `.mcp.json`, `agents/`, `commands/`,
  `hooks.json`. The loader also accepts **`.claude-plugin/plugin.json` and
  `.cursor-plugin/plugin.json`** manifests, so one bundle can target all three tools. This is
  the most promising long-term distribution channel for Tina4: a single plugin carries the
  skills *and* the MCP registration *and* hooks, installable by name, versioned, with no
  per-project file writes at all.
- **Hooks** — `hooks` is stable in this build; `hooks.json` ships inside plugins.
- **`AGENTS.override.md`** — a local, higher-precedence layer, useful for arm-specific
  overrides during testing without touching the file `tina4 ai` generates.

---

## `tina4 ai` defects observed while building this fixture

Recorded as `CODX-*` in `agent-testing/codex-skill-delivery/README.md`. Summary:

- **CODX-01** (pre-existing) — doubled-brace route example, `response({{"users": []}})`.
  **Still present in tina4-python 3.13.94**, in all 7 context files, 2 occurrences each.
- **CODX-02** — skills installed to `.claude/skills/` only; invisible to Codex's loader.
  The subject of this document.
- **CODX-03** — `tina4 ai` dies with an unhandled `EOFError` when stdin is not a TTY.
- **CODX-04** — the Rust CLI's `--all` / `--force` flags are not forwarded to the Python
  handler; the interactive menu still prompts and then hits CODX-03.
- **CODX-05** — `tina4 ai` creates an empty `.cursor/` directory it never writes into.

---

## Reproducing

```bash
cd /var/home/work/gitdir/testing-tina4/codex

# A — bare fixture (current state)
codex debug prompt-input "build a users route" > /tmp/a.json

# C — with the fix
mkdir -p .agents && ln -s ../.claude/skills .agents/skills
codex debug prompt-input "build a users route" > /tmp/c.json

# compare the developer message
python3 - <<'PY'
import json
for tag in "ac":
    d = json.load(open(f"/tmp/{tag}.json"))
    dev = "".join(c.get("text", "") for c in d[0]["content"])
    n = sum(1 for l in dev.splitlines() if l.startswith("- tina4"))
    print(tag, len(dev), f"{n} tina4 skills")
PY

# restore bare fixture
rm .agents/skills && rmdir .agents
```

**This fixture is left in the bare, as-`tina4 ai`-ships state** — the symlink was removed
after measuring, so the directory still reproduces the defect rather than the fix. Re-add it
with the one-liner above when you want the working configuration.

## Sources

- [Build skills — ChatGPT Learn](https://learn.chatgpt.com/docs/build-skills) (canonical
  target of `developers.openai.com/codex/skills`)
- [Custom instructions with AGENTS.md — OpenAI Developers](https://developers.openai.com/codex/guides/agents-md)
- [AGENTS.md Discovery — Codex CLI docs](https://fossies.org/linux/codex-rust/docs/agents_md.md)
- [AGENTS.md for Codex CLI (2026): Lookup Order, Limits & Monorepo Templates](https://www.codegateway.dev/en/blog/agents-md-playbook-2026)
- [The Codex CLI Skills Ecosystem](https://codex.danielvaughan.com/2026/03/27/codex-cli-skills-ecosystem/)
- [Codex CLI Agent Skills — install & usage guide](https://itecsonline.com/post/codex-cli-agent-skills-guide-install-usage-cross-platform-resources-2026)
- Primary evidence: `codex debug prompt-input` output and `strings` over
  `~/.codex/packages/standalone/current/bin/codex` (0.145.0)
