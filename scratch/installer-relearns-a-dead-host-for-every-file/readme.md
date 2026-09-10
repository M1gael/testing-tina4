# The skills installer re-learns a dead host once per file

A `tina4 update` that recovers from a CDN outage takes **minutes** to do it, and spends
almost all of that time asleep, re-proving something the first file already established.

Reported from Windows PowerShell on **tina4 CLI 3.8.85**: the install completed and every
file landed, but the run "took very long". It did — and the reason is not the outage.

**Pinned to:**

| | |
|---|---|
| CLI as reported | `3.8.85` (released) |
| Installer as reported | `install-skills.ps1` / `.sh` at `v3.8.85` — **two** tiers, raw then jsDelivr |
| Installer as it now stands | `origin/main` `5825222` — **three** tiers, tina4.com then jsDelivr then raw (`3ca8c23`) |
| Skills ref | `3.13.135` |
| curl | 8.15.0 |
| Measured | 2026-09-09 |

Both matter. The two-tier version is what the reporter ran; the three-tier version is what a
fix has to land on, and it carries the same defect in the same function, unchanged.

## What is actually wrong

Two things, and the second one is why nobody caught the first.

### 1. Nothing remembers that a host is down

`install-skills.sh:49-58` (and `install-skills.ps1:54-76`) walk their source list per file,
with no state between calls:

```sh
download_file() {
  destination="$1"; shift
  for url in "$@"; do
    if curl -fsSL --retry "$retry_count" --retry-delay "$retry_delay" "$url" -o "$destination"; then
      return 0
    fi
    rm -f "$destination"
    echo "  ! download failed, trying next source: $url" >&2
  done
```

`--retry 3` is **four** attempts, `--retry-delay 2` sleeps 2s between them. So one file
against one dead host costs 4 doomed requests and 6 seconds. There are **48** files. The
function is called 48 times and starts from zero every time.

> **The theory, falsifiably:** the cost of an outage is
> `files x (retry_count + 1)` doomed requests and `files x retry_count x retry_delay`
> seconds, because nothing distinguishes a host that is down — a fact that stays true for
> every later file — from a file that is absent, and nothing carries either fact forward.

### 2. The installer's only automated test stopped testing the installer

`tests/skills_installer_http.py` stands up a local server that injects 503s, and CI runs it
on ubuntu **and** windows. It sets `TINA4_SKILLS_PRIMARY_ROOT` and
`TINA4_SKILLS_MIRROR_ROOT`.

Commit `3ca8c23` made the installer three-tier and renamed those variables to
`TINA4_SKILLS_TINA4_ROOT` / `JSDELIVR_ROOT` / `RAW_ROOT`. It did not touch the test.

The installer now reads **neither** of the variables the test sets. Since that commit the
test has been running the installer against the **real internet**, passing for the wrong
reason, asserting nothing about retries or fallback. Proven directly:

```
$ TINA4_SKILLS_PRIMARY_ROOT=http://127.0.0.1:9 \
  TINA4_SKILLS_MIRROR_ROOT=http://127.0.0.1:9 sh install-skills.sh
exit=0 elapsed=5.0s files=48
```

Both roots point at a closed port. It installed 48 files anyway. The local server in the
test never receives a request, so its 503 injection reaches nothing.

This had to be repaired before defect 1 could be gated at all.

## Reproduction

`./prove.sh` — no network needed. `hosts.py` stands in for the real hosts on loopback, and
`mirror/` holds the genuine bytes for ref 3.13.135, so the installer's own sha256
verification runs for real rather than being stubbed out.

### Measured — the installer as reported (two tiers, primary 503s for everything)

| | stock `v3.8.85` | with the fix |
|---|---|---|
| doomed requests to the dead host | **192** | **4** |
| requests at `retry_count=0` | 48 | 1 |
| files installed | 48 | 48 |
| exit code | 0 | 0 |
| warnings printed | 48 | 1 |
| wall clock (`retry_delay=0`) | **338.1 s** | **8.1 s** |

192 is exactly `48 files x 4 attempts`. At `retry_count=0` it is exactly `48 x 1`. The cost
is a function of the retry walk and the file count, and of nothing else — which is the
theory, stated as an equation and then measured at two points on it.

The same run against a **closed port** rather than a 503 (curl reports `000`, not an HTTP
status) gives 48 warnings stock and 1 with the fix, so the classification covers a host that
is unreachable as well as one that is answering badly.

### Measured — the installer as it now stands (three tiers, shipped defaults)

`retry_count=3`, `retry_delay=2`, first tier 503s for everything, via the repo's own
harness on `origin/main` `5825222`:

| | stock `origin/main` | with the fix |
|---|---|---|
| wall clock | **291.0 s** | **8.2 s** |
| doomed requests to the dead tier | **192** | within a 4-request budget |

Four minutes fifty-one, of which roughly 264 s is `Start-Sleep`/`--retry-delay` doing
nothing. Note what the three-tier change did and did not do: putting tina4.com first means a
raw.githubusercontent.com outage no longer costs anything, which is why the reporter's own
symptom is already softened on `main`. But it also means an outage on **tina4.com** — Tina4's
own single origin, now tier one — costs the full 291 s. The defect did not move; the tier
that triggers it did.

### Measured — against the real hosts

