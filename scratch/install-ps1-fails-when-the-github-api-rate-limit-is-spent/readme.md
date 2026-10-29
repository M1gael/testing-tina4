# install.ps1 fails when the GitHub API rate limit is spent

The Windows installer (`install.ps1`) is the same file in the CLI repo and at tina4.com. It reads
the latest release, and its asset URLs, from `api.github.com/repos/tina4stack/tina4/releases/latest`
(CLI `install.ps1:20`, tina4 `origin/main` 0b92b43). Unauthenticated, that API allows 60
requests an hour per IP. #115 and #118 moved `main.rs` and `install.sh` off it; `install.ps1`
was left on it. Ledger: `f-cli-60`.

## Run (2026-10-26, Windows 11 VM, Windows PowerShell 5.1.26100, API `remaining 0` on the shared IP)

`run-installer.ps1 <installer>` runs the script through `iex` (as `irm | iex` does), into a
throwaway LOCALAPPDATA, and restores the user PATH afterwards.

- `install-stock-0b92b43.ps1`: `threw: The remote server returned an error: (403) Forbidden.`,
  nothing installed.
- `install-fixed.ps1` (worktree `~/.cache/tina4-worktrees/installps1`, commit f948a94):
  `Version: v3.8.106`, checksum verified, Authenticode signature verified, `RESULT installed:
  tina4 3.8.106`.
- Instrumented copies of the fix, with the tag forced (deleted afterwards):
  - v9.9.8, which has no asset: "Could not download tina4-windows-amd64.exe from release v9.9.8",
    nothing installed.
  - v3.8.39, which has no SHA256SUMS: "SHA256SUMS is not available for v3.8.39 - refusing to
    install an unverified binary", nothing installed.

## Fix

Resolve the tag from the `releases/latest` redirect's og:url, the same lookup and regex as
`install.sh`, and download from `releases/download/<tag>/`. The edit **invalidates the
Authenticode signature**, so the maintainer must re-sign it (`scripts/sign-installers.ps1 -Files
install.ps1`); CI's "Verify canonical PowerShell installer signature" step stays red until then.
After signing, the signed file is copied to `tina4-documentation` `docs/public/install.ps1`.

## Not visited

- PowerShell 7 (not on the VM).
- A real 404 shows as "The connection was closed unexpectedly" on PS 5.1 rather than as a 404.
  The install still refuses.
- The harness's first version shared `$tmp` with the installer (iex runs in the same scope) and
  reported a good install as FAIL. Renamed to `$harnessDir`.
