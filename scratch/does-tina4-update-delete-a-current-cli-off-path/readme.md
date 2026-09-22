# Does `tina4 update` delete a current CLI off PATH?

**Yes — without asking, unrecoverably, on a test that never reads the version it claims to
test.** Ledger row `f-cli-19`.

Investigated 2026-09-22 against the released **v3.8.88** `tina4-linux-amd64`
(sha256 `ea59826247768b7b3ae358624f042d37acb4faa68afcf06a7f47061092db550d`, the binary a user
gets), source read at `origin/main` `3a4377d`. Linux, Fedora, glibc.

## Mechanism

`handle_update()` (`src/main.rs:1620`) calls `clean_v2_binaries()` as its **first** step,
before the version check and before anything is downloaded (`src/main.rs:1624`). It is the
function's only call site, and `handle_update` is reached only from `Commands::Update`
(`src/main.rs:468`) — re-derived with `git grep` at `3a4377d`.

`clean_v2_binaries()` (`src/main.rs:1897`) resolves each of `tina4python`, `tina4php`,
`tina4ruby`, `tina4nodejs` through `which::which`, skips any whose path contains `vendor`,
`.venv` or `node_modules`, runs the survivor with `--version`, concatenates **stdout and
stderr**, and calls it v2 if that text contains any of:

```rust
out.contains("Thor") || out.contains("Deprecation") || out.contains("1.") || out.contains("2.")
```

then `std::fs::remove_file(&path)`. No prompt, no dry run, no backup, no undo.

**The falsifiable sentence:** the v2 test is a substring match over the whole of a CLI's
`--version` output, so it deletes on any `1.` or `2.` appearing anywhere in that text — a
property of the text, not of the version.

## What was run

`./prove.sh` — rebuilds the sandbox, downloads the released binary, and drives the real
`tina4 update`. Nothing on the machine's own PATH is reachable: the run uses
`env -i PATH=<decoys>:/usr/bin:/bin` and `HOME=<sandbox>` (which also neutralises
`refresh_installed_skills()`, which would otherwise write into `~/.claude/skills`).

| Decoy prints | Result |
|---|---|
| this machine's real `tina4python/php/ruby/nodejs --version` output | **kept** (round 1) |
| `Tina4 Python CLI 3.1.0` | **deleted** — `1.` |
| `tina4-ruby 0.2.206` | **deleted** — `2.` |
| `Tina4 Node CLI Thor 9.9.9` | **deleted** — the intended target |
| `Tina4 PHP CLI 3.13.136` | **kept** — contains neither |
| `Tina4 PHP CLI 3.13.136 (PHP 8.2.1)` | **deleted** — the `2.` came from the *PHP* version |
| same, under `vendor/bin` or `node_modules/.bin` | kept — the skip list |
| a symlink on PATH to a binary elsewhere | symlink deleted, target kept |

Two further controls: with a real TTY (`script -qec`) it still deletes and still does not
prompt; `tina4 doctor` deletes nothing.

## Bounds

- **Run** — every line of the table, on Linux, against the released v3.8.88 binary.
- **Read** — the mechanism and the single call site, at `3a4377d`.
- **Measured, and it narrows the row:** none of the four v3 CLIs installed on this machine
  (`tina4-python 3.13.100`, tina4-php v3, tina4-ruby, `tina4-nodejs 3.13.136`) matches. None of
  them implements `--version` at all — they print `Unknown command: --version` and a help
  screen, and those four help screens contain no `1.`, `2.`, `Thor` or `Deprecation`. The
  ledger row's "replay against PyPI 3.1.0–3.13.136" was **not** re-derived here.
- **Not visited:** Windows (the `.bat` fallback in the same function), macOS, a genuine v2
  CLI from the era this was written for, and older v3 CLIs whose banner may carry a version.
- **What would change the answer:** any port adding `--version`, or printing a runtime version
  in its banner. `(PHP 8.2.1)` is enough.

## Reachability

The CLI prints `Tina4 CLI <new> available (you have <old>). Run: tina4 update`
(`src/main.rs:595`), so users are told to run the command. `install.sh` at `3a4377d` does
**not** call it — reachability is the user typing it.

