# `tina4 update` cannot write to its own install directory

Ledger rows **f-cli-17** (the defect) and **f-cli-18** (our reporting gap).
Run `./prove.sh`. Exits 0 when everything is as recorded below. Needs network:
case B performs a real update.

**Versions.** Stock evidence is the released **3.8.85** `tina4-linux-amd64`
(`bin/tina4-3.8.85`), the version both reporters were on. Latest at the time of
writing is 3.8.86, so the download path runs rather than short-circuiting on
"already up to date". Source read at `origin/main` `9993bc0`.

## What was reported

Two machines, 2026-09-10, both on 3.8.85 upgrading to 3.8.86.

Linux (or WSL):

```
▶ Trying tina4-linux-amd64 ...
curl: (23) Failure writing output to destination
✗ Could not download tina4-linux-amd64 to /usr/local/bin/tina4.tmp (curl exited 23 -- it could not write the file).
```

macOS arm64:

```
▶ Trying tina4-darwin-arm64 ...
curl: (56) Failure writing output to destination, passed 1369 returned 4294967295
✗ Could not download tina4-darwin-arm64 to /usr/local/bin/tina4.tmp (curl exited 56).
```

The asset name is chosen at compile time from `cfg!(target_os = ...)`
(`src/main.rs:2002-2006`), so `tina4-linux-amd64` cannot come from a Windows
build. Both reports are Unix, both `/usr/local/bin`.

## Mechanism

`src/main.rs:1615`:

```rust
let tmp_path = current_exe.with_extension("tmp");
```

The update downloads to a temporary file **beside the running binary**, then
renames it over itself. Nothing in the path elevates, and nothing checks the
directory is writable before the download starts. The installer places the
binary in `/usr/local/bin`, which is `root`-owned `755` on stock Linux and on
Apple Silicon macOS, and installs there **under sudo**. So the install half and
the update half disagree about where the binary lives and who owns it, and only
the update half is wrong.

Introduced by `b742759` (2026-03-23), *"Implement self-update and v2 binary
cleanup in tina4 update"* — the only commit that has ever contained that line.
Not caused by any change of ours; `git log -S 'with_extension("tmp")'` returns
that commit alone.

Homebrew on Intel Macs used to `chown /usr/local` to the logged-in user, so on
those machines `tina4 update` works. Apple Silicon Homebrew moved to
`/opt/homebrew` and leaves `/usr/local` alone. That split is why this survived
six months.

## Proved

Single-factor, both directions. The only variable is the mode on the directory
holding the binary.

| | case A: dir `555` | case B: dir writable |
|---|---|---|
| curl | `(23) client returned ERROR on write of 1369 bytes` | — |
| exit code | 1 | 0 |
| result | `3.8.85`, unchanged | `3.8.85 → 3.8.86` |
| leftover `tina4.tmp` | none | none |
| message names the directory | yes | — |
| message suggests `sudo` | **no** | — |

**Confirmed against a genuinely `root:root` directory, not only a `chmod`
trick.** The table above uses mode `555` because `prove.sh` must run without
sudo. Repeated once by hand with the install directory and binary `chown`ed to
`root:root 755` — the exact shape of a real `/usr/local/bin`:

- plain `tina4 update` as a normal user: `curl: (23) client returned ERROR on
  write of 1369 bytes`, exit 1, still 3.8.85;
- `sudo tina4 update`, same directory, seconds later:
  `✓ Updated tina4 CLI 3.8.85 → 3.8.86`, binary left `root:root 755`.

So sudo is a working workaround, and privilege is the only thing that separates
the two runs.

**Same failure on both platforms, not two.** The Linux reproduction here fails
after **1369 bytes** — the identical count in the macOS report's
`passed 1369 returned 4294967295`. That is curl's first write of the body. The
two platforms differ only in which exit code curl picks for it.

## What is not fixed, and whose it is

**f-cli-17 — upstream's, unfixed.** Update has never been able to update a
root-owned install. Three plausible shapes, all a maintainer's call: elevate
(re-exec under `sudo` after asking); pre-flight the directory and say
`re-run with sudo` before downloading anything; or install to a user-owned
directory in the first place. Nothing is written here — this row is a
reproduction, not a fix.

**f-cli-18 — ours, a gap in [tina4#21](https://github.com/tina4stack/tina4/pull/21).**
`cause_for_curl_code` (`src/main.rs:2088`) classifies 23 as `Write` and gives
the "check free space and that you can write to …" line. **56 is deliberately
left `Unclassified`**, with a comment saying curl uses it for both a receive
error and a failed destination write, so a wrong verdict would be worse than
none. Field evidence now says otherwise: both the macOS report above and the
one that motivated #21 in the first place (see
`scratch/tina4-update-blames-the-platform-for-a-local-disk-failure`, which
records `curl: (56) Failure writing output to destination, passed 16375
returned 4294967295`) are 56 **and say in their own text that the write
failed**. The macOS user therefore got a bare `(curl exited 56)` and no
guidance at all, for the same cause the Linux user was told how to fix. Reading
curl's message rather than only its exit code separates the two without
guessing. Not attempted here.

