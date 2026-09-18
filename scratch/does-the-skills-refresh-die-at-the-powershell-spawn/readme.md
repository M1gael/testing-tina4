# Does the skills refresh die at the PowerShell spawn, or inside PowerShell?

**Question.** @jeandre's `tina4 update` prints `Installing tina4 AI skills for all...`, then the
bare skip line, and nothing in between. Does that gap mean the child process never ran, or can a
child that *did* run produce the same gap?

**Answer: it died at the spawn.** A child that runs the real bootstrap cannot produce that gap —
every failure available to it writes to stderr, and stderr is inherited. But the reasoning that
gets there is narrower than it first looks, and one obvious step of it is invalid. See *The step
that does not hold*.

**Pinned.** tina4 CLI **3.8.88** (`2bb1418`), the released Linux binary, `--version` checked.
`src/setup.rs` is byte-identical between `v3.8.87` and `v3.8.88` (`git diff --quiet` exits 0), so
this is the same code that produced the 2026-09-16 report. Bootstrap: the live 2339-byte
`https://tina4.com/install-skills.ps1`, fetched 2026-09-17 and `diff`-identical to the copy
stored in `../skills-refresh-fails-with-no-reason-on-windows/`. PowerShell **7.4.6**, rootless
tarball in `/tmp/pwsh`. Run on Linux; **no Windows host was used**.

```
./prove.sh           0 = the silent skip reproduces from a spawn failure alone
./counterexample.sh  shows the same output from a child that DID launch
```

## The reproduction: one symlink

`prove.sh` builds a PATH farm holding every one of `/usr/bin`'s 1406 executables **except `sh`**,
then runs `tina4 skills all` twice. The only difference between the arms is that one symlink.

| | stdout | stderr | exit | what printed |
|---|---|---|---|---|
| **A** `sh` withheld | 97b | **0b** | 2 | `Installing...` then the bare skip |
| **B** A + one symlink | 975b | 0b | 0 | the installer header, 8 skills, 48 files verified |

Arm A is @jeandre's screenshot: the same two lines, nothing between, nothing on stderr. This is
the **Linux** arm (`run_status_env("sh", ...)`, `setup.rs:1016`), but it is the same
`.unwrap_or(false)` at `setup.rs:1717-1725` that the Windows arm at `:1007-1013` goes through.

Necessary and sufficient, in one factor: withhold the spawned program and the silence appears;
restore it and it goes.

## The step that does not hold

**"Zero bytes, therefore the process never launched" is invalid on its own.**

`counterexample.sh` replaces the withheld `sh` with `/usr/bin/false` — a real program that
launches, runs, and exits 1 without printing. Result:

```
exit=2  stdout=97b  stderr=0b   →  C.out BYTE-IDENTICAL to A.out
```

`.unwrap_or(false)` maps a spawn `io::Error` and a silent non-zero exit to the same `false`, so
the CLI's output genuinely cannot tell them apart. Any argument resting on the gap alone is
resting on nothing.

## What the step actually rests on

It rests on a second claim, which is that the *real* payload is never silent. That was
previously asserted from reading. It has now been run, against the live bootstrap, under `iex
([System.IO.File]::ReadAllText(...))` — the exact string `windows_skills_command`
(`setup.rs:944-949`) builds:

| Failure forced | stdout | stderr | exit |
|---|---|---|---|
| every source 404s (`TINA4_SKILLS_REF=0.0.0-nope`) | 0b | **450b** | 1 |
| network unreachable (dead proxy) | 0b | **450b** | 1 |
| ConstrainedLanguage mode | 0b | **131b** | 1 |
| staged installer file empty | 0b | **112b** | 1 |

The first two are the bootstrap's own `throw` at its line 48, rendered by PowerShell. The third
is `Cannot invoke method. Method invocation is supported only on core types in this language
mode.`

**Four failure shapes, four loud.** A launched PowerShell running that bootstrap has no silent
way to fail. So the zero-byte gap is inconsistent with "it ran", and that is what carries the
answer — not the gap by itself.

### One candidate this positively eliminates

**Application Control in its ConstrainedLanguage form is out.** WDAC forcing ConstrainedLanguage
would block `[System.IO.File]::ReadAllText` — and that prints 131 bytes. It was previously listed
as an equal candidate alongside PATH. It is not one. A policy that denies the *launch* is still
open; a policy that merely constrains the language is not.

## So the surviving explanations

Both sit at the spawn, and the CLI cannot distinguish them:

1. `CreateProcess` never launched `powershell.exe` — `PATH`, or a policy/AV denying the launch.
2. It launched and was killed before executing its first statement.

The difference does not change the fix.

