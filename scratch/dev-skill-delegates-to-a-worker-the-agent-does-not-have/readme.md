# dev-skill-delegates-to-a-worker-the-agent-does-not-have

**Ledger row:** [`f-ai-06`](../../known-issues/ledger.md)
**Measured on:** `tina4-developer-nodejs` SKILL.md as shipped at tags **3.13.103** and
**3.13.114**, against **codex-cli 0.147.0**, 2026-08-24.

## The issue

`tina4-developer-<lang>` — the developer skill `tina4 ai` installs for python, php, ruby and
nodejs — tells the assistant, in the imperative, **not to do the work itself**:

> ### 1. Keep the main session free — delegate to a worker
> When the developer gives an instruction, don't do the work inline. **Allocate it to a plan, then
> spawn a separate worker to execute it**, so the main session is always free for the next input.
> — `.claude/skills/tina4-developer-nodejs/SKILL.md:155`

Spawning a worker is a **harness capability, not a framework one**. Claude Code has it. Codex, as
configured by `tina4 ai`, does not: `codex debug prompt-input` renders the whole model-visible
prompt for a tina4 project and the word *worker* appears **zero** times in it. The skill uses it 17
times.

So an agent that reads this skill is holding an instruction it cannot carry out, and the skill
never says what to do instead. What it can still do is the surrounding ceremony — write the plan
file, announce the next step, report — which is what a developer sees: an assistant that keeps
saying what it is about to do.

## Why the report is this skill and not the app

The three surface markers in the reported session are all literal instructions from this file, and
nothing else in the Tina4 tree emits them:

| marker in the report | instruction | line |
|---|---|---|
| every reply begins 🤖 (`:robot_face:` in Slack) | *"begin every reply with the 🤖 emoji"* | `SKILL.md:27` |
| `About to: <verb> <path>`, three times | *"Formula: `About to: <verb> <path or command>`"* | `SKILL.md:40` |
| a maintained `plan/release-readiness.md` | *"Work is driven by a plan file under `plan/`"* | `SKILL.md:122` |

The 🤖 marker and the worker instruction are both present at tag **3.13.103**, the version the
reported app pins. `Announce before you act` is **not** — it first appears at **3.13.105**
(2026-08-19, `5cf5c5b`). The reported session used both, so the skill in that developer's context
was ≥3.13.105 even though their app pins 3.13.103 — `skillsRef()` keys the fetch to the installed
framework version, so the newer text arrived by some other route (a later `tina4 ai` run, or the
global `~/.claude/skills` install, which by design lags or leads independently).

## The mechanism

Three defects compound, in order of weight.

**1. The instruction is unsatisfiable and has no fallback.** `SKILL.md:155-157` is unconditional.
Nothing in the section says "if your harness has no worker mechanism, build inline." The one
sentence that addresses cross-agent portability is about *cost tiers*, not about whether workers
exist at all:

> This is agent-agnostic: Claude maps it to model + reasoning-effort, Codex to its model/effort
> selector, Cursor to its model picker. — `SKILL.md:161`

A model/effort selector is a setting. It does not spawn anything. The sentence reads as a portability
guarantee while quietly assuming the capability it is meant to make portable.

**2. It contradicts its own section preamble, 33 lines earlier.** `SKILL.md:122`:

> Prefer keeping the main session free (scope / delegate / report) and spawning workers to build —
> **but if you build in the main session**, you still own the plan file …

The preamble permits inline work; §1's heading and first sentence forbid it. A reader resolving the
conflict toward the more specific, more imperative §1 stops building.

**3. The announcement contract is framed as an interception point.** `SKILL.md:29-46` asks for
three announcements per action — Plan, Next, Done — and states the purpose plainly:

> A developer who can see the plan can stop it before you spend their afternoon undoing it.
> … one line before each step, **so the developer can stop between steps** rather than after all of
> them.

Told that the point of an announcement is to give the developer a chance to intervene, and told
separately that the main session must stay free "for the next input", an agent in a turn-taking
session has every reason to end the turn on the announcement. That is the reported behaviour.

`tina4-js` carries a **softened** copy of the same Working Method (`tina4-js/SKILL.md:84-107` in the
port repos): *"Prefer a worker per task; main session stays free **when possible**"*, and it keeps
the "or you" escape in the Delegate row. It also gates on developer approval — *"the plan file
(approved to start)"*, *"scope it with the developer first"* — which is its own turn-ending pull,
but it never says "don't do the work inline". The hard form is only in the four developer skills.

## Before / after

`prove.sh` runs three Codex sessions on an identical fixture and an identical prompt, differing
only in how the skill is delivered. **HOME is redirected to a throwaway directory** — the first run
of this experiment was void because the machine's own `~/.agents/skills` and `~/.claude/skills`
carry the same six tina4 skills, so the control arm had the skill too and both arms emitted
`About to:`.

Measured 2026-08-24, codex-cli 0.147.0:

| arm | skill delivery | `About to:` | 🤖 | log lines | `plan/` | task finished |
|---|---|---|---|---|---|---|
| C | project `.agents/skills/` (Codex's native registry) | 4 | 5 | 6 086 | no | yes |
| D | none — control | **0** | **0** | 6 534 | no | yes |
| E | `AGENTS.md` pointer → `.claude/skills/` (what `tina4 ai` writes) | 8 | 7 | 10 423 | **yes** | yes |

Two things the table settles:

- **Both delivery paths reach Codex 0.147.0.** Arm C proves the native `.agents/skills/` registry
  works; arm E proves the `AGENTS.md` pointer block `tina4 ai` writes is enough on its own, which
  is the path a real scaffolded project takes. Ledger `CLI-FW-06` was measured on codex-cli 0.145.0
  and says Codex receives none of the skills; that half is now out of date.
- **The behavioural contract is the skill's, not Codex's.** Arm D is the same fixture, same model,
  same prompt, and emits neither marker.

## What is NOT proven here

**A stall was not reproduced.** All three arms finished the task. `codex exec` is non-interactive —
there is no "next input" to keep the session free for, and no developer to stop between steps — so
the two instructions that would end a turn have no referent, and the cost shows up as overhead
instead: arm E used 60% more log lines than the control and was the only arm to build a `plan/`
tree.

The reported failure is a **multi-turn interactive** one, and reproducing it needs a driven
interactive session rather than `codex exec`. Until that exists, the causal claim rests on the
three literal markers matching and on the instruction being unsatisfiable — strong, but short of
the standard `scratch/readme.md` sets. Say so on the row; do not upgrade it quietly.

## Suggested fix

Make the delegation **conditional on the capability**, and keep the plan discipline unconditional:

- Rewrite `SKILL.md:155-157` to say the plan file is mandatory and worker delegation is an
  optimisation *where the harness provides workers* — naming the check, not assuming the answer.
- Delete the contradiction: either `:122` or `:155` has to go.
- Reframe `SKILL.md:29-46` so an announcement precedes an action **in the same turn**, rather than
  being described as the developer's chance to stop it. The stop-point framing is what turns a
  progress line into an end-of-turn.
- Correct `:161`, which names Codex and Cursor as if a model/effort selector were a worker.

The same four edits apply to python, php and ruby — the sections are line-for-line the same file
with the language swapped (`tina4-developer-python/SKILL.md:152`, `-php/SKILL.md:157`,
`-ruby/SKILL.md:155`).

## Run it

```bash
NODEJS_REPO=~/gitdir/tinaforks/tina4-nodejs ./prove.sh
```

Costs three real Codex sessions, roughly 5-10 minutes. Everything is written under a `mktemp -d`;
nothing is left in this directory.
