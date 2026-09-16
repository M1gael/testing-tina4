# `tina4 serve` cannot spawn `npx` on Windows, so a tina4js project never starts

`2026-09-16 · tina4 CLI origin/main 6a9b68e = 3.8.87 · which 7.0.3 (Cargo.lock) ·
reported on Windows, node v24.13.0, npm 11.6.2, vite 8.3.0 ·
Linux control on rustc 1.98.0, node v22.22.2`

Ledger row: `f-cli-20`.

## The behaviour

Reported from a Windows tina4js project, with `node_modules` present:

```
PS C:\Users\caleb\projects\tina4-pwa\pwa-frontend> tina4 serve
✓ Detected tina4js project
▶ Starting vite on 0.0.0.0:5173
  ✗ Could not spawn the tina4js server: program not found
✗ Failed to start the tina4js server. See the error above.
```

## The mechanism

`src/main.rs:1249`, the `"tina4js"` arm of `start_language_server`:

```rust
let mut cmd = std::process::Command::new("npx");
cmd.args(["vite", "--port", &port_s, "--host", host, "--strictPort"])
```

Windows' `CreateProcess`, which `std::process::Command` uses, appends only `.exe` to a bare
program name. It never reads `%PATHEXT%`. Node ships `npx` as `npx.cmd` and there is no
`npx.exe`, so the lookup fails before any syscall and Rust returns its Windows-only
`program not found` — no errno, because nothing was ever asked of the kernel. The error is
printed at `src/main.rs:1266`.

The CLI already carries the fix. `console::resolve_cmd` (`src/console.rs:205`) is
`which::which()`, and `which` 7.0.3 does read `%PATHEXT%` (`finder.rs:195-255`,
`#[cfg(windows)] fn append_extension`). Its own doc comment at `src/console.rs:203` states the
trap in as many words. **Eighteen lines above the broken site, `src/main.rs:1231` uses it.**

`5a79cfd` (v3.8.0) introduced `resolve_cmd` and converted exactly two call sites in `main.rs`
— `bundle` and the Node.js `npx`. The tina4js arm was missed. It has been bare since
`ce98a47` (2026-04-02), the commit that added tina4js support, and appears bare in all 126
tags that contain it, so no released version has ever started vite on Windows.

Three more sites spawn whatever launcher `resolve_cli` returns, which is a bare `"npx"`
(`main.rs:1320`) or `"bundle"` (`main.rs:1312`):

| Site | What breaks |
|---|---|
| `main.rs:1149` | managed serve for a Node.js or Ruby project |
| `main.rs:1341` | `delegate_command` — every forwarded subcommand |
| `manifest.rs:103` | `commands --json`, and `.ok()?` swallows the error, so the delegated commands vanish from `tina4 --help` with no reason given |

`resolve_cli:1319` checks `which::which("npx").is_ok()` — the PATHEXT-aware lookup — and then
hands back a bare name for a PATHEXT-blind spawn.

## Why the output alone does not prove it

`program not found` is identical whether the CLI cannot resolve `npx` or `npx` is genuinely
absent from `PATH`. Two runs on the reporter's machine separated them.

**Same cmd.exe session, consecutive, same directory:**

```
C:\Users\caleb\projects\tina4-pwa\pwa-frontend>npx vite --version
vite/8.3.0 win32-x64 node-v24.13.0

C:\Users\caleb\projects\tina4-pwa\pwa-frontend>tina4 serve
✓ Detected tina4js project
▶ Starting vite on 0.0.0.0:5173
  ✗ Could not spawn the tina4js server: program not found
```

The shell resolves `npx` through `%PATHEXT%` and runs it. The CLI, in the same process
environment, cannot. That is both directions of the causation in two commands. It also rules
out a stale `PATH` in the original PowerShell window, which would have failed identically.

**`tina4 doctor`, same window**, closes the other half — that `resolve_cmd` would actually
work there:

```
  Node.js      ✓ 24.13.0     ✓ npm        11.6.2
  ✓ tina4nodejs      Node.js      installed (global)
```

- `✓ npm 11.6.2` comes from `doctor.rs:308 check_tool`, which spawns through
  `resolve_cmd`. So `Command::new(<resolved path>)` runs a `.cmd` on that machine.
