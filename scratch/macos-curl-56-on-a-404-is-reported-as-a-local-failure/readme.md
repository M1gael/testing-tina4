# macOS curl's exit 56 on a 404 is reported as a local failure

`tina4 update` decides whether a failed download was the server refusing it (try the next asset
name, then say the release has no asset) or a fault on this machine, from curl's exit code alone.
Only 22 counts as a server refusal (`classify_curl_status`, `src/main.rs`). The curl macOS ships
has been seen exiting **56** for a `--fail` 404 (team report 2026-10-26, `curl: (56) The requested
URL returned error: 404`) and 56 for a failed write (`Failure writing output to destination`,
the `f-cli-17` and `f-cli-18` reports). So a missing asset printed "The release asset is fine",
and a write failure got no cause. Ledger: `f-cli-57`, `f-cli-18`.

Tree: tina4 `origin/main` 0b92b43 (3.8.106).

## Reproduce

`./prove.sh <tina4 binary>`. It runs `tina4 update` from a throwaway install dir, with
`bin/curl`, a stand-in (`fake-curl-8.7.1`) that runs the real curl and rewrites exit 22 and 23
to the macOS 56 with the field text. `FAKE_LATEST` points `releases/latest` at a tag;
`FAKE_SERVE_FROM` serves real assets for it; `tina4.tmp` symlinked to /dev/full makes the write
fail.

- Stock 0b92b43: `FAIL 404-under-56`, `FAIL write-under-56`, `PASS 404-under-22`. The 404 case
  prints the field output exactly: "Could not download ... (curl exited 56). The release asset is
  fine".
- Fixed: all three PASS. The 404 walks every name and ends "Release v9.9.8 publishes no asset";
  the write case says "curl exited 56 -- it could not write the file ... check free space".

## Fix (worktree `~/.cache/tina4-worktrees/fcli57`, branch `fix/update-reads-http-status-not-only-curl-exit`, commits dc15928 and 65a0249 on 0b92b43, not pushed; patches in `fcli57.patches/`)

- New `download_with_curl` captures curl's stderr, re-prints it, and passes it to
  `classify_curl_status`, the same shape as the existing wget path. Used for Unix curl and
  Windows curl.exe. PowerShell is unchanged.
- `classify_curl_status(status, stderr)`: any exit code with "The requested URL returned
  error" is an HTTP refusal; 56 with "Failure writing output to destination" is a write failure.
  All other cases are unchanged.

Gates, one piece reverted at a time: the HTTP arm turns the unit test and the 404 proof red; the
write arm turns the unit test and the write proof red; the Unix call site and the stderr
hand-off turn both proofs red, and the hand-off also turns `the_curl_download_reads_curls_own_line`
red. Suite 390 pass, 0 fail. clippy is clean on Linux and on `x86_64-pc-windows-gnu`.

## Not visited

- Real macOS curl 8.7.1. The stand-in reproduces the reported output, not curl's internals.
  Building 8.7.1 here was blocked by the permission classifier.
- Windows curl.exe at run time (type-checked only).

## Second instance: `tina4 doctor` (65a0249, `f-cli-59`)

`latest_from_curl` (`src/doctor.rs`) read only exit 22 as an HTTP error. Run with the stand-in and
`FAKE_404_URL=install-skills.sh`: stock prints "could not check latest (offline)", fixed prints
"skills version check returned an HTTP error - the endpoint may have moved". The new unit test
turns red when the stderr arm is reverted.

## The whole incident, end to end

- The 404 itself was the 3.8.104 atom-feed resolver offering a tagged, unpublished release. It is
  fixed upstream in 3.8.106 (#118). Run today: the **released** 3.8.104 linux-amd64 binary updates
  to 3.8.106 cleanly, with the checksum verified.
- Our fix, built as version 3.8.104 (a throwaway instrument worktree, since removed), updates to
  the real 3.8.106 with the checksum verified using real curl, the 56 stand-in, and wget only
  (no curl on PATH).
- What is left: any machine still on 3.8.104 reads the atom feed, so it will 404 again during
  the next tag-to-publish window (CI build plus local EV signing). It clears once that machine
  updates once. Removing the window itself would mean the release workflow not pushing the tag
  until publish. That workflow ties provenance attestations to the tag, so it is the
  maintainer's design and not changed here.
