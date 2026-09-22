#!/usr/bin/env bash
# Does `tina4 env --sync` write the truncation back into .env, and does it compound?
# Runs in a throwaway copy — the project's own .env is never touched.
set -u
BIN="${BIN:-/var/home/work/.cache/tina4-update-probe/a/bin/tina4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cp "$HERE/.env" "$HERE/app.py" "$HERE/requirements.txt" "$WORK/"
cd "$WORK"
echo "# version: $("$BIN" --version 2>&1 | head -1)"
show() { echo "## $1"; grep -E 'ENDS_DQ|QUOTED_EMPTY|TINA4_CSP|TRIPLE_SQ' .env | sed 's/^/    /'; echo; }
show "before"
"$BIN" env --sync >/dev/null 2>&1; show "after 1st --sync"
"$BIN" env --sync >/dev/null 2>&1; show "after 2nd --sync"
ls .env.bak >/dev/null 2>&1 && echo "    (a .env.bak was written)" || echo "## no .env.bak — the original is gone"
