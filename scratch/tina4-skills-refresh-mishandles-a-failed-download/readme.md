# `tina4 update` mishandles a transient CDN outage during the skills refresh

Reported 2026-09-08 from Windows PowerShell: `tina4 update` upgraded the CLI
3.8.83 → 3.8.84, then dumped a red `Invoke-RestMethod` exception —
`503 Backend.max_conn reached`, `Error 54113`, `Varnish cache server` — and
finished with *"Skills skipped"* / *"the client update is still complete"*.

Run `./prove.sh` for the stock half; pass a fixed build as `$1` for the other.
Exits 0 when everything below still holds. It needs the network, and it says
`skip` rather than `FAIL` for any check whose CDN is not serving at that moment
— during the first full run raw.githubusercontent.com went down and came back
mid-suite, which is exactly the condition under test.

**Versions.** Stock evidence is the released **3.8.84** `tina4-linux-amd64`
(`bin/tina4-3.8.84`), the version the reporter landed on. `src/setup.rs` at
`origin/main` (`197e90c`) is byte-identical to `v3.8.84`, so the source read
here is the source that binary was built from. Fixed build is
`fix/skills-refresh-survives-a-transient-cdn-outage`, cut from `origin/main`.

## The 503 is real, ongoing, and not the reporter's machine

20 probes, 5 seconds apart, 2026-09-08 08:06–08:08Z, from a different continent
than the reporter (`evidence/cdn-probe.log`):

| host | result |
|---|---|
| `raw.githubusercontent.com/.../install-skills.sh` | **200 ×14, 503 ×6** |
| `cdn.jsdelivr.net/gh/tina4stack/tina4@main/install-skills.sh` | 200 ×20 |

The 503 body is byte-for-byte the reporter's: `<title>503 Backend.max_conn
reached</title>`. Six of them were consecutive, so the outage window was at
least 30 seconds. This is the Fastly/Varnish tier in front of
raw.githubusercontent.com, and nothing about it is ours to fix.

What *is* ours is that one fetch out of the whole flow has no answer for it.

## Two defects, not one

### 1. The bootstrap is the only unarmoured download in the chain

`install-skills.sh` and `install-skills.ps1` are careful about exactly this
failure. Both take `TINA4_SKILLS_RETRY_COUNT` (default 3), both carry a
`mirror_root` of `https://cdn.jsdelivr.net/gh/tina4stack`, and every skill file
they pull tries the primary and then the mirror
(`install-skills.sh:26-29,49-58`, `install-skills.ps1:15-18,46-61`).

The one-line bootstrap that fetches *those scripts* has neither:

```rust
// src/setup.rs:834  (Windows)
"$env:TINA4_SKILLS_TARGET='{target}'; irm https://raw.githubusercontent.com/tina4stack/tina4/main/install-skills.ps1 | iex"
// src/setup.rs:840  (macOS / Linux)
"curl -fsSL https://raw.githubusercontent.com/tina4stack/tina4/main/install-skills.sh | TINA4_SKILLS_TARGET={target} sh"
```

One host, one attempt. Measured against a 503:

```
the bootstrap in setup.rs (curl -fsSL)        attempts=1 exit=22
install-skills.sh's own downloads (--retry 3) attempts=4 exit=22
```

The 503 killed the fetch of the script that knows how to survive a 503.

### 2. On macOS and Linux the failure is invisible — the refresh reports success

This one is worse than what the reporter saw, and it is why the report is worth
more than "GitHub had a bad minute".

A pipeline exits with the status of its **last** command. `curl -f` writes
nothing to stdout on a 503 and exits 22; `sh` reads that empty stdin, runs
nothing, and exits **0**. `run_status` (`src/setup.rs:1416`) is
`.status().map(|s| s.success())`, so it returns `true`, `if !ok`
(`src/setup.rs:843`) never fires, and neither does the `Tina4 skills refresh
failed` line in `refresh_installed_skills` (`src/main.rs:1742`).

Stock 3.8.84, `tina4 skills claude`, same command twice, only the network varied:

| | files installed | exit code | what it said |
|---|---|---|---|
| CDN 503 | **0** | **0** | one `curl: (22)` line, nothing from the CLI |
| CDN fine | 48 | 0 | full success output |

The exit code cannot tell those apart. On the reported entry point,
`tina4 update`, the run reaches `refresh_installed_skills` (`src/main.rs:1598`
on the already-current path, `:1678` after an upgrade) and says nothing at all.

Windows was the *lucky* platform. PowerShell exits non-zero when `irm` throws,
so `run_status` saw the failure and the warning printed. The reporter got an
ugly twenty-line .NET exception — but they got the truth. A Linux or macOS
colleague running the same command in the same minute would have been told
nothing and left with stale skills.

## Causation, both directions

Single factor: where in the pipeline the failure happens.

```
fetch ok, script exits 2   -> pipeline status 2    the CLI DOES see this
fetch fails, nothing runs  -> pipeline status 0    the CLI CANNOT see this
```

So `run_status` is not broken in general — it is blind precisely to a failed
download, which is the only failure a CDN outage produces. And with the primary
503ing, `install-skills.sh` run directly falls back to jsDelivr and installs 48
files, exit 0: the outage was survivable the whole time.

## Retrying alone would not have saved this run