One run of the candidate against the genuine tina4.com / jsDelivr / raw, on 2026-09-09 while
raw.githubusercontent.com was flapping: **48 files, exit 0, 39.3 s, one warning**. The
warning is the fix writing raw off after a single walk. Stock would have paid that walk once
per file.

## The fix

`install-skills.sh` and `install-skills.ps1`, same shape in both:

- **Remember a host that is not answering**, for the run only, keyed on `scheme://host`.
  A skipped source is not dropped — it goes on a list.
- **Classify the failure.** `curl -f` collapses every HTTP error into exit 22, so the status
  comes from `--write-out '%{http_code}'`, which is printed on failure too and — verified —
  is printed exactly once no matter how many times `--retry` retried. `000` or `5xx` is a
  fact about the host; `4xx` is a fact about one path and must never cost the host.
- **Two passes.** The first skips known-dead hosts. The second tries exactly those, so a
  skip can never lose a source: if every remaining source fails, the run still asks the
  dead one before giving up.

**Deliberately not changed:** the number of retries or the delay (the walk itself is fine —
it is the repetition that is not); the tier order; the checksum step; and the timeout
situation — neither `curl` nor `Invoke-WebRequest` has one here, so a host that accepts a
connection and then never answers still hangs, exactly as it does today. That is a separate
defect and is not in this evidence.

## What gates what

Each piece reverted on its own, against the repo's own harness, and each turns it red alone:

| reverted | result |
|---|---|
| the dead-host memory | RED — `outage`: the down tier asked 96 times, budget 4 |
| the skip itself | RED — `outage`: same 96 |
| the failure classification | RED — `gap`: one missing file sent 33 requests to the fallback |
| the second pass | RED — `revival`: the written-off tier was never asked again |

And the whole installer reverted to `origin/main` turns `outage` red, which is what makes the
new test a regression test rather than a description.

## Residual gaps — stated, not implied

- **The PowerShell half WAS executed** — PowerShell 7.4.6, unpacked from the upstream
  standalone tarball into `/tmp` (it needs no root, which is why the earlier "no pwsh here"
  was wrong). Against the real `install-skills.ps1`: all five harness contracts pass, and each
  of the four components turns the suite red on its own, exactly as on the shell side.
  Reverting the whole `.ps1` to `origin/main` turns `outage` red. The classifier was also
  probed directly — 503 to 2, 404 to 1, 200 to 0, refused connection to 2 — with the functions
  lifted verbatim out of the shipped file and run under `Set-StrictMode -Version Latest`, since
  a caller can have strict mode set and the CLI bootstrap runs this script through `iex` in the
  caller's scope.
- **What is still not covered is Windows PowerShell 5.1 specifically.** The run above is
  PowerShell 7 on Linux. The exception type differs there — 5.1 throws `System.Net.WebException`
  wrapping an `HttpWebResponse`, 7 throws `HttpResponseException` wrapping an
  `HttpResponseMessage` — but both expose `.StatusCode` as the same `System.Net.HttpStatusCode`
  enum, which is the only member touched, and for a refused connection 5.1 leaves `.Response`
  null, which is the branch that returns "host is down". PSScriptAnalyzer's `PSUseCompatibleSyntax`
  and `PSUseCompatibleCommands` rules against a 5.1 profile report **zero** findings on the
  patched file, and the full default ruleset shows my change adds **no** new finding of any kind
  versus upstream. CI's `skills-installer (windows-latest)` invokes `powershell.exe`, which *is*
  5.1, so that job covers precisely this remaining gap. Windows filesystem semantics are likewise
  untested here.
- **The `.ps1` Authenticode signature is now invalid.** `ci.yml:32-46` requires
  `Get-AuthenticodeSignature` to report `Valid` for both the checked-out file and a copy
  fetched from raw at the merge SHA. Any edit to the body breaks both, and re-signing needs
  the code-signing key. That step will be red until the maintainer re-signs — this is not a
  fixable-by-me condition and must not be presented as a surprise.
- **The harness fixture lists 43 files; the installer fetches 47.** `web-push.md` is in
  `install-skills.sh`'s `DEV_REFS` and in the published `skills.sha256` (47 lines), but not
  in the test's `DEV_REFS`. Those four files are downloaded and never asserted. Pre-existing,
  untouched here, worth its own row.
- **CI verifies the signature by downloading from raw.githubusercontent.com with no retry**
  (`ci.yml:42`) — the very host this work is about. During an outage that step fails for
  reasons that have nothing to do with the change under test.
- **No timeout anywhere.** A host that accepts a connection and never answers still hangs the
  first walk. Unchanged, out of evidence, separate defect.
- **Two tiers on one host share its fate.** The memory is keyed on `scheme://host`, which is
  the thing that actually goes down. A self-hosted setup pointing several tiers at one
  machine gets no benefit from the write-off rather than a wrong answer.

## Files

| | |
|---|---|
| `prove.sh` | the whole reproduction and the gates; no network |
| `hosts.py` | loopback stand-ins for the real hosts: 503, 404-gap, recovery, closed port |
| `fetch-mirror.sh` | populates `mirror/` with the genuine bytes for a ref (needs network, once) |
| `mirror/` | real skill files at 3.13.135, so the installer's sha256 step runs for real |
| `stock-install-skills.{sh,ps1}` | the installers as shipped in `v3.8.85`, two tiers |
| `fixed-install-skills.{sh,ps1}` | the candidate against that version |
| `evidence/` | raw run logs and per-run request counts |
