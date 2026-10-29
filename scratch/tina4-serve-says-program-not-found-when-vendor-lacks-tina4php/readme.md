# tina4 serve says "program not found" when vendor/ lacks tina4php (f-cli-61, tina4#127)

On a php project where `vendor/` exists but `vendor/bin/tina4php` does not, `tina4 serve` and every delegated command (`tina4 routes`, ...) fail with a spawn error that names neither the file nor the fix:

- Windows: `Could not spawn the php server: program not found` (this is tina4#127; see `../tina4-serve-cannot-find-php-in-a-windows-worktree/release-3.8.107.txt`)
- Linux: `Could not spawn the php server: No such file or directory (os error 2)`

Not Windows-specific. Tested at tina4 `origin/main` `3616f0d` (3.8.107 + merged #125/#126).

## Mechanism

- `start_language_server` php arm (`src/main.rs:1481`) and `delegate_command` (`:1748`) only check that `vendor/` exists.
- `resolve_cli` (`src/main.rs:1641`) then falls back to a bare `tina4php` when neither `vendor/bin/tina4php` nor `bin/tina4php` exists, and that bare name is spawned.
- With a global `tina4php` on PATH (composer global), that one is run instead. On this host it was an old version, and it died with `Class "Tina4\PortTakeover" not found`. So `repro.sh` cuts PATH to `/usr/bin:/bin`.

Why the reporter's `vendor/` lacked the file is not established.

## Reproduction

`repro.sh <tina4 binary>`. Stock (`stock-3616f0d.txt`): both defect cases FAIL. Fixed (`fixed.txt`): all PASS. The controls (no `vendor/` at all; `tina4php` present) pass on both.

## Fix (branch `fix/php-launcher-missing-says-composer-install`, worktree `~/.cache/tina4-worktrees/fcli61`)

`php_launcher_missing()` is true when there is no `vendor/bin/tina4php`, no `bin/tina4php`, and no `tina4php` on PATH. Both entry points check it after the `vendor/` check and print `vendor/bin/tina4php is missing. Run: composer install`. A global `tina4php` is still used when present.

Test: `tests/php_launcher_missing.rs` (serve, routes, global-still-used). Each of the three pieces, reverted alone, turns its test red. Round trip: `composer install` in such a project creates `vendor/bin/tina4php`, and `tina4 routes` then runs.

## Not covered

On Windows, a global composer `tina4php` is a `.bat`. `which` finds it, so no message is printed, but the bare spawn still fails. That is the same as before, and it is the launcher-spawn gap held in f-cli-21.

## Windows (2026-10-26)

Built on the Windows 11 guest from this branch. Use WinLibs gcc on PATH: rustup's self-contained mingw now fails to link with `cannot find -lktmw32`. `tests/php_launcher_missing.rs` passes there (2/2; the global-tina4php test is unix-only). `probe.ps1` case C now prints `vendor\bin\tina4php is missing. Run: composer install` (`windows-fixed.txt`), and cases A, B, D and E are unchanged (200).