---

## The fix

Branch `fix/update-asks-before-deleting-a-cli-off-path`, cut from `origin/main` `3a4377d`,
uncommitted, worktree `~/.cache/tina4-worktrees/fcli19`. Diff saved as `fix.patch`
(src/main.rs + tests/update_v2_cleanup.rs, +424/-66).

Two changes, both in the evidence:

1. **Decide from a parsed version, not a substring.** `first_version_major` reads the *first*
   `<major>.<minor>` token in the output — a v3 CLI names itself before it names its runtime —
   and `classify_cli_generation` returns `V2` (major 1-2), `V3` (major 3+) or `Unknown`.
   `Unknown` is never a reason to delete. `Thor` still counts, but only where no version was
   readable, so it can never overrule a current release. Major `0` is deliberately `Unknown`:
   tina4-python has shipped `0.2.x` in the v3 era.
2. **Ask before deleting.** Candidates are collected, printed, and removed only after a yes.
   With no terminal on stdin nothing is deleted and the paths are printed with the `rm` line —
   prompting a pipe would hang an unattended `tina4 update`, which is `f-cli-12`'s defect and
   not one to introduce here.

**Deliberately unchanged:** the second arm, which looks for another `tina4` on PATH, keeps its
own rule (`!out.contains("tina4")`). That rule was never measured, and only its silent deletion
is fixed. The `vendor` / `.venv` / `node_modules` skips are untouched.

### How it was verified

`cargo test` — 227 unit + 4 new entry-point tests, `cargo clippy -- -D warnings` clean (the
three `--all-targets` clippy errors are pre-existing on `3a4377d`, in files this does not
touch). Six unit tests cover positive / negative / positive-edge / negative-edge, plus the
unreadable-version case and the version parser.

Four mutations, each reverted after:

| Mutation | Result |
|---|---|
| classifier back to the substring test | red — `update_leaves_a_current_cli_that_names_its_runtime` |
| remove the confirmation | red — `update_without_a_terminal_removes_nothing_and_says_so` |
| treat a pipe as consent | red — same test |
| take the last version token instead of the first | red — `first_version_major_reads_a_version_not_any_digits` |

**One of those attacks found a hole in the tests, not the fix.** The entry-point test first
asserted only that the file still existed — which the consent gate satisfies on its own, so it
stayed green with the old classifier put back. It now asserts the binary was never *nominated*,
and that mutation is red.

`BIN=<built binary> ./prove.sh` runs the reproduction against the fix: the three `-> DELETED`
rows and the symlink row go red, which is the behaviour change.

### Second pass, 2026-09-22 — two holes found in the fix itself

An adversarial re-read plus a 16-string probe battery against the built binary.

**The classifier read only the first version token, and that was still wrong.**
`Ruby 2.7.0 -- Tina4 Ruby CLI 3.13.136` was nominated: the leading token is the
*interpreter's*, major 2. Narrower than the substring test, not safe. Now every
`<major>.<minor>` in the text is read and **a major of 3 or more anywhere wins**.
The asymmetry is deliberate — mistaking a v2 for current leaves a stale binary on
PATH, mistaking a current one for v2 offers to delete a working CLI, and only the
second cannot be undone. Gated at both levels: reverting to first-token-only turns
`classify_v2_positive_edge_runtime_version_does_not_make_it_v2` and
`update_leaves_a_current_cli_whose_runtime_is_named_first` red.

Same change fixes a wart the probe found: a number too large for `u32`
(`1234567890123.0`) used to abort the scan and hide every token after it.

**Scope creep of my own, reverted.** The first version removed a `.bat` sibling on
the *success* branch for all four named CLIs. Upstream only does that in the
*failure* branch for those four, and on success only for the second `tina4` arm.
That is an extra file deletion, unmeasured, in exactly the class of operation this
fix exists to restrain. Each candidate now carries upstream's own flag and the two
arms behave as they did.

**Not gated:** the `.bat` behaviour has no test — the success branch needs a
terminal to consent, and the suite has no pty. Verified by reading the diff against
upstream, and by the interactive runs (yes deletes, no keeps).
