#!/usr/bin/env bash
# Does `tina4 init <lang> <path>` stop when <path> already holds a different
# Tina4 project?  Exit 1 = reproduced (it does not stop).  Exit 0 = fixed.
#
# Pinned: tina4 CLI 3.8.87 (released tina4-linux-amd64, sha256 verified against
# the release SHA256SUMS).  Needs node/npm and uv on PATH.
set -u
TINA4="${TINA4:-$(dirname "$0")/bin/tina4-linux-amd64}"
[ -x "$TINA4" ] || { echo "no CLI at $TINA4 — set TINA4=/path/to/tina4"; exit 2; }

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT; cd "$W"

printf 'n\n' | "$TINA4" init js  mixing-test >/dev/null 2>&1 || { echo "step 1 failed"; exit 2; }
printf 'n\n' | "$TINA4" init python mixing-test > step2.log 2>&1
SECOND_EXIT=$?

echo "second init exit: $SECOND_EXIT"
grep -E 'Directory already exists|gitignore already exists' step2.log | sed 's/^/  /'

fail=0
for f in app.py pyproject.toml uv.lock package.json package-lock.json vite.config.ts src/main.ts; do
    [ -e "mixing-test/$f" ] || { echo "MISSING $f — layout changed, this proof is stale"; exit 2; }
done
echo "  both stacks present: app.py + pyproject.toml + uv.lock AND package.json + vite.config.ts + src/main.ts"

# The .gitignore skip is the sharp end: python's ignores never land.
for rule in '.venv/' '.env' 'secrets/' '__pycache__/'; do
    grep -qxF "$rule" mixing-test/.gitignore || { echo "  .gitignore is missing python rule: $rule"; fail=1; }
done

[ "$SECOND_EXIT" -eq 0 ] && { echo "  and it exited 0"; fail=1; }
[ "$fail" -eq 1 ] && { echo "REPRODUCED"; exit 1; }
echo "not reproduced"; exit 0
