# Suggested fix — `f-ai-06` (with a note on `f-ai-07`)

**Target:** the four framework developer skills, in all three delivery trees — 12 files.
**Written against:** `tina4-nodejs` at `83ac514` (`3.13.114-3`), 2026-08-25.
**Status:** proposed. Nothing applied, committed, branched, pushed or filed.
**Script:** `./apply-fix.sh` (diff only) / `./apply-fix.sh --write`.

## Scope

| repo | skill | trees |
|---|---|---|
| `tina4-nodejs` | `tina4-developer-nodejs` | `.claude` `.agents` `.cursor` |
| `tina4-python` | `tina4-developer-python` | `.claude` `.agents` `.cursor` |
| `tina4-php` | `tina4-developer-php` | `.claude` `.agents` `.cursor` |
| `tina4-ruby` | `tina4-developer-ruby` | `.claude` `.agents` `.cursor` |

Every anchor below was verified present **exactly once in all twelve files**, and the patch was
applied to a throwaway copy of all twelve: 12 files changed, 0 unmatched anchors, 0 gates left
behind, `##` heading count unchanged (59 → 59 on Node).

The `f-ai-07` drift between `.claude` and `.agents`/`.cursor` is in factual details, not in any
gate — so one patch covers the whole set. `tina4-js` is out of scope: the shipped port copy (v1.5.2)
carries none of these gates.

> **Anchors are text, never line numbers.** `SKILL.md` grew 970 → 996 lines between the
> investigation and this document, so every line number recorded on `f-ai-06` is already stale. The
> ports also wrap the same sentences differently (`two architectural approaches` vs `two distinct
> architectural approaches`, `Are we server-rendered` vs `Are we doing server-rendered`), so the
> script matches any whitespace run where an anchor has a space.
>
> This bit once: the sentence *"…so a developer who switches languages recognises the pattern
> instantly."* appears **twice** — once ending the announce block, once ending `Detect if you are
> stale`. A newline-blind anchor matched the second and swallowed the stale-detection section.

---

## Edit 1 — finish `de5358d`: remove the approval gates

`de5358d` (2026-08-13) is titled *"drop approval-to-start / confirm-to-close / ask-first gates"* and
removed none of them. Seven instances, `1a`–`1g`.

**1a** — approval to start / confirm to close

```diff
 pass on a real run. **Do not** leave boxes open waiting for the developer to approve each item —
-that is why plans stall. Developer approval is only required to **start** the plan and to set
-`## Status: Complete`. When an item lands, also append **commit hash + one-line description** under
-Commits in the same edit.
+that is why plans stall. No developer approval is required to start the plan or to close it —
+state the outcome, build against it, and report. When an item lands, also append **commit
+hash + one-line description** under Commits in the same edit.
```

**1b** — the "done" table row

```diff
-| `## Status: Complete` | All Scope + Tests checked, developer confirms the feature | After developer confirmation |
+| `## Status: Complete` | All Scope + Tests checked and green on a real run | Agent, immediately — the developer can reopen it |
```

**1c** — Closing the Plan

```diff
-When every Scope and Tests item is `[x]` and the developer confirms, set
-`## Status: Complete` with the date.
+When every Scope and Tests item is `[x]` and green on a real run, set
+`## Status: Complete` with the date and report it.
```

**1d / 1e / 1f / 1g** — the UI ask-gates. Verb swaps only; the surrounding sentences differ per port
and are left alone.

| id | from | to |
|---|---|---|
| 1d | `Ask the developer which one they want` | `Decide which one applies` |
| 1e | `**Before writing any UI code, ask:**` | `**Before writing any UI code, settle:**` |
| 1f | `— Ask for any UI work.` | `— Settle it for any UI work.` |
| 1g | `If unclear, ask.` | `If unclear, state the one you are assuming and proceed.` |

---

## Edit 2 — reframe `## Announce before you act` as narration

This is the block the reporter saw. Ablation arm G deleted it outright: announcements went 6 → 0,
the skill still loaded (🤖 survived), and the feature still shipped. The block is separable and
removing it cost nothing — so keep the visibility and drop the turn-boundary contract.

Three things go: *"so the developer can stop between steps"* (turns an announcement into a
handover), the `About to:` formula itself (what the reporter saw repeated with nothing following
it), and the two-file cap (a hard stop every two writes).

The whole section, `## Announce before you act` through `recognises the pattern instantly.`,
becomes:

```markdown
## Narrate as you act

**Say what you are doing, in one line, as you do it — then keep going.** The developer reads the
trail; they do not have to answer it. Nothing in this section is a turn boundary and nothing in it
waits for a reply.

Two lines per substantive action, both in the same turn as the work itself:

1. **Plan** — one line naming every file you'll touch and every command you'll run for the current
   slice, at the top of your first response for that slice.
2. **Done** — one line after each step, so the developer knows what to undo.
   Formula: `Wrote <path>` / `Ran <command> — <one-line result>`.

Name these when they happen, because they are the expensive ones to reverse — name them and
proceed, do not pause on them:

- the first file write in a slice
- a schema migration
- a new dependency
- scaffolding into more than two files
- a full test-suite run

The one case to actually ask: an irreversible action where the developer's intent is ambiguous.
Then ask one specific question with your best read as the default, so a "yes" moves the work.

This is the same rhythm across all four framework developer skills (Python / PHP / Ruby / Node), so
a developer who switches languages recognises the pattern instantly.
```

**Lighter variant** if `About to:` is wanted for its own sake: keep the line but add *"`About to:`
is narration, not a checkpoint — write it and take the action in the same turn."* Weaker against the
reported failure, since the reported agent emitted the formula and then stopped.

