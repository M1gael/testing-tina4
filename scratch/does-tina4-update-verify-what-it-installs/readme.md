# Does `tina4 update` verify what it installs?

**No — nothing checks the bytes between the download and the rename, although every release
publishes `SHA256SUMS` and the project's own `install.sh` verifies against it.** Ledger row
`f-cli-06`.

Investigated 2026-09-22. Released `v3.8.85` → `v3.8.88` `tina4-linux-amd64`; source read at
`origin/main` `3a4377d`. Linux, glibc.

## Mechanism

`handle_update()` (`src/main.rs:1620`):

1. `download_first_candidate(...)` → `download_file_classified(url, tmp)` (`src/main.rs:2359`),
   which on non-Windows runs `Command::new("curl").args(["-fsSL","-o",dest,url])` — **the bare
   name `curl`, resolved through `PATH`**;
2. `classify_curl_status` (`src/main.rs:2164`) maps **exit 0 to `DownloadOutcome::Ok`** and
   reads nothing else — not the size, not the type, not a checksum;
3. `chmod 0755` on the temp file, rename the running binary to `.old`, rename the temp file
   into its place, then **delete the `.old` backup**;
4. print `✓ Updated tina4 CLI <old> → <new>`.

`SHA256SUMS` appears nowhere in `src/` — `git grep -in sha256 origin/main -- src/` returns only
unrelated hits in `metrics.rs`/`rag.rs`/`setup.rs`.

**The falsifiable sentence:** the exit status of the downloader is the whole acceptance test,
so whatever is at the temp path when it exits 0 becomes the CLI.

## The contrast that settles it

`install.sh` at the same commit **does** verify — lines 107-132: it fetches `SHA256SUMS` from
the same release tag, errors if the asset is not listed, errors if no sha256 tool is present,
and *refuses to install* on mismatch: `Error: checksum mismatch for ${BINARY} - refusing to
install`. Its own comment: *"Releases from 3.8.53 publish SHA256SUMS; when it is present we
verify strictly."*

So the policy exists and is already implemented for the first install. The self-update path,
which does the same job, skips it.

## What was run

`./prove.sh`. A stand-in `curl` sits first on PATH; the version check (no `-o`) is passed
through to the real curl, so only the asset download is under our control.

| | Result |
|---|---|
| **B1** real curl (control) | installs, and the installed sha256 equals the published `SHA256SUMS` line — the harness can see a correct install |
| **B2** downloader exits 0 having written `TOTALLY-NOT-A-TINA4-BINARY` | **27 bytes of ASCII installed as the CLI**, `✓ Updated tina4 CLI 3.8.85 → 3.8.88`, **exit 0**, and the `.old` backup deleted — the working CLI is gone, not merely un-upgraded |
| **B3** downloader exits 0 having written nothing | `✗ Cannot replace binary — restoring backup` on stderr, old binary restored, **exit 0** |

`SHA256SUMS` confirmed published on v3.8.70, v3.8.85, v3.8.86, v3.8.87, v3.8.88 (GitHub API).

## Bounds

- **Run** — B1/B2/B3 on Linux against the released binaries.
- **Read** — the absence of any check, at `3a4377d`, scope `src/**`, patterns
  `sha256|checksum|signature|gpg`, case-insensitive.
- **Not visited:** Windows (the `curl.exe` / PowerShell branch of the same function), macOS,
  and the `.deb` install path.
- **B2 substitutes bytes at the downloader, not on the wire.** It proves the *absence of a
  check*; it is not a claim about how bytes would be substituted in practice. A corrupted
  proxy, a cache, a partial write, or anything that can write that temp path lands the same way.
- **What would change the answer:** a checksum step in `handle_update`, or any acceptance test
  beyond the exit status.

## Found on the way

B3: a download that produces no file leaves `handle_update` printing `Cannot replace binary`
and **exiting 0**. That is `f-cli-23`'s shape reached on Linux, through a different branch than
the Wine/PowerShell one that row describes.

---

## The fix

Branch `fix/update-verifies-the-binary-it-installs`, cut from `origin/main` `3a4377d`,
uncommitted, worktree `~/.cache/tina4-worktrees/fcli06`. Diff saved as `fix.patch`
(Cargo.toml, Cargo.lock, src/main.rs, tests/update_verifies_download.rs, +508/-8).

`handle_update` now fetches `SHA256SUMS` from the same release tag, looks up the asset name
that actually downloaded, hashes the temp file, and **refuses on a mismatch or an unlisted
asset**: the temp file is deleted, the running CLI is not touched, and it exits 1. A verified
install prints `Checksum verified (sha256)`.

When the release publishes no `SHA256SUMS` — nothing before 3.8.53 does — it installs and says
`installing without verifying`. That is `install.sh`'s own rule, mirrored rather than
tightened, and it is the one residual: an attacker who can block that one URL turns
verification off silently. Saying so out loud is the whole of the mitigation here.

**Cost:** one direct dependency, `sha2 = "0.10"`, pure Rust, nothing to cross-compile. Seven
crates in the lockfile: `sha2`, `digest`, `block-buffer`, `crypto-common`, `generic-array`,
`typenum`, `cpufeatures`.

### How it was verified

`cargo test` green (227 unit, including 6 new; 4 new entry-point tests),
`cargo clippy -- -D warnings` clean.

The entry-point tests are hermetic — PATH holds one directory with a stand-in `curl` that
answers the release API with a forced version, then serves whatever the test wants the download
to be. No network, and the binary under test is a copy.

| | |
|---|---|
| substituted bytes | refused, exit non-zero, binary byte-identical to before |
| matching bytes | installed, `Checksum verified` |
| no SHA256SUMS published | installed, `without verifying` said out loud |
| asset not listed in the sums | refused, binary unchanged |

Four mutations, each reverted after:

| Mutation | Result |
|---|---|
| lift the verification out of `handle_update` | unit tests **stay green**, entry-point tests red — which is why they exist |
| match the asset name by prefix | red — `verify_negative_edge_a_prefix_name_does_not_match` |
| accept an unlisted asset | red — two unit tests |
| warn on mismatch instead of refusing | red — two entry-point tests |

`sha256_file` is checked against the published digest of the empty input, not against itself.
