# `tina4 update` reports a skills-refresh failure with no reason, on Windows

**Pinned:** tina4 CLI **3.8.87** (released `tina4-linux-amd64`, sha256 verified), CLI source
`origin/main` **`6a9b68e`**, `tina4-documentation` `origin/main` **`a5fc43f`**. Probed
2026-09-16 from Linux. Reported by @jeandre on Windows, screenshot only, no timestamp.

**Reproduced again 2026-09-17 on 3.8.88** (`2bb1418`). `src/setup.rs` is byte-identical between
`v3.8.87` and `v3.8.88`, so the two runs exercise the same code — see *Run 3* below, which
locates the failure at the spawn.

`./probe.sh` — 0 chain healthy and Content-Type correct, 1 something is wrong.

## What was reported

```
▶ Refreshing Tina4 AI skills for all...
  ▶ Installing tina4 AI skills for all...
  ⚠ Skills install skipped — run later: tina4 ai
⚠ Tina4 skills refresh failed; the client update is still complete.
```

Nothing between "Installing…" and the skip. No cause.

## The root cause was already found and fixed upstream

`tina4-documentation` `48716f3`, 2026-09-14 11:31 SAST, *"fix(skills): Windows
install-skills.ps1 shim choked on a byte[] from iex"*. On Windows PowerShell 5.1
`Invoke-WebRequest(...).Content` returns `System.Byte[]` when the server sends a non-text
Content-Type. tina4.com sent none, jsDelivr sends `application/octet-stream`. The shim got a
`byte[]`, **treated it as truthy success**, broke out of the retry loop, never reached the
`raw.githubusercontent` fallback that would have worked, and `Invoke-Expression` then refused
it.

The shim half of that fix is live — the decode is in the file tina4.com serves today.

## Still wrong: the other half of that fix is not in effect

`48716f3` was two layers. The second was *".htaccess forces `text/plain; charset=utf-8` for
.ps1/.sh"*. Measured 2026-09-16:

| URL | Content-Type |
|---|---|
| `tina4.com/install-skills.ps1` | **none** |
| `tina4.com/skills/3.13.137/install-skills.ps1` | **none** |
| `tina4.com/install-skills.sh` | `text/x-sh` |
| `cdn.jsdelivr.net/...@3.13.137/install-skills.ps1` | `application/octet-stream` |
| `raw.githubusercontent.com/.../3.13.137/install-skills.ps1` | `text/plain; charset=utf-8` |

So the manual path the file's own header advertises is still broken on PowerShell 5.1:

```powershell
$env:TINA4_SKILLS_TARGET = "claude"; irm https://tina4.com/install-skills.ps1 | iex
```

`irm` returns `byte[]`, `iex` refuses it. The shim's internal decode cannot help — that failure
happens before any of the shim's code runs. The CLI path is unaffected: it downloads to a file
and reads it with `[System.IO.File]::ReadAllText`.

## Why the report carried no reason — the reason the screenshot is useless

The two bootstraps do not report alike.

`install-skills.ps1`, live at tina4.com, discards every download error:

```powershell
} catch {
  if ($attempt -lt 3) { Start-Sleep -Seconds 2 }
}
```

`install-skills.sh` prints curl's own error and then its own:

```sh
if ! curl -fsSL --retry 3 --retry-delay 2 "$tina4_url" -o "$tmp" && ... ; then
  echo "error: could not download the Tina4 skills installer from any source" >&2
```

Run here, stock 3.8.87, single factor `TINA4_SKILLS_REF=0.0.0-nope`, HOME redirected:

```
  ▶ Installing tina4 AI skills for all...
curl: (22) The requested URL returned error: 404
curl: (22) The requested URL returned error: 404
curl: (22) The requested URL returned error: 404
error: could not download the Tina4 skills installer from any source
  ⚠ Skills install skipped — run later: tina4 ai
```

Four cause lines on Linux, none on Windows, same CLI code. `src/setup.rs:1023-1028` adds
nothing of its own — the other two skip sites at `:964-971` and `:995-1002` print their cause,
this one cannot, because `run_status` (`src/setup.rs:1717-1725`) maps both a spawn failure and
a non-zero exit to a bare `false` via `.unwrap_or(false)`.

