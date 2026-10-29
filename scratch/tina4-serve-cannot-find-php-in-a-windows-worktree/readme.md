# tina4 serve cannot find php in a Windows worktree (tina4#120)

**Question:** on Windows, why does `tina4 serve` for a php project fail with `Could not spawn the php server: program not found` while `where php` and `tina4 doctor` still find php?

Tested on: tina4 CLI 3.8.106 (`origin/main` `0b92b43`), Windows 11 VM, PHP 8.4.25 NTS, MinGit 2.56.0, Composer 2.10.3, tina4php 3.13.154.

## Answer

The issue says Rust's bare-name program search depends on the current directory. It doesn't:
`std/src/sys/process/windows.rs` (`resolve_exe` / `search_paths`) searches the child's PATH, then the folder of the running exe, then the system folders, then the parent's PATH. It never looks in the current folder. *(read)*

With a real `php.exe` on PATH, `tina4 serve` works from both a normal checkout and a linked worktree. *(run: `prove.ps1`)*

The same error, with `tina4 doctor` still reporting PHP as fine, comes from two setups *(run: `probe.ps1 -Where wt|repo`)*:

| Case | Normal checkout | Worktree |
|---|---|---|
| A: `php.exe` on PATH | serves (200) | serves (200) |
| B: php reachable only through a `php.bat` shim | **program not found** | **program not found** |
| C: `vendor\bin\tina4php` missing | **program not found** | **program not found** |

Why each case fails:
- `doctor` passes in every case because `doctor.rs:336` resolves the name through `which` (`console::resolve_cmd`), which honours PATHEXT (`.bat` and `.cmd`).
- `serve` spawns the bare name (`src/main.rs:1496`, using `resolve_cli` at `:1651`/`:1653`). Rust's own search only appends `.exe`.
- Case C makes `resolve_cli` fall back to a bare `tina4php`. Each worktree has its own `vendor\`, so this is the only cause found that can differ between a checkout and its worktree.

## What it means

- The suggested fix, `console::resolve_cmd("php")`, covers cases B and D. That is confirmed on Windows: see "Fix and proof" below.
- The fix does not cover case C.
- It is the same fix as our held `f-cli-21`.
- To tell which case the reporter has, ask for `where php` and `dir vendor\bin`, run from the failing worktree.

## Side finding

`.env` is gitignored, so a new worktree has none, and `tina4 serve` there stops at `Auth: TINA4_SECRET is not set`. That's by design, but it is the next error anyone serving from a worktree will hit.

## Fix and proof (2026-10-26)

The fix wraps `console::resolve_cmd` around the three spawns of the launcher that `resolve_cli` returns:
- `src/main.rs:1496` (php serve)
- `src/main.rs:1756` (delegated subcommands)
- `src/manifest.rs:109`

It also adds the source-scan regression test `tests/windows_spawn_resolution.rs`.

Stock and fixed were built from the same commit (`0b92b43`) with the same toolchain on the guest (`build-fixed.ps1`, rustup windows-gnu plus WinLibs). The raw output is in `before-after.txt`.

| Case | Stock | Fixed |
|---|---|---|
| A `php.exe` on PATH | 200 | 200 |
| B php only through `php.bat` | program not found | 200 |
| C `vendor\bin\tina4php` missing | program not found | **program not found** (not covered) |
| D `php.bat` in a folder with spaces | program not found | 200 |
| E `php.cmd` ahead of `php.exe` | 200 | 200 |
| `tina4 routes`, php only through `php.bat` | `Failed to run php vendor\bin\tina4php routes: program not found` | exit 0 |

Each row was identical in the normal checkout and in the linked worktree.

## The published 3.8.107 binary (tina4#127, 2026-10-26)

tina4#127 says the released `tina4-windows-amd64.exe` for 3.8.107 was built before #121. It was not. The published exe (`dl-3.8.107.ps1`: SHA256 `1ac136bc…`, matching `SHA256SUMS` and the issue's hash) was run through `probe.ps1`, and the output is in `release-3.8.107.txt` *(run)*:

| Case | release 3.8.106 | release 3.8.107 |
|---|---|---|
| A `php.exe` on PATH | 200 | 200 |
| B php only through `php.bat` | program not found | 200 |
| C `vendor\bin\tina4php` missing | program not found | program not found |
| D `php.bat` in a folder with spaces | program not found | 200 |
| E `php.cmd` ahead of `php.exe` | 200 | 200 |

B and D are what #121 fixes, and 3.8.107 passes both, so the shipped binary does contain #121. The reporter's setup (a real `php.exe` on PATH; works in the checkout, fails in the worktree) is case C. Case A never failed, even on 3.8.106. A new worktree has no `vendor\` because it is gitignored, so `resolve_cli` falls back to a bare `tina4php`. The fix is to run `composer install` in the worktree. To confirm, run `dir vendor\bin` in the failing worktree. *(inferred for the reporter's machine)*
