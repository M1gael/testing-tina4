# `tina4 update` blames the platform for a local disk failure

Ledger row **f-cli-05**. Run `./prove.sh` for the stock half; pass a fixed build
as `$1` for the other half. Exits 0 when everything is as recorded below.

**Versions.** Stock evidence is the released **3.8.69** `tina4-linux-amd64`
(`bin/tina4-3.8.69`), which is the version the reporter was on. Source read at
upstream **3.8.78** (`c02cb48`). The fixed binary is
`fix/update-reports-the-real-download-failure` built with the crate version
lowered to 3.8.60, because at 3.8.78 `update` short-circuits on "already up to
date" and the download path never runs — `prove.sh` refuses to continue if it
is handed a 3.8.78 build, since that would measure nothing.

## What happens

Reported on macOS arm64. The first line was real, the next three were not:

```
▶ Trying tina4-darwin-arm64 ...
curl: (56) Failure writing output to destination, passed 16375 returned 4294967295
▶ Trying tina4-darwin-aarch64 ...
curl: (56) The requested URL returned error: 404
...
✗ Download failed (tried: tina4-darwin-arm64, tina4-darwin-aarch64, tina4-macos-arm64, tina4-macos-aarch64).
```

Two people read that as "there is no macOS build". There is:
`tina4-darwin-arm64` on v3.8.78 is 10361248 bytes, a valid Mach-O arm64
executable, and its sha256 matches the release's own `SHA256SUMS` line. The
message is curl failing to **write**, not to fetch.

## Mechanism

`download_file` (`src/main.rs:2071`) returned a `bool`, so `handle_update`
(`src/main.rs:1666`) could not tell an HTTP refusal from a local failure and
tried the next candidate either way. Every remaining candidate 404s, and the
summary names them all.

Three further consequences, all reproduced:

- **The real error can be invisible.** When the write fails partway, curl dies
  on SIGXFSZ and prints nothing at all, so the *only* visible error is a 404
  for a name the user was never going to get.
- **A truncated `tina4.tmp` is left behind** — 65536 bytes in case 2. The
  `if !downloaded` branch returns without removing it.
- **The process exits 0.** Nothing scripted can detect a failed update.

## The fallback names are not fictional

An earlier reading of this called them invented. Wrong: `tina4-macos-arm64`,
`tina4-macos-x86_64`, `tina4-linux-x86_64` and `tina4-windows-x86_64.exe` were
the **real** asset names in v3.1.4 and v3.1.9. `1333e05` (2026-03-24) added the
fallback loop for exactly that. Only the `aarch64` spellings have never
existed. The defect is not that the names are made up — it is that their
benefit has been zero since v3.2.0 while their cost is paid on every local
failure.

## Before and after

| | stock 3.8.69 | fixed |
|---|---|---|
| unwritable destination | 404 for a phantom name, "Download failed (tried: …)" | names the file, the reason, and the directory |
| write fails partway | no error printed at all | "curl was killed by a signal" |
| leftover | `tina4.tmp`, 65536 bytes | none |
| exit code | 0 | 1 |
| successful update | works | works, still exits 0 |

## Ruled out along the way

- **A glibc floor regression.** The linux-amd64 builds require GLIBC_2.39, but
  so does every release measured back to 3.8.65 — update does not introduce it,
  and anyone below 2.39 could never have run these builds at all.
- **The macOS asset being missing.** Downloaded and checksum-verified against
  the release's own `SHA256SUMS`.
- **Anything of ours causing it.** No PR of ours has ever touched this repo.

## Still open, not fixed here

A **musl** build updates itself into the **glibc** build: the candidate list has
no musl name, so `tina4-linux-musl-amd64` fetches `tina4-linux-amd64`.
Reproduced — a `static-pie linked` binary became `dynamically linked` after one
`tina4 update`. On Alpine the replacement cannot exec at all: it asks for
`/lib64/ld-linux-x86-64.so.2` and `libc.so.6`, neither of which musl provides.
Its own row, deliberately not folded into this fix.