## Control: the chain is healthy today

Stock 3.8.87, HOME redirected to a throwaway seeded with a stub skill in
`.claude/skills`, `.agents/skills`, `.cursor/skills`:

```
  verified 48 skill files against skills.sha256 (ref 3.13.136)
  installed for <fake>/.claude/skills
  installed for <fake>/.agents/skills
  installed for <fake>/.cursor/skills
  Done - eight skills installed for all (ref 3.13.136).
EXIT=0
```

## Control 2, on the reporter's own Windows box (2026-09-17)

@jeandre ran the four-line manual shim and it succeeded:

```powershell
$env:TINA4_SKILLS_TARGET='all'
$p = "$env:TEMP\tina4-shim.ps1"
Invoke-WebRequest -UseBasicParsing -Uri 'https://tina4.com/install-skills.ps1' -OutFile $p
iex ([System.IO.File]::ReadAllText($p))
```

```
  Target: all  (ref: 3.13.136)
  verified 48 skill files against skills.sha256 (ref 3.13.136)
  installed for C:\Users\jeann\.claude\skills
  installed for C:\Users\jeann\.agents\skills
  installed for C:\Users\jeann\.cursor\skills
  Done - eight skills installed for all (ref: 3.13.136).
```

**This is a control, not a reproduction.** `-OutFile` + `ReadAllText` is the same type-safe path
the CLI takes internally, so it deliberately steps around the `irm | iex` failure this project
is about. It does **not** show the Content-Type defect is gone — `probe.sh` re-run the same day
still exits 1, `Content-Type` still absent.

What it does establish, on that machine: reachability of tina4.com, shim content and decode,
the checksum step, the ref (3.13.136 — unchanged since the 2026-09-16 measurement), and write
access to all three tool directories. Everything downstream of the spawn is healthy.

What is left as the cause of the original silent skip is therefore either stale content from
before `48716f3`, or a failure to spawn PowerShell at all.

## Run 3, the discriminator (2026-09-17): it is the spawn

Same box, CLI **3.8.88**, immediately after Control 2 succeeded:

```
PS C:\Users\jeann> tina4 update
> Checking for updates...
  i Current: 3.8.88  Latest: 3.8.88
  / CLI already up to date
> Refreshing Tina4 AI skills for all...
  > Installing tina4 AI skills for all...
  ! Skills install skipped - run later: tina4 ai
! Tina4 skills refresh failed; the client update is still complete.
```

`setup.rs` is byte-identical between `v3.8.87` and `v3.8.88` (`git diff --quiet v3.8.87
origin/main -- src/setup.rs` exits 0), so this is the same code that produced the first report.

### Two of the three skip sites are ruled out by what is *absent*

| Site | What it prints on failure | Seen? |
|---|---|---|
| `setup.rs:965` `skills_stage_dir` | `Could not create a temporary directory for the skills installer - ...` | no |
| `setup.rs:995` `fetch_skills_installer` | `Could not download the skills installer - ...` | no |
| `setup.rs:1023` after `run_status` | nothing of its own | **this one** |

So the stage directory was created and the 2339-byte bootstrap reached disk. The only remaining
failure is `run_status("powershell", ...)` at `:1007-1013` returning `false`.

### And PowerShell never ran a statement

`run_status` inherits **both** stdout and stderr (`setup.rs:1717-1725`), and every failure
reachable *inside* PowerShell writes something:

- the bootstrap's own give-up is `throw "Could not download the Tina4 skills installer from
  either source."` — a red error under `$ErrorActionPreference='Stop'`
- the inner installer prints `Tina4 Skills Installer` / `Target: ...` before it does anything
- a parse error, an execution-policy refusal, or a ConstrainedLanguage block on
  `[System.IO.File]::ReadAllText` all print

**Zero bytes crossed that gap.** The process never launched, or was killed before its first
statement.

### Mechanism (read + inferred — no Windows here)