Worth stating, because "add `--retry`" is the obvious patch. The measured outage
ran at least 30 seconds. Three attempts two seconds apart span about six. The
**mirror** is what does the work here; the retry only covers a single bad
packet. The fix keeps both, because they cover different failures.

## What the fix changes

Branch `fix/skills-refresh-survives-a-transient-cdn-outage`, uncommitted.
`src/setup.rs` only.

- **Two sources.** `SKILLS_INSTALLER_SOURCES_SH` / `_PS1` — raw.githubusercontent
  then the jsDelivr mirror the installer scripts already trust. Verified the
  mirror serves identical bytes (both 6474 bytes, same sha256).
- **Three attempts per source**, two seconds apart — the installer's own numbers.
- **A 60-second budget** on the whole walk. `curl` is invoked without a timeout
  here, as everywhere else in this client, so six attempts where there was one
  could multiply a hang by six. Once the budget is spent no further attempt
  starts.
- **Download first, run second.** The installer is fetched to a private staging
  directory and then executed, so the download's own exit status is checked
  instead of being swallowed by a pipeline.
- **Say which source failed and why**, reusing `download_file_classified` and
  `FailureCause` from `src/main.rs` — the classifier the `f-cli-05` work added
  for exactly this kind of message.

Deliberately **not** changed:

- `install-skills.sh` / `.ps1` — already correct. The defect is upstream of them.
- `download_file_classified` itself, and the release-asset walk in
  `download_file`. That walk stops on a local failure because it tries different
  asset *names* on one host. The installer walk keeps going, because these are
  two different hosts and "cannot reach raw.githubusercontent.com" says nothing
  about jsDelivr. Same helper, opposite rule, commented as such.
- Windows still runs the script through `iex` over the file's contents, not
  `-File`. `-File` on a downloaded `.ps1` has to clear the execution policy and
  the mark-of-the-web; a string handed to `iex` clears neither, because neither
  applies to it. Only where the bytes come from changed.
- `SKILLS_INSTALL_URL` at `src/doctor.rs:10` points at
  `https://tina4.com/install-skills.sh`, which serves a **different, shorter**
  script (1907 bytes vs 6474). Left alone — see *Still open*.

## Which components gate

Each reverted on its own against the fixed build; each turns the suite red by
itself.

| reverted | goes red |
|---|---|
| **A** mirror URL → duplicate primary | mirror fallback, "reported the last source it tried" |
| **B** whole `install_skills_target` → shipped pipe | exit code, named failure, `tina4 update` reporting, attempt count |
| **C** `SKILLS_FETCH_ATTEMPTS` 3 → 1 | attempt count (2 instead of 6) |
| **D** `SKILLS_FETCH_BUDGET` 60s → a day | slow-CDN early stop |

Fixed build, all checks:

```
fixed, both CDNs 503: files installed (0)         exit code (2, non-zero)
fixed, both CDNs 503: named the failure           reported the last source it tried
fixed, primary 503 only: installed from the mirror (48 files), exit 0
fixed, network fine: 48 files, exit 0
fixed, installer itself fails (bad TINA4_SKILLS_REF): exit 2
fixed update: the update run now reports the failed refresh
fixed: fetch attempts before giving up (6)
fixed, slow + broken CDN: stopped early (5 attempts, 68s), said it gave up
fixed: staging directories left behind (0)
```

## Residual gaps

- **Windows is unverified by running.** No PowerShell on this machine. The
  Windows branch was changed and read, not executed. What is known from the
  reporter's screenshot is that the shipped Windows path *does* exit non-zero on
  a failed `irm` — the silent-success half is Unix-only. The new
  `$ErrorActionPreference='Stop'` guard exists because a failed `Get-Content`
  would otherwise hand `iex` a null and exit 0, recreating the Unix bug on
  Windows; that reasoning is from the language, not from a run.
- **The 503 is reproduced as a refused proxy `CONNECT`, not an HTTP response.**
  curl exits 56 rather than 22. Both leave stdout empty and both are what the
  code sees as "the download failed"; the exit-22 path is covered separately by
  the plain-HTTP origin used for the attempt counting.
- **The budget is gated with a 12-second stall.** A host that accepts a
  connection and then never answers still hangs the first attempt for as long as
  the OS allows — unchanged from the shipped behaviour, and not fixed here.
- **`tina4 update`'s own exit code is still 0** when the refresh fails. It now
  *says* the refresh failed, which is what the reporter's platform already did.
  Making update exit non-zero is a broader call than this defect.

## Still open, not fixed here

- `src/doctor.rs:10` advertises `https://tina4.com/install-skills.sh`, a
  different and much shorter script than the one `setup.rs` installs from. One
  of the two is stale. Nobody has been reported broken by it, and picking which
  is authoritative is a maintainer's call.
- A 200 response carrying something other than the installer would still be
  executed, on both platforms. That is the ordinary `curl | sh` bargain and it
  predates this change; the skill files the script then downloads *are*
  checksum-verified against `skills.sha256`.

## Files

| file | what |
|---|---|
| `prove.sh` | the whole reproduction and the fixed-build gates |
| `fake503.py` | local CONNECT proxy / origin that 503s chosen hosts, optionally after a stall |
| `bin/tina4-3.8.84` | the released binary the stock half runs |
| `evidence/cdn-probe.log` | the 20-probe availability measurement |
