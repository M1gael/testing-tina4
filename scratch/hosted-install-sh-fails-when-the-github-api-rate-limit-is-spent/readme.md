# The hosted install.sh fails when the GitHub API rate limit is spent

`curl -fsSL https://tina4.com/install.sh | sh`, the documented install, serves
`tina4-documentation` `docs/public/install.sh`. As of docs `origin/main` 85c2442, that file is a
byte-identical copy of the CLI repo's install.sh at ca00db4 (2026-10-17). Line 79 reads the
latest release from `api.github.com/repos/tina4stack/tina4/releases/latest`. Unauthenticated,
that API allows 60 requests an hour per IP. With `set -e`, a 403 ends the install at exit 22,
and the only output is curl's own line. The CLI repo fixed its copy in #115 and then #118
(0b92b43, which resolves the `releases/latest` redirect and probes asset URLs); the hosted copy
was never re-synced.

## Run (2026-10-26, this machine's IP with the API quota spent: `remaining 0`)

- `hosted-install-85c2442.sh`: rc 22, nothing installed. Log: `curl: (22) The requested URL
  returned error: 403`.
- `cli-install-0b92b43.sh`: rc 0, tina4 3.8.106 installed, checksum verified.
- Fixed hosted copy (docs worktree `~/.cache/tina4-worktrees/hosted-install-docs`, commit 21c6169
  on `origin/main` 85c2442): rc 0 with curl, and rc 0 with wget only (no curl on PATH).

## Fix

Re-sync `docs/public/install.sh` to tina4 0b92b43's install.sh, byte for byte, the way earlier
syncs did (85c2442, 615779f). It is committed locally on `fix/sync-hosted-install-sh-to-cli-0b92b43`
and not pushed; patch in `hosted-install-docs.patches/`. The page `docs/install-security.md`
("Reads the latest GitHub release") stays accurate.

## Not visited / not fixed

- macOS (BSD grep and sed) and Termux/iSH runs of the new copy. The grep -oE and sed used are
  POSIX-compatible (read).
- `install.ps1`, both the hosted and the CLI copies, still uses `api.github.com` (line 20 of the
  CLI copy), so Windows installs hit the same 60/hour limit. The hosted copy is Authenticode-signed,
  so it cannot be edited without re-signing. Not fixed.
- Nothing keeps the hosted copy in step with the CLI's; it drifts after every installer change.