- `✓ tina4nodejs installed (global)` comes from `doctor.rs:158`, a bare
  `which::which("tina4nodejs")`. npm's global directory holds `tina4nodejs.cmd` beside an
  extensionless shim, and `which` 7.0.3 requires `path.extension().is_some() || matches_arch(..)`
  (`checker.rs:76`), where `matches_arch` is `winsafe::GetBinaryType` (`checker.rs:110`) and
  refuses a non-PE script. The extensionless shim was rejected, so the `Ok` came from PATHEXT
  inference finding the `.cmd`. **Bare-name `.cmd` resolution works on that machine.**

Note also that the same `doctor` run reports `✓ vite  tina4js  installed (project)` while
`serve` cannot launch it. The CLI's own diagnostic contradicts the CLI's own behaviour.

## The Linux control

The defect cannot be reproduced on Linux — `execvp` searches `PATH`, so a bare `npx` resolves.
`control/` is the minimal project that reaches the same code path, with a stub standing in for
vite so nothing is fetched:

```
cd control && <tina4> serve
✓ Detected tina4js project
▶ Starting vite on 0.0.0.0:5173
VITE-STUB-SPAWNED args=--port 5173 --host 0.0.0.0 --strictPort
```

Identical on the unfixed and the fixed binary. Its job is to show the arm is live, that these
are the exact arguments `:1250` builds, and that the fix does not regress the platform that
already worked.

## The fix

`fix.patch` — four one-line changes, each the shape already used at `main.rs:1178`, `:1219`,
`:1231`, `:1818`, `:1823`, `:1828` and `init.rs:266`. `delegate_command` keeps the logical
name for its error message and resolves only for the spawn, exactly as `run_cmd_in` does.

`resolve_cmd` falls back to the name unchanged when lookup fails
(`console.rs:208 unwrap_or_else`), so nothing changes when the program is genuinely absent.

Branch: `fix/serve-resolves-npx-so-tina4js-starts-on-windows` in `../tinaforks/tina4`,
cut from `origin/main` `6a9b68e`. Uncommitted.

## The regression test

`windows_spawn_resolution.rs` (goes in `tests/`). `cargo test` runs on ubuntu only and the
failure cannot be reproduced on Linux, so the gate is on the shape of the code, not the
behaviour — the only regression test this defect admits without a Windows host. It follows
`deploy.rs::no_npx_in_a_production_cmd`, which bans a string for the same kind of reason.

Each of the four changes was reverted on its own and turns the suite red on its own:

| Reverted | Red |
|---|---|
| `main.rs:1249` npx | `tina4js_serve_resolves_npx`, `no_pathext_dependent_program_is_spawned_by_bare_name`, `every_spawn_is_either_resolved_or_known_safe` |
| `main.rs:1149` | `every_spawn_is_either_resolved_or_known_safe` |
| `main.rs:1341` | `every_spawn_is_either_resolved_or_known_safe` |
| `manifest.rs:103` | `every_spawn_is_either_resolved_or_known_safe` |

`the_scan_still_finds_the_spawns` exists because a source-scanning test whose parser returns
nothing passes every other assertion in the file. Blinding the parser was tried: the two gates
went green and only the self-check caught it.

## What this does NOT cover

- **Nothing here was run on Windows.** No wine, no mingw, no Windows Rust target on this
  machine. The Windows behaviour is the reporter's, run on a released binary; the fix is
  verified only by reading and by the Linux control.
- If `%PATHEXT%` is unset, `which` gets an empty extension list
  (`finder.rs:227 unwrap_or_default`) and `resolve_cmd` does not help either.
- Rust ≥1.77.2 routes a `.bat`/`.cmd` through `cmd.exe` and refuses arguments it cannot escape
  safely. `--host` is user-supplied; a host containing a quote would now fail differently.
  Not reached here, pre-existing class.
- `install.rs:315` spawns a bare `gem`, and `install_tina4_cli("tina4ruby", "gem", ..)` beside
  it. Same mechanism, different subsystem, separately reported — deliberately left out of this
  fix and out of the test's scope.
- The PHP and Ruby serve arms on Windows were not exercised.
- `tina4-js`'s own `bin/tina4.js` was never checked for the same pattern.