Neither row proposes telling the user to run `sudo tina4 update` as the *fix* —
that is the workaround while the defect stands.

## Ruled out

- **Ours.** `with_extension("tmp")` predates every PR of ours by six months, and
  the same denial produced `Download failed (tried: …)` on `167b320c`, our own
  branch point. #21 changed the wording, not the behaviour.
- **Curl's stderr being newly exposed.** The pre-#21 code already ran
  `curl -fsSL` with inherited stderr; `-sS` shows errors. `curl: (23)` was on
  screen before us too.
- **Disk full.** Case B writes 9MB to the same filesystem seconds later.
- **The release asset.** Case B downloads and executes it.

---

# Investigation, 2026-09-10 — scope and the shape of a fix

Two questions, asked after the rows above were written. Changed nothing; the fork
was left on the branch it was found on and the probe directories were removed.

## Q1. Which curl codes does a failed write actually produce, and is a message-based rule sound?

**Answer: on this curl, every destination-write failure is exit 23, and the message
text differs between shapes.** 56 was never reproduced here.

**Run**, curl 8.15.0 (`x86_64-redhat-linux-gnu`), real GitHub asset URL:

| shape | exit | curl's message |
|---|---|---|
| directory not writable | 23 | `client returned ERROR on write of 840 bytes` |
| destination file mode 444 | 23 | `client returned ERROR on write of 839 bytes` |
| `/dev/full` | 23 | `Failure writing output to destination, passed 16375 returned 0` |
| `ulimit -f 64` | 153 (SIGXFSZ) | nothing printed at all |

Two consequences.

**The message is not a stable key.** `Failure writing output to destination` and
`client returned ERROR on write of N bytes` are both write failures on the same
curl. The Linux reporter's 3.8.85 output shows `curl: (23) Failure writing output
to destination` for a permission denial, where curl 8.15.0 here prints `client
returned ERROR on write of 1369 bytes` for the identical condition — so the text
for one condition also moves between curl versions.

**The `f-cli-18` rule survives anyway, narrowly.** It only ever fires on 56, and
both 56 sightings on record carry `Failure writing output to destination`
verbatim. It is a correct rule over the observed evidence. It is not a general
one, and it should not be described as reading "curl's message" — it is a rule
about one string on one exit code.

**Bounds.** 56 was not reproducible here at all, so the rule rests entirely on two
macOS field reports (**inferred**, not run). Whether macOS curl returns 56 for the
permission case specifically, or only for a mid-stream write failure, is unknown
and would need a Mac. `ulimit -f` prints nothing and dies on a signal — already
handled, since the classifier takes the whole `ExitStatus`.

## Q2. Is Windows affected?

**Answer: no, as installed.** **Read**, `origin/main` `9993bc0`:

- `install.ps1:7` — `$installDir = "$env:LOCALAPPDATA\tina4"`. Per-user, always
  writable by the user who installed it.
- `install.sh:8` — `INSTALL_DIR="${TINA4_INSTALL_DIR:-/usr/local/bin}"`.

`src/main.rs:1615` is not platform-gated — no `cfg!(target_os` appears above it in
the function — so Windows writes its temporary file beside the binary too. It
succeeds because the directory is the user's own. Not run: no Windows here.

## The finding that matters most

**The installer already performs the exact check the updater is missing**, twelve
lines of the same repo. `install.sh:140-145`:

```sh
# Install — try without sudo first
if [ -w "$INSTALL_DIR" ]; then
  mv "$TMP" "${INSTALL_DIR}/tina4"
else
  echo "Need sudo to install to ${INSTALL_DIR}"
  sudo mv "$TMP" "${INSTALL_DIR}/tina4"
fi
```

So this is not an open design question about install contracts, as the first
version of `f-cli-17` framed it. The project has already decided how it handles a
root-owned install directory — test `-w`, say so, elevate — and `tina4 update`
simply never got that treatment.

**Negative, scope stated:** no writability test, `geteuid`, or elevation exists
anywhere in the update path. Searched all 17 files of `src/*.rs` for
`is_writable`, `.metadata()`, `readonly()`, `permissions()`, `sudo`, `geteuid`,
`Elevat`; every `sudo` hit is in `deploy.rs` (printing instructions) or
`install.rs` (installing language runtimes).

**A documented escape already exists.** `README.md:29` shows
`TINA4_INSTALL_DIR=~/.local/bin`. An install there is user-owned, so update works
— that is case B above, **run**.

## What this does to the two rows

- `f-cli-17` — the fix is smaller and less contentious than first written. Port
  `install.sh`'s existing `-w` test into the update path before the download
  starts. Not a new policy; the policy exists.
- `f-cli-18` — still real, still ours, but second in priority. A pre-flight check
  makes curl's exit code irrelevant for the common cause, and classification only
  matters for the cases pre-flight cannot see.

**Bound on the proposed pre-flight:** `-w` on the directory would not catch a
destination *file* that exists mode 444 in a writable directory — shape 2 above,
exit 23. Rare (the binary is 755), and it degrades to today's behaviour rather
than regressing, but the check is not a complete cover and should not be claimed
as one.
