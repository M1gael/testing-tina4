# testing-tina4

A workspace holding the separate projects that test the Tina4 framework.

**Each project is its own directory with its own readme, and that readme is the authority on
how the project works.** This file says only which projects exist and what each one is for.
It does not restate their rules, their workflow, or their tooling — to know how a project
operates, open its readme.

One directory per project. The single exception is `known-issues/`, which is not a project
but a shared record every project writes into.

## Projects

| Directory | What it is for | Its rules live in |
|---|---|---|
| `documentation-testing/` | Crawl the official Tina4 documentation chapter by chapter and section by section. Implement what each page literally shows, in real Tina4 projects, and establish whether the things it cites exist and behave as described — plus any general documentation faults found on the way. | [`documentation-testing/readme.md`](documentation-testing/readme.md) |

## The shared record

| Directory | What it is for | Its rules live in |
|---|---|---|
| `known-issues/` | Every confirmed issue found by any project, in one table — documentation and framework code alike, one row each. Projects log **out** to here; nothing else in this repo keeps a second bug list. | [`known-issues/readme.md`](known-issues/readme.md) |

## Adding a project

Keep the separation this layout exists to enforce — a project's work, history and backlog
stay inside that project.

1. Give it its own directory.
2. Give it a `readme.md` that defines its scope, and include a **Not here:** block naming
   what must never be written into it and where that belongs instead. That block is the part
   that actually prevents drift; a scope statement on its own does not.
3. Log its findings out to `known-issues/ledger.md`. Do not start a second issue list.
4. Add one row to the table above. One line. The definition stays in the project's readme.

Work that belongs to no project does not get parked in the nearest project's files. It gets
a directory of its own, or it stays out of this repo.

## Git

- Remote `git@github.com:M1gael/testing-tina4.git`, default branch `main`, and `main` is the
  only branch.
- This repo uses the **`M1gael`** identity on plain `github.com`. Upstream `tina4stack` repos
  are cloned over the `github-work` SSH alias (**`MichaelC8E`**). Don't cross the two.
- `~/.local/bin/sync` does `pull + add -A + commit + push` across every `M1gael` repo under
  `gitdir/`. It is run by hand, but it sweeps the whole working tree — an uncommitted change
  is only uncommitted until the next run.