## Mechanism for (1), and its warrant

**Read, not measured here.** `powershell.exe` lives in `System32\WindowsPowerShell\v1.0\`, not in
`System32`. `CreateProcess` given a bare program name searches the application directory, the
current directory, `System32`, the Windows directory, then `PATH` — so bare
`Command::new("powershell")` (`setup.rs:1012`) resolves **via `PATH` only**. A `PATH` that has
lost `%SystemRoot%\System32\WindowsPowerShell\v1.0\` fails the spawn.

Her own interactive PowerShell window is not evidence against this: Explorer launches it by full
path, never by a `PATH` lookup.

**Two lines settle it on her box:**

```powershell
where.exe powershell
cmd /c powershell -NoProfile -Command "Write-Output OK"
```

Nothing from the first means `PATH`. A path from the first and a failure from the second means
the launch is being denied — a machine-administration decision, not something to work around.

## CI cannot catch this

`.github/workflows/ci.yml` does have a `windows-latest` job, and it does not reach here. It runs
`python tests/skills_installer_http.py powershell` and an Authenticode check, under GitHub's own
`shell: powershell`. **The tina4 binary is never invoked**, so `Command::new("powershell")` at
`setup.rs:1012` is never exercised on Windows by anything. A broken spawn ships green.

## Run 4 (2026-09-17): observed on Windows semantics, under Wine

Everything above was measured on Linux. This section was measured with the **Windows binary**,
on the `cfg!(target_os = "windows")` branch, with real `CreateProcess` semantics.

**Setup.** `tina4-windows-amd64.exe` v3.8.88 from the GitHub release, sha256 checked against the
release's own `SHA256SUMS` (`f6f3a095…5fec`). Wine **11.0** via the `com.usebottles.bottles`
flatpak, in a persistent prefix at `~/.cache/tina4-wine/pfx` (800 files in `system32`). The
prefix was restored to its original state after every run.

**Wine is not Windows, and it lied once — usefully.** Wine ships a `powershell.exe` *stub* that
prints `fixme:powershell:wmain stub.`, ignores its arguments and **exits 0**. With it in place
both spawns "succeed", `fetch_skills_installer` reports a download that never happened, and the
run ends at 42 bytes with no skip line at all. Every number below was taken with that stub
either removed or deliberately repurposed, and the first two runs against a half-built,
ephemeral prefix were discarded.

### The reproduction

`curl.exe` present and exiting 0 (download succeeds), `powershell.exe` removed:

```
  > Installing tina4 AI skills for all...
  ! Skills install skipped - run later: tina4 ai
```

93 bytes, exit 2, **no cause**. That is the shape of the reported screenshot, produced on the
Windows code path rather than argued for from Linux.

### The elimination, now run rather than inferred

Same prefix, `curl.exe` ALSO removed, so the download fails instead:

```
  > Installing tina4 AI skills for all...
  ! Could not download the skills installer - https://raw.githubusercontent.com/tina4stack/tina4/main/install-skills.ps1: the downloader could not be started: program not found
  ! Skills install skipped - run later: tina4 ai
```

272 bytes. **A failed download says why on Windows; a failed spawn does not.** The report carried
no cause line, so the download succeeded and the failure is at the spawn. That step was
previously inferred from reading; it is now observed.

### Two claims upgraded from "read" to "run"

- **The argv the CLI actually passes.** Wine logged it verbatim:
  `argv[1] "-NoProfile"`, `argv[2] "-Command"`, `argv[3] "$ErrorActionPreference='Stop';
  $env:TINA4_SKILLS_TARGET='all'; iex ([System.IO.File]::ReadAllText('C:\users\…\tina4-skills-220-…\install-skills.ps1'))"`.
  Flags separate, path intact, no quoting corruption. **A mangled `-Command` string is
  eliminated by observation.**
- **Where `powershell.exe` lives.** Wine's own stub sits at
  `system32\WindowsPowerShell\v1.0\powershell.exe`, not in `system32`, and the bare name resolved
  to it through `PATH` — the layout this whole investigation rested on, now seen rather than
  recalled.

### Found on the way: a real latent defect, unrelated to the report

`download_file_classified` (`main.rs:2362-2397`) takes a PowerShell fallback exit code of 0 as a
successful download and **never checks the destination file exists or has any content**. Wine's
do-nothing stub exposed it: `fetch_skills_installer` returned `Ok` with nothing on disk, and the
installer was then pointed at a file that was never written. The same hole is reachable on real
Windows by any `Invoke-WebRequest` that exits 0 without producing a file. Not this report's
cause — her box has `curl.exe`, which takes the other branch — and not pursued here.

## Warrants

