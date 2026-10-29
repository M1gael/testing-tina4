# Termux (Android) cannot install or use the tina4 CLI

Ledger: `f-cli-38` (CLI), `d-site-01` (docs). Trees: tina4 `05dc716` (main), tina4-documentation
`018b4f1` (main), both fetched 2026-10-20. Test bed: Android 14 x86_64 emulator, Termux 0.118.3
(GitHub build), see `/var/home/work/vm/README.md` (2026-10-20 section). Every result below ran over
SSH into Termux's own sshd, i.e. as the app (`untrusted_app_27`), not via `run-as`.

## What was absent (stock)

- `curl -fsSL https://tina4.com/install.sh | sh` on Termux: detects `linux/amd64`, then
  "Need sudo to install to /usr/local/bin" / "sudo: not found". The served script is
  `tina4-documentation/docs/public/install.sh`, a hand-synced copy that is two commits behind
  `tina4/install.sh` (`ca00db4`, `66d3dd5`, 2026-10-17, which already detect Termux).
- Even the current `tina4/install.sh` finds nothing on x86_64 Android: the release publishes
  `tina4-android-arm64` only. glibc `tina4-linux-amd64` cannot exec (no `/lib64/ld-linux`);
  `tina4-linux-musl-amd64` dies with SIGSYS.
- With a working binary (built here with the NDK), on a fresh Termux:
  `tina4 install php|ruby|nodejs` know only choco/brew/sudo apt/NodeSource and fail (exit 0
  regardless); `tina4 init php|ruby|nodejs|python` exit 1 when the runtime is missing (no `pkg`
  path); composer's fallback targets `/usr/local/bin` and fails silently.
  `gate-stock.txt`, `gate-fixed.txt` (stock python row): all four languages FAIL the gate.
- Ruby, even with the runtime present: `bundle install` cannot build the `sqlite3` gem (no
  Android precompiled gem; the source build needs `mini_portile2`).
- `tina4python` lands in `~/.local/bin`, which Termux never puts on PATH.
- Every `uv` tina4 starts warns "Failed to hardlink files": Android denies apps `link()`
  (`ln` -> Permission denied). `UV_LINK_MODE=copy` silences it (0 vs 2 warnings).

## The change (uncommitted)

`~/.cache/tina4-worktrees/android-cli` (branch `feat/android-x86_64-termux`), patch also at
`~/.cache/tina4-worktrees/android-cli.fix.patch`:

- `install.rs`: `termux_packages()` / `termux_install()`; php/composer, ruby, nodejs install via
  `pkg` on Android; `termux_ruby_build_config()` (sets `build.sqlite3 --enable-system-libraries`
  globally, installs `libsqlite` if its header is missing); `termux_local_bin_on_path()`
  (`uv tool update-shell` after installing tina4python).
- `init.rs`: missing runtime, uv and composer install via `pkg` on Android; ruby build config.
- `setup.rs`: git via `pkg` on Android.
- `doctor.rs`: codeql row says it is not available on Android instead of `brew install codeql`.
- `main.rs`: `UV_LINK_MODE=copy` on Android unless the user set it.
- `release.yml`: `x86_64-linux-android` target -> `tina4-android-amd64` (cargo-ndk, API 24),
  added to both expected-asset lists. Not run: needs a release.
- README: Android (Termux) install section. Unit tests: package lists, x86_64 asset name.

`~/.cache/tina4-worktrees/android-docs` (branch `docs/android-termux-install`), patch at
`~/.cache/tina4-worktrees/android-docs.fix.patch`: `docs/public/install.sh` synced from tina4
main; Android (Termux) install text on get-started, general/cli, index, install-security.

## The gate

`gate.sh <binary> [langs]` - per language, a freshly reinstalled Termux, then `tina4 init`,
`tina4 serve` (HTTP 200 + tina4 page), `tina4 install`, package manager present right after
install, `tina4 doctor` from a new login shell (runtime, manager and tina4<lang> ✓; php's CLI
excluded because `install php` only prints a hint everywhere), no hardlink warnings.
`ORDER=install-first` swaps install before init. `PRE=` starts from a given state.

Component gating: `mutate.py` reverts one piece and rebuilds; `gate-components*.sh` run each
mutant on the cell that exercises it. Results in `gate-components.txt`, `gate-components-2.txt`.
Setup and installer runs: `setup-run.sh` (real interactive `tina4 setup` via `drive.py`, a pty
driver that answers each prompt only when it appears), `installer-run.sh` (hosted script against a
local release copy serving `tina4-android-amd64`). Everything chained: `final-run.sh` ->
`final-run.txt`.

## Open

- arm64 Android: the arm64 build compiles; not run (x86_64 emulator).
- iSH (iOS): supported upstream (`66d3dd5`), not tested here.
- `install-security.md` says the installer "prints the next command"; `install.sh` actually
  launches `tina4 setup` when a terminal is attached. Pre-existing, not changed.