`powershell.exe` does not live in `System32`. It lives in
`System32\WindowsPowerShell\v1.0\`. `CreateProcess` given a bare program name searches the
application directory, the current directory, `System32`, the Windows directory, and then
`PATH` — so bare `Command::new("powershell")` can only resolve **via `PATH`**. An inherited
`PATH` that has lost `%SystemRoot%\System32\WindowsPowerShell\v1.0\` fails the spawn.

Her own interactive PowerShell session is *not* evidence against this: Explorer launches it by
full path, never by a `PATH` lookup.

Application Control, AppLocker or AV denying or killing the launch fits the same evidence
exactly. Every one of them is invisible for a single reason — `.unwrap_or(false)` throws the
`io::Error` away.

### The probe was run, and PATH is not the cause

```powershell
PS C:\Users\jeann> where.exe powershell
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
```

**The PATH hypothesis is dead.** `PATH` carries the PowerShell directory, the canonical file is
present, and `CreateProcess` given the bare name resolves it. Nothing about resolution would
change on that machine.

The mechanism above is still correct *as a description of how a bare-name spawn resolves* — it
is simply not what is happening here. That distinction matters: the resolution hardening is now
a fix for a case nobody has observed, and should be judged on its own, not on this report.

### What survives

1. The launch is denied — Application Control / AppLocker / AV refusing to start the process.
2. It launches and is killed before executing its first statement.

ConstrainedLanguage is excluded by measurement (Run 3 above: it prints 131 bytes). Both
survivors are invisible for the one reason this project started with: `.unwrap_or(false)` throws
the `io::Error` away.

### The next probe: the CLI's exact spawn, by hand

If this succeeds, the elimination that put the failure at the spawn is wrong somewhere, and the
investigation goes back to stage 1.

```powershell
$d = Join-Path $env:TEMP "tina4-probe"
New-Item -ItemType Directory -Force -Path $d | Out-Null
C:\Windows\System32\curl.exe -fsSL -o "$d\install-skills.ps1" https://tina4.com/install-skills.ps1
Write-Output "downloaded $((Get-Item "$d\install-skills.ps1").Length) bytes"
& powershell -NoProfile -Command "`$ErrorActionPreference='Stop'; `$env:TINA4_SKILLS_TARGET='all'; iex ([System.IO.File]::ReadAllText('$d\install-skills.ps1'))"
Write-Output "exit $LASTEXITCODE"
```

### Note on the fix

This is the same bare-spawn family as `f-cli-21`, but `console::resolve_cmd` would **not**
close it: `which` searches `PATH` too, so it fails wherever `CreateProcess` fails. The Windows
arm needs an absolute fallback to
`%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`, preferring `pwsh` when present —
and, separately, `run_status` has to surrender the `io::Error` so the skip line can say why.

## No ordering gap this time

The bootstrap moved to ref `3.13.137` in `ea0a9e4`, 2026-09-14 11:46 SAST = **09:46 UTC**. The
tag `3.13.137` was created in `tina4stack/tina4` at **09:45:31 UTC** — one minute earlier. Tag
first, then the pin. [[skills-ref-tagged-after-the-release]] did not recur.

## Not established

- **Which spawn-side cause it is.** `PATH` missing the PowerShell directory, and Application
  Control / AppLocker / AV refusing the launch, produce identical output today. `where.exe
  powershell` separates them and has not been run.
- **Whether the process launched and died, or never launched.** `run_status`
  (`src/setup.rs:1717-1725`) maps a spawn `io::Error` and a non-zero exit to the same bare
  `false`. The distinction does not change the fix, and cannot be recovered from the screenshot.
- **Windows was still not run here.** No Windows host, no `pwsh`. The `CreateProcess` search
  order and the location of `powershell.exe` are read, not measured on that box.
- **The original 2026-09-16 report is now moot as a dating question.** It reproduces on current
  code with current content, so whether it predated `48716f3` no longer matters.
- **Windows was not run here.** No Windows host, and no `pwsh` on this machine. Every Windows
  claim is read from the source or taken from `48716f3`'s own verification note.
- `exit 0` from `tina4 update` after a failed refresh is deliberate — the message says the
  client update is still complete.
