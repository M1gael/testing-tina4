#!/usr/bin/env python3
"""Suggested fix for f-ai-06 / f-ai-07 — see suggested-fix.md.

Prints a unified diff by default and writes nothing. --write edits in place.
Never commits, branches, pushes or opens a pull request.

Every anchor is TEXT, not a line number: SKILL.md line numbers drift between
releases, and the four ports wrap the same sentences differently. Whitespace in
an anchor matches any run of whitespace, so a match survives a re-wrap.
"""

import argparse
import difflib
import pathlib
import re
import sys

FORKS = pathlib.Path.home() / "gitdir" / "tinaforks"
REPOS = {
    "tina4-nodejs": "tina4-developer-nodejs",
    "tina4-python": "tina4-developer-python",
    "tina4-php": "tina4-developer-php",
    "tina4-ruby": "tina4-developer-ruby",
}
TREES = (".claude", ".agents", ".cursor")


def anchor(text):
    """Escape `text`, but let any whitespace run match any whitespace run."""
    return r"\s+".join(re.escape(word) for word in text.split())


# --- Edit 2 ------------------------------------------------------------------

NARRATE = """## Narrate as you act

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
a developer who switches languages recognises the pattern instantly."""


# --- the patch ---------------------------------------------------------------
# (edit id, description, compiled pattern, replacement)

EDITS = [
    ("1a", "drop approval-to-start / confirm-to-close",
     anchor("that is why plans stall. Developer approval is only required to **start** the plan "
            "and to set `## Status: Complete`. When an item lands, also append **commit hash + "
            "one-line description** under Commits in the same edit."),
     "that is why plans stall. No developer approval is required to start the plan or to close it —\n"
     "state the outcome, build against it, and report. When an item lands, also append **commit\n"
     "hash + one-line description** under Commits in the same edit."),

    ("1b", "drop confirm-to-close from the done table",
     anchor("| `## Status: Complete` | All Scope + Tests checked, developer confirms the feature "
            "| After developer confirmation |"),
     "| `## Status: Complete` | All Scope + Tests checked and green on a real run | "
     "Agent, immediately — the developer can reopen it |"),

    ("1c", "drop confirm-to-close from Closing the Plan",
     anchor("When every Scope and Tests item is `[x]` and the developer confirms, set "
            "`## Status: Complete` with the date."),
     "When every Scope and Tests item is `[x]` and green on a real run, set\n"
     "`## Status: Complete` with the date and report it."),

    ("1d", "drop the first UI ask-gate",
     anchor("Ask the developer which one they want"),
     "Decide which one applies"),

    ("1e", "drop the second UI ask-gate",
     anchor("**Before writing any UI code, ask:**"),
     "**Before writing any UI code, settle:**"),

    ("1f", "drop the third UI ask-gate",
     anchor("— Ask for any UI work."),
     "— Settle it for any UI work."),

    ("1g", "drop the if-unclear-ask fallback",
     anchor("If unclear, ask."),
     "If unclear, state the one you are assuming and proceed."),

    ("2", "reframe the announce block as narration",
     r"^## Announce before you act\b.*?" + anchor("recognises the pattern instantly."),
     NARRATE),

    ("3a", "make the delegate heading conditional",
     anchor("### 1. Keep the main session free — delegate to a worker"),
     "### 1. Delegate when your harness has workers — otherwise build inline"),

    ("3b", "make the delegate instruction conditional",
     anchor("When the developer gives an instruction, don't do the work inline. **Allocate it to a "
            "plan, then spawn a separate worker to execute it**, so the main session is always "
            "free for the next input."),
     "If your harness can spawn sub-agents, allocate the instruction to a plan and spawn a worker\n"
     "to execute it, so the main session stays free for the next input. **If it cannot — most CLI\n"
     "agents cannot — build inline yourself.** Either way, whoever builds owns the plan file.\n"
     "Never announce a worker you cannot spawn, and never treat \"spawn a worker\" as a reason to\n"
     "end a turn."),

    ("3c", "stop assuming a worker did the editing",
     anchor("so as the worker edits routes, models, and templates the"),
     "so as routes, models and templates are edited the"),

    ("4", "correct the agent-agnostic claim",
     anchor("This is agent-agnostic: Claude maps it to model + reasoning-effort, Codex to its "
            "model/effort selector, Cursor to its model picker."),
     "This is agent-agnostic where the harness supports it: Claude Code maps a sub-agent to model "
     "+ reasoning-effort. Codex and Cursor expose a model/effort selector for the session, not a "
     "worker to delegate to — there, pick the tier and build inline."),

    ("5a", "lead the preamble with the harness condition",
     anchor("Prefer keeping the main session free (scope / delegate / report) and spawning workers "
            "to build — but if you build in the main session, **you still own the plan file**:"),
     "Prefer keeping the main session free (scope / delegate / report) and spawning workers to\n"
     "build **where your harness can spawn them**; otherwise build in the main session. Either way\n"
     "**you own the plan file**:"),

    ("5b", "stop naming a worker as the only output",
     anchor("| 3. Delegate | Spawn a worker per task; the main session stays free "
            "| worker(s) running off the plan |"),
     "| 3. Delegate or build | Spawn a worker per task where the harness supports it; otherwise "
     "build inline | work running off the plan |"),

    ("6", "stop showing the plan as a checkpoint",
     anchor("Show the plan before coding so the developer can adjust scope."),
     "Write the plan and show it in the same turn you start building — the developer adjusts scope\n"
     "as you go, they do not have to unblock you."),
]

COMPILED = [(i, d, re.compile(p, re.S | re.M), r) for i, d, p, r in EDITS]


def patch(text):
    misses = []
    for edit_id, desc, pattern, repl in COMPILED:
        text, n = pattern.subn(lambda _m, r=repl: r, text, count=1)
        if n == 0:
            misses.append(f"{edit_id} ({desc})")
    return text, misses


def targets(forks):
    for repo, skill in REPOS.items():
        for tree in TREES:
            yield forks / repo / tree / "skills" / skill / "SKILL.md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="edit in place (default: diff only)")
    ap.add_argument("--forks", type=pathlib.Path, default=FORKS)
    args = ap.parse_args()

    forks = args.forks
    failed = False
    for path in targets(forks):
        if not path.exists():
            print(f"MISSING  {path}", file=sys.stderr)
            failed = True
            continue
        before = path.read_text()
        after, misses = patch(before)
        rel = path.relative_to(forks)
        if misses:
            failed = True
            print(f"UNMATCHED  {rel}: {', '.join(misses)}", file=sys.stderr)
        if before == after:
            print(f"NO CHANGE  {rel}", file=sys.stderr)
            continue
        if args.write:
            path.write_text(after)
            print(f"WROTE  {rel}", file=sys.stderr)
        else:
            sys.stdout.writelines(difflib.unified_diff(
                before.splitlines(keepends=True), after.splitlines(keepends=True),
                fromfile=f"a/{rel}", tofile=f"b/{rel}"))

    print("\nEdit 6 is partial: the 'Show the plan before coding' gate is patched, but folding\n"
          "'## Plan First — Always' into '## The Tina4 Working Method' is a structural dedup and\n"
          "is left manual on purpose — see suggested-fix.md.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
