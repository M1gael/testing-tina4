# dev-skill-delegates-to-a-worker-the-agent-does-not-have

**Ledger row:** [`f-ai-06`](../../known-issues/ledger.md)
**Measured on:** `tina4-developer-nodejs` SKILL.md as shipped at tags **3.13.103** and
**3.13.114**, against **codex-cli 0.147.0**, 2026-08-24.

Reporter-raised: a Codex session on a tina4-nodejs app kept saying what it was about to do and
doing little or none of it.

## Why the report is this skill

The three surface markers in the reported session are literal instructions from this one file,
and nothing else in the Tina4 tree emits them:

| marker in the report | instruction | line |
|---|---|---|
| every reply begins 🤖 (`:robot_face:` in Slack) | *"begin every reply with the 🤖 emoji"* | `SKILL.md:27` |
| `About to: <verb> <path>`, three times | *"Formula: `About to: <verb> <path or command>`"* | `SKILL.md:40` |
| a maintained `plan/release-readiness.md` | *"Work is driven by a plan file under `plan/`"* | `SKILL.md:122` |

The 🤖 marker and the worker instruction are both present at tag **3.13.103**, the version the
reported app pins. `Announce before you act` is **not** — it first appears at **3.13.105**
(2026-08-19, `5cf5c5b`). The reported session used both, so the skill in that developer's context
was ≥3.13.105 even though their app pins 3.13.103; `skillsRef()` keys the fetch to the installed
framework version, so the newer text arrived by another route (a later `tina4 ai` run, or the
global `~/.claude/skills` install, which lags or leads independently by design).

## The instruction inventory

The file is at war with itself. **Twelve** instructions end a turn or suppress an action;
**four** push the other way.

**Gates**

| line | instruction |
|---|---|
| `:44` | never write more than two files between announcements |
| `:48` | five named stop-points — first file write, migration, dependency, scaffolding past two files, full test suite |
| `:131` | Delegate row: *"Spawn a worker per task; the main session stays free"* |
| `:156` | *"When the developer gives an instruction, don't do the work inline"* |
| `:236` | *"Developer approval is only required to **start** the plan"* |
| `:409` | *"Ask the developer which one they want before writing UI code"* |
| `:483` | *"**Before writing any UI code, ask:** 'Are we server-rendered or client-rendered?'"* |
| `:769` | *"Every feature starts with `plan/<feature-name>.md` … **No exceptions.**"* |
| `:850` | `## Status: Complete` only *"After developer confirmation"* |
| `:861` | *"'Server-rendered or client-rendered?' — Ask for any UI work … If unclear, ask."* |
| `:939` | *"Ask short questions."* |

**Counter-gates**

| line | instruction |
|---|---|
| `:122` | *"but if you build in the main session, you still own the plan file"* |
| `:137-152` | infer the outcome and PROCEED — *"Do not stop to ask: a stated assumption the developer can correct beats a plan blocked waiting on a reply"* |
| `:233-238` | *"do not wait for per-item approval … **that is why plans stall**"* |
| `:835` | *"Do **not** wait for per-item human approval."* |

The file therefore contains an accurate, named diagnosis of the reported failure — and patches it
in one narrow place while leaving five larger gates standing.

## The fix that missed

`de5358d` (2026-08-13) is titled:

> `docs(skills): let AI complete plans autonomously (drop approval-to-start / confirm-to-close / ask-first gates); add model + terse-thinking guidance to tina4-js`

It rewrote the outcome-asking section and two Working Method table rows. It **never touched any of
the five gates it names**:

```bash
git show de5358d -- .claude/skills/tina4-developer-nodejs/SKILL.md \
  | grep -cE "approval is only required to|After developer confirmation|Ask for any UI work|Before writing any UI code|Ask the developer which one"
# 0
```

`git blame` puts `:236`, `:850` and `:861` at `16eb0c8` (2026-08-11) and `:409`, `:483` at
`6d7c3568` (2026-07-08) — both **before** the commit that claimed to remove them. All five are at
HEAD today, in `.claude` and `.agents` alike.

## How it got this shape

| date | commit | what changed |
|---|---|---|
| 2026-07-08 | `6d7c3568` | developer skill split per language; the two UI ask-gates already present |
| 2026-07-09 | `0d84ef9` | *"add The Tina4 Working Method"* — the worker operating model, when `.claude/skills` was the repo's only tree |
| 2026-08-04 | `33c0a0b` | *"add Codex skill entrypoints"* — `.agents/skills` created, operating model copied across unchanged |
| 2026-08-11 | `eece8fd` | Cursor entrypoints under `.cursor/skills` |
| 2026-08-11 | `16eb0c8` | plan discipline unified: names the stall (*"that is why plans stall"*) **and** adds the start gate |
| 2026-08-12 | `4d7df10` | the agent-agnostic tier claim at `:161` |
| 2026-08-13 | `de5358d` | the gate-drop that missed five gates |
| 2026-08-19 | `5cf5c5b` | `Announce before you act` |
| 2026-08-24 | — | the report |

The operating model predates Codex support by four weeks. When Codex support arrived it was a file
copy, not an adaptation.

## The worker instruction — a real defect, not the cause

`SKILL.md:155-157` is unconditional:

> When the developer gives an instruction, don't do the work inline. **Allocate it to a plan, then
> spawn a separate worker to execute it**, so the main session is always free for the next input.

Spawning a worker is a harness capability. `codex debug prompt-input` renders the whole
model-visible prompt for a tina4 project and the word *worker* appears **zero** times in it; the
skill uses it 17 times. The one sentence addressing portability is about *cost tiers*, not about
whether workers exist:

> This is agent-agnostic: Claude maps it to model + reasoning-effort, Codex to its model/effort
> selector, Cursor to its model picker. — `SKILL.md:161`

A model/effort selector is a setting. It does not spawn anything.

**But it is not what the reported agent was acting on.** Across the two skill-carrying arms of the
delivery experiment, **0 of 23 and 0 of 27 agent turns** mention a worker, delegation or the main
session in the agent's own output. The model read the instruction, could not act on it, said
nothing about it, and built inline anyway — resolving the `:122` / `:156` contradiction toward the
preamble. It is the clearest defect in the file and the weakest driver of the behaviour.

## Two experiments

### 1. Delivery — `prove.sh`

Three arms, identical fixture and prompt, differing only in how the skill reaches Codex.
**HOME is redirected to a throwaway directory**; the first run of this experiment was void because
the machine's own `~/.agents/skills` and `~/.claude/skills` carry the same six tina4 skills, so the
control arm had the skill too and both arms emitted `About to:`.

| arm | skill delivery | `About to:` | 🤖 | log lines | `plan/` | task finished |
|---|---|---|---|---|---|---|
| C | project `.agents/skills/` (Codex's native registry) | 4 | 5 | 6 086 | no | yes |
| D | none — control | **0** | **0** | 6 534 | no | yes |
| E | `AGENTS.md` pointer → `.claude/skills/` (what `tina4 ai` writes) | 8 | 7 | 10 423 | **yes** | yes |

Both delivery paths reach Codex 0.147.0 — the native registry and the prose pointer alike. The
behavioural contract is the skill's, not Codex's: arm D is the same fixture, model and prompt and
emits neither marker.

### 2. Ablation — `ablate.sh`

Four arms, all carrying the skill via `.agents/skills/`, differing only in which section of
SKILL.md was deleted. Section bounds are resolved by search, not hard-coded, so an edited skill
still ablates correctly.

| arm | skill variant | `About to:` | 🤖 | log lines | files changed |
|---|---|---|---|---|---|
| F | full | 6 | 6 | 10 638 | 7 |
| G | minus `Announce before you act` (`:29-61`) | **0** | 5 | 11 815 | 7 |
| H | minus `1. Keep the main session free` (`:155-164`) | 6 | 5 | 12 868 | 8 |
| I | minus both | **0** | 16 | 5 278 | 6 |

The announcement count tracks the Announce block exactly and is untouched by removing the worker
section. Every arm still read the skill (🤖 survives in all four) and every arm still shipped the
feature — the block is separable and deleting it cost nothing in output.

**Log volume did not separate** (F 10 638, G 11 815, H 12 868). An earlier draft of this readme
suggested the skill drives verbosity; the ablation does not support that and the claim is dropped.

## What is still NOT proven

**A stall.** Every arm in both experiments finished the task. `codex exec` is non-interactive —
there is no "next input" to keep the session free for and no developer to stop between steps, so
the instructions that would end a turn have no referent. `codex`'s
`default_mode_request_user_input` feature flag was tried as a way in and is inert: enabling it
changes the rendered prompt by zero bytes.

The reported failure is multi-turn and interactive, and reproducing it needs a driven interactive
session. Until that exists the causal claim rests on the three literal markers matching, on the
gate inventory, and on the ablation attributing the announcements to a single removable block —
strong, but short of the standard `scratch/readme.md` sets. Say so on the row; do not upgrade it
quietly.

## Suggested fix, in evidence order

A concrete patch for all six now exists: **[`suggested-fix.md`](suggested-fix.md)**, runnable as
`./apply-fix.sh` (diff only) / `--write`. Verified to apply cleanly to all twelve files — 4 skills
x 3 delivery trees — with 0 unmatched anchors and 0 gates left behind. Nothing has been applied,
branched or filed. The summary below is the rationale; the patch is the text.


1. **Finish `de5358d`** — remove the five gates it was meant to drop: `:236`, `:850`, `:409`,
   `:483`, `:861`.
2. **Reframe `:29-61`** so an announcement precedes an action *in the same turn* rather than being
   the developer's chance to stop it. Ablation says this is free.
3. **Make delegation conditional** on the harness having workers; keep the plan file unconditional.
4. **Delete the `:122` / `:156` contradiction** — one of them has to go.
5. **Correct `:161`**, which names Codex and Cursor as if a model/effort selector were a worker.
6. **Reconcile the two plan doctrines** — the Working Method (`:120-257`) and *Plan First — Always*
   (`:764-868`) restate the same rules in different words, and `:769`'s "No exceptions" is stricter.

All six apply identically to python, php and ruby: the four files are the same document with the
language swapped, and every gate above is present in all four with identical counts
(`tina4-developer-python/SKILL.md:152`, `-php/SKILL.md:157`, `-ruby/SKILL.md:155` for the worker
section).

`tina4-js` is **clear** for the worker imperative and for the approval gates — the shipped port
copy (v1.5.2) reads *"the plan file (outcome stated, then start)"*. The gated text survives only in
the tina4-js repo's own copy (v1.5.0), which `sync-tina4-skills.sh` calls "a soft mirror on its own
release cadence" and does not gate.

## Run them

```bash
NODEJS_REPO=~/gitdir/tinaforks/tina4-nodejs ./prove.sh    # 3 codex sessions, ~5-10 min
NODEJS_REPO=~/gitdir/tinaforks/tina4-nodejs ./ablate.sh   # 4 codex sessions, ~10-20 min
./apply-fix.sh                                            # the proposed patch, as a diff
```

Both cost real tokens. Everything is written under a `mktemp -d`; nothing is left here.
