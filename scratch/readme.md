# scratch

**Proof projects. One directory per issue, each a real runnable Tina4 app.**

A scratch project exists to answer one question with certainty: *is this issue real, do we
understand exactly how it works, and does our fix actually close it?* It is the evidence a
fix is built on, and it is written **before** the fork is touched.

Every project here is named for the behaviour it proves, not for the fix — read the directory
list and you should be able to tell what is broken without opening anything.

## The order of work

A fix does not get written until its proof project exists and its first two stages pass.

1. **Reproduce on the stock framework.** Install the released version, run the app, and
   capture the wrong behaviour as output. If it cannot be reproduced from a clean install,
   there is no issue and the ledger row is wrong.
2. **Explain it.** Name the exact `file:line` that causes it and why. A reproduction without
   a mechanism is a symptom, not an understanding — and a fix built on a symptom is a guess.
3. **Prove the fix closes it.** Apply the candidate fix against the same app and show the
   behaviour change, side by side with stage 1.
4. **Only then** apply the fix to the local fork and verify it there a second time.
5. **Then** ask for approval to open the pull request. Never open one unasked.

## What a project contains

| File | What |
|---|---|
| `readme.md` | The issue, the mechanism with `file:line`, and the before/after output. Self-contained — a reader should not need the ledger to follow it. |
| the app | A real project from `tina4 init python .` — routes, config, whatever the issue needs. |
| `prove.sh` (or equivalent) | Runs the reproduction and prints the verdict. Re-runnable by anyone, on any machine. |

Pin the framework version the run was done against. An unversioned reproduction ages into a
claim nobody can check.

**Not here:**

- **The fix itself** — a candidate patch may sit here while it is being proven, but the fix
  lands in the fork at `gitdir/tina4-python`, on its own branch. This directory is evidence,
  not a source tree.
- **A second issue list** — findings are logged out to `../known-issues/ledger.md`. A project
  here corresponds to a ledger row; it does not replace one.
- **Documentation crawling** — that is `../documentation-testing/`, a separate project with
  its own rules. A scratch project may cite a documentation page as the contract an issue
  breaks, but it does not test the documentation.
- **Anything that must survive** — this directory is disposable by name and by intent. When a
  fix is merged upstream, the project's findings are already in the ledger row; the project
  can go.

## Working against the real repositories

The framework, the book and the site live outside this repo. A proof project written against a
stale copy proves something about a version nobody runs.

```
gitdir/tina4-python/          origin = tina4stack; fork = MichaelC8E
gitdir/tina4-book/            fork of tina4stack/tina4-book      (fork = MichaelC8E)
gitdir/tina4-documentation/   fork of tina4stack/tina4-documentation
gitdir/tina4-js/              clone of tina4stack/tina4-js
```

**Pull before you prove anything.** All of them, not just the one you expect to touch — a
framework issue gets checked against the documentation that describes it, and the documentation
is the contract the issue breaks.

```bash
for r in tina4-python tina4-book tina4-documentation tina4-js; do
  git -C ../$r fetch --all --prune
done
```

**A fork is only useful once it is level with the official repo.** A fork's default branch
drifts behind silently — no warning, the files just quietly describe an older release. Measure
before trusting it:

```bash
git -C ../tina4-python rev-list --left-right --count v3...origin/v3
#                                                    ^ours-only  ^upstream-only
```

Zero commits of our own means syncing is a fast-forward and loses nothing. Bring it level
*before* branching, and cut the fix branch off the upstream branch rather than off whatever the
fork happens to be sitting on. A branch cut from a release two versions back reads as though it
deletes everything shipped since.

Two identities, and they must not cross: this repo uses **`M1gael`** on plain `github.com`;
every `tina4stack` repo is cloned over the **`github-work`** SSH alias (`MichaelC8E`).

## Trying a fix before it is a fix

Stage 3 needs the candidate applied somewhere. Editing the framework inside a project's `.venv`
is allowed *for that purpose* — poking at the installed copy is how you find out whether an
idea holds, and routing it through a clone first only slows the answer down.

Three rules make that safe:

1. **Stage 1 comes first, on untouched source.** Patching to see whether a chapter proceeds is
   not a finding. "It works once I patch this" is a hypothesis about a defect you have not yet
   reproduced.
2. **Restore the workspace immediately afterwards.**
   ```bash
   cd ../documentation-testing/pypy && uv sync --reinstall-package tina4-python
   ```
   A scratch patch that outlives the question it answered is the banned thing. It turns every
   later run in that workspace into a lie, and the output looks identical either way. If you
   cannot say which files you touched, reinstall rather than guess.
3. **Never report a number measured against a patched workspace.** Ledger rows and proof-project
   readmes cite the clean run, or a `PYTHONPATH` run against the fork.

Once the fix is written, `PYTHONPATH` pointing at the fork is the better default — it alters
nothing, so it needs no cleanup and cannot be forgotten.

## After the proof

The fix lands on its own branch in `gitdir/tina4-python`, cut from the current upstream branch,
carrying a regression test that fails against unfixed source. Then it is verified a second time
there, from the fork rather than from this directory.

**Opening the pull request is not part of the workflow.** It happens on explicit approval, per
fix, and never as a side effect of finishing one. Commit messages carry no `owner/repo#NNN`
reference — an auto-link posts a visible event on the upstream issue under whichever account
pushed, which is how the two identities get crossed.