- **Run** — arms A/B/C, and all four PowerShell failure shapes. Linux, pwsh 7.4.6, stock 3.8.88.
- **Run** — `setup.rs` identical across `v3.8.87..v3.8.88`; live bootstrap identical to the stored copy.
- **Read** — `setup.rs:944-949`, `:1007-1013`, `:1717-1725`; `main.rs:2359-2397`; `ci.yml`.
- **Read** — the `CreateProcess` search order and the location of `powershell.exe`.
- **Inferred** — that @jeandre's box is case (1) rather than (2). Unresolved by design; the two probes above resolve it.

## Not visited

- **Real Windows, and real Windows PowerShell.** Run 4 reaches the Windows *code path* under
  Wine 11.0, which is a long way better than arguing from Linux, but Wine is not Windows and it
  ships no real PowerShell — only a stub. So nothing here observes Windows PowerShell 5.1
  itself: not its exception types (`WebException` vs `HttpResponseException`), not its error
  rendering, and not how Application Control or AV interact with a launch. pwsh 7.4.6 on Linux
  covered "is it silent", which is much weaker than "what does it say", and is the only property
  the argument needs.
- **The fix, on Windows.** It could not be cross-built here: no mingw and no MSVC toolchain, so
  `x86_64-pc-windows-gnu` and `-msvc` are both unavailable. Run 4 shows the *unfixed* binary's
  silence on the Windows path; the repaired binary's output there is still unobserved.
- **A WindowsApps App Execution Alias stub for `powershell`.** A zero-byte stub for an
  uninstalled Store app exits non-zero without printing, and would fit case (2). Not reachable
  from here, and not known to exist for `powershell` specifically.
- **Whether `tina4 update` and `tina4 skills all` differ on her box.** Both enter
  `install_skills_target`; `update` exits 0 by design, `skills` exits 2. Only the exit code differs.
- **The first report's date.** Now moot: it reproduces on current code with current content.

## Found on the way, unpursued

- `src/main.rs:2379` is a **second** bare `Command::new("powershell")`, in the download fallback
  used when `C:\Windows\System32\curl.exe` is absent. Same family. Its own comment already says
  *"Untested: this path needs a Windows box without curl.exe."*
- `download_file_classified` (`main.rs:2362-2388`) already does on Windows what the skills spawn
  does not: it reaches for an **absolute** `C:\Windows\System32\curl.exe` first. The pattern the
  fix needs is in the same file.
- `iex` on an empty string exits **1** with 112b on stderr, not 0 as reasoned before running it.
  The conclusion is unchanged — it is loud either way — but the earlier reasoning was wrong.
- `tina4stack/tina4` has two issues total, neither related. Nobody has reported this.

## Run 5 (2026-09-17): the fix, measured on that same instrument

Run 4 showed the defect on Windows semantics. This run puts the repaired binary next to the
stock one in the same prefix, one cell at a time.

**How the fixed binary was built.** There is no mingw and no MSVC toolchain on this box and no
root to install one, so `x86_64-pc-windows-gnu` was cross-built with rustup's target plus zig
0.13.0 standing in for the C toolchain: `zig cc` as compiler and linker, `zig ar`, and
`zig dlltool` symlinked as `x86_64-w64-mingw32-dlltool` (rustc invokes that name by hand for the
import-library path `windows-sys` and `parking_lot_core` need). Four adjustments were needed in
the `zig cc` wrapper, all recorded in it: strip the `--target=x86_64-pc-windows-gnu` the `cc`
crate appends (zig cannot parse it), strip the binutils-only link flags zig's lld rejects, drop
`-lgcc/-lmsvcrt/-lmingw*` because zig ships its own CRT, map `-lgcc_eh` onto zig's `-lunwind`,
and pass `windows_x86_64_gnu`'s `libwindows.0.52.0.a` by path. `rustc`'s own
`compiler_builtins` is dropped in favour of zig's `compiler_rt`, which is what removes a
duplicate `___chkstk_ms`.

**Two differences from a release build, stated rather than hidden.** The binary is built by a
different toolchain from the official release, and the `grass` dependency had `cdylib` removed
from its crate types in a build-only copy of the tree (zig's linker will not take the `.def`
file rustc generates for a Rust dylib). Neither touches a line under test. The copy is a build
artefact; the fix branch itself is unmodified.

It runs: `tina4-fixed.exe --version` prints `tina4 3.8.88` under Wine.

### A. `powershell.exe` absent — does the fix say why?

`curl.exe` stand-in in `system32` so the download succeeds, `powershell.exe` moved aside:

| | bytes | exit | output |
|---|---|---|---|
| stock v3.8.88 | 93 | 2 | `! Skills install skipped — run later: tina4 ai` |
| fixed | 148 | 2 | `! powershell could not be started: program not found`<br>`! Skills install skipped — run later: tina4 ai` |

**The reported screenshot, and the same run with a cause line on it.** This is the reporting
half of the fix, observed on the Windows code path.

### B. `powershell.exe` present, its directory off the PATH — does resolution save the run?

First attempt said both binaries succeeded, and that was the instrument, not the answer: a live
wineserver holds the registry in memory, so editing `system.reg` underneath one changes nothing.
Killed the server, edited, and **checked what a child process actually gets** before believing
any result:

```
PATH seen by a child:   C:\windows\system32;C:\windows;C:\windows\system32\wbem
powershell.exe on disk: yes
```

| | bytes | exit | meaning |
|---|---|---|---|
| stock v3.8.88 | 93 | 2 | silent skip — the bare name resolves through PATH alone, and PATH lost it |
| fixed | 42 | 0 | ran it |

Wine logged the fixed binary's own spawn:
`argv[0] L"C:\\windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"`. **The canonical
path was used, and the run that stock skipped completed.** First evidence for the resolution
half that is not a unit test.

### C. Nothing wrong at all — does the fix disturb the healthy path?

`curl.exe` present, `powershell.exe` present and on PATH: stock and fixed both 42 bytes, exit 0.
With `curl.exe` removed, so the download takes its PowerShell fallback, both again 42 bytes,
exit 0. No regression, and no new output where there was none.

### What run 5 does not establish

- **It does not explain Jeandre's machine.** `where.exe powershell` on her box returns the
  canonical path, so she is not in cell B; the resolution half changes nothing for her. Cell A's
  cause line is what will name her failure, whatever it turns out to be.
- **A non-default `%SystemRoot%` was not visited.** Wine's prefix is `C:\windows`; that branch is
  covered by unit tests only.
- **A launch denied by policy or AV was not simulated.** Wine has no such refusal to offer.
- **Wine is not Windows.** Its `powershell.exe` is a stub that ignores arguments and exits 0, so
  "ran it" in cell B means the process started, not that any PowerShell statement executed.

The prefix was restored after every run and the PATH key read back to confirm it —
`wineserver -k` returns before the server has flushed its registry, and an early restore gets
overwritten. That happened once and was repaired.

## Verification 2026-09-18: the fix against the refreshed fork

The fork (`MichaelC8E/tina4`) had sat **48 commits behind** upstream and was fast-forwarded to
`2bb1418` on 2026-09-18. Question: does the fix still hold against it?

**Yes, and the refresh was load-bearing.**

- `fork/main` and `origin/main` are now the **same commit and the same tree**
  (`2bb1418`, tree `25c3d1b`), and the patch's pre-image blobs match that tree's
  (`src/setup.rs` `e4aa697`, `src/main.rs` `589471a`). *Run.*
- Fresh detached worktree off `fork/main`, the two new test files dropped in **before** the
  patch: `the_repaired_sites_still_resolve_before_spawning`,
  `the_set_of_bare_powershell_spawns_has_not_grown`, `a_spawn_that_never_starts_says_so` and
  `a_child_that_runs_and_fails_says_that_instead` all **FAILED**; only the direction-agnostic
  `no_source_binds_powershell_to_a_name` passed. The instrument can say "no" on this tree. *Run.*
- Same worktree, patch applied from `fix.patch`: **247 passed, 0 failed**,
  `cargo clippy -- -D warnings` **exit 0**. *Run.*
- The counterfactual: **9 of the 48 commits the fork was missing touch `src/setup.rs` or
  `src/main.rs`** — among them `b84b1fe fix(windows): read the skills installer as text, not
  bytes`, `547a9e5 fix(skills): survive a CDN outage`, `e4f852d fix(cli): say what actually
  failed when a download fails`. At the stale tip the blobs are different (`e80fbb6`,
  `45f1602`) and `git apply --check` exits **1**: *patch failed: src/setup.rs:948 … does not
  apply*. Against the refreshed tip it exits **0**. Had the branch been cut from the fork's own
  tip, this fix could not have been written against it at all. *Run.*

**Bounds.** Linux only; this says nothing about Windows behaviour, and nothing about the
reporter's machine. It covers one repo — the other nine checkouts in `tinaforks/` were not
synced or checked. It is a statement about `2bb1418`; any upstream commit after it re-opens the
question. The throwaway worktrees used here (`verify-fork-main`, `stale-c02cb48`) were removed
afterwards; `spawn-fix` (the fix) and `pristine-2bb1418` (the unfixed-source gate) remain.
