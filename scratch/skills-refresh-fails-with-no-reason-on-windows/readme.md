# `tina4 update` reports a skills-refresh failure with no reason, on Windows

**Pinned:** tina4 CLI **3.8.87** (released `tina4-linux-amd64`, sha256 verified), CLI source
`origin/main` **`6a9b68e`**, `tina4-documentation` `origin/main` **`a5fc43f`**. Probed
2026-09-16 from Linux. Reported by @jeann on Windows, screenshot only, no timestamp.

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

## No ordering gap this time

The bootstrap moved to ref `3.13.137` in `ea0a9e4`, 2026-09-14 11:46 SAST = **09:46 UTC**. The
tag `3.13.137` was created in `tina4stack/tina4` at **09:45:31 UTC** — one minute earlier. Tag
first, then the pin. [[skills-ref-tagged-after-the-release]] did not recur.

## Not established

- **When @jeann ran it.** No timestamp on the screenshot. If before 2026-09-14 09:31 UTC it is
  `48716f3` and is fixed; after, it is something else and the silence above is why we cannot
  tell from the image.
- **Windows was not run here.** No Windows host, and no `pwsh` on this machine. Every Windows
  claim is read from the source or taken from `48716f3`'s own verification note.
- `exit 0` from `tina4 update` after a failed refresh is deliberate — the message says the
  client update is still complete.