---

## Edit 3 — make delegation conditional on the harness

`codex debug prompt-input` renders the whole model-visible prompt for a tina4 project: the word
*worker* appears **zero** times. The skill uses it 18 times and instructs unconditionally.

**3a** — heading

```diff
-### 1. Keep the main session free — delegate to a worker
+### 1. Delegate when your harness has workers — otherwise build inline
```

**3b** — the instruction

```diff
-When the developer gives an instruction, don't do the work inline. **Allocate it to a plan, then
-spawn a separate worker to execute it**, so the main session is always free for the next input.
+If your harness can spawn sub-agents, allocate the instruction to a plan and spawn a worker
+to execute it, so the main session stays free for the next input. **If it cannot — most CLI
+agents cannot — build inline yourself.** Either way, whoever builds owns the plan file.
+Never announce a worker you cannot spawn, and never treat "spawn a worker" as a reason to
+end a turn.
```

**3c** — the DevReload sentence, which assumes a worker did the editing

```diff
-so as the worker edits routes, models, and templates the
+so as routes, models and templates are edited the
```

The rest of that paragraph is untouched — python and php carry an extra sentence there that node
and ruby do not, and a whole-paragraph replacement would silently drop it.

---

## Edit 4 — correct the agent-agnostic claim

Names Codex and Cursor as if a model/effort selector were a worker. It is a setting; it spawns
nothing.

```diff
-This is agent-agnostic: Claude maps it to model + reasoning-effort, Codex to its model/effort
-selector, Cursor to its model picker.
+This is agent-agnostic where the harness supports it: Claude Code maps a sub-agent to model +
+reasoning-effort. Codex and Cursor expose a model/effort selector for the session, not a worker to
+delegate to — there, pick the tier and build inline.
```

---

## Edit 5 — resolve the preamble contradiction

The Working Method preamble concedes inline building; the numbered section then forbids it. After
Edit 3 they agree, but the preamble should lead with the condition rather than treat it as an aside.

**5a**

```diff
-Prefer keeping the main session free (scope / delegate / report) and spawning workers to build — but if you build
-in the main session, **you still own the plan file**:
+Prefer keeping the main session free (scope / delegate / report) and spawning workers to
+build **where your harness can spawn them**; otherwise build in the main session. Either way
+**you own the plan file**:
```

**5b** — the Working Method table row

```diff
-| 3. Delegate | Spawn a worker per task; the main session stays free | worker(s) running off the plan |
+| 3. Delegate or build | Spawn a worker per task where the harness supports it; otherwise build inline | work running off the plan |
```

---

## Edit 6 — the two plan doctrines

`## The Tina4 Working Method` and `## Plan First — Always` restate the same rules ~500 lines apart,
in different words, at different strictness. An agent reading both gets two plan protocols.

**Scripted part** — the one line in that section that is a gate:

```diff
-Show the plan before coding so the developer can adjust scope. If they say "just build it," still
-create the plan file, then build against it — never skip the file.
+Write the plan and show it in the same turn you start building — the developer adjusts scope
+as you go, they do not have to unblock you. If they say "just build it," still
+create the plan file, then build against it — never skip the file.
```

**Manual part, deliberately not scripted** — fold `## Plan First — Always` into the Working Method:
keep the file format, the `plan/MASTER.md` requirement and the tool-layer enforcement note; drop
`### Working the Plan — non-negotiable`, whose items 2, 6 and 7 restate Working Method steps 6, 2
and 1 in substance. This is a structural dedup with a large, port-specific diff and it is the least
evidenced of the six — it is a readability fix, not a fix for the reported failure. A script doing
it blind would be reckless.

`No exceptions` on the plan file **stays**. It gates writing a file, not waiting on a human, and is
no part of the reported failure.

---

## Suggested commit split, per repo

| commit | edits | subject |
|---|---|---|
| 1 | 2 | `docs(skills): make action narration non-blocking (drop About-to checkpoints)` |
| 2 | 3, 4, 5 | `docs(skills): make worker delegation conditional on harness support` |
| 3 | 1 | `docs(skills): remove the approval gates de5358d was meant to drop` |
| 4 | 6 | `docs(skills): fold Plan First — Always into the Working Method` |

Edits 3, 4 and 5 are one change and should land together. Edit 1 is mechanical and independent.
Edit 2 is the one the reporter actually hit. Edit 6 can be dropped without weakening the fix.

## What this does NOT do

- **It does not close `f-ai-07`.** The three trees stay three hand-maintained copies per repo and
  `scripts/sync-tina4-skills.sh` still does not keep them in step. Patching twelve files by hand
  would make the drift worse; the script exists so all twelve move together, but the sync script is
  still the real fix (task **A9**).
- **It is not proven to fix the reported stall.** The stall is still unreproduced (task **A1**).
  What is proven: the announcement behaviour tracks Edit 2's block exactly, and removing that block
  cost nothing in output or in completion.
- **It touches no framework code.** `f-rt-01` (`packages/core/src/server.ts`, handler arguments
  bound by parsed parameter name) is a separate fix and has no candidate written yet.

## Run it

```bash
./apply-fix.sh                       # unified diff for all 12 files, writes nothing
./apply-fix.sh --write               # edit in place
./apply-fix.sh --forks /tmp/copy     # run against a throwaway copy of the tree
```

Exit status is non-zero if any anchor fails to match — which is how you find out a release moved
the text out from under this patch. Neither mode commits, branches, pushes, nor opens a pull
request.
