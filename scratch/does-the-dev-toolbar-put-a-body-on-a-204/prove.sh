#!/usr/bin/env bash
# Reproduce: the dev toolbar puts a body on a 204 No Content response.
#
#   ./prove.sh                 # run both trees and print the table
#
# Trees (detached worktrees of tina4stack/tina4-python, cut from origin/v3):
#   ~/.cache/tina4-worktrees/pr132-stock   198e09b, untouched
#   ~/.cache/tina4-worktrees/pr132-fixed   198e09b + PR #132 (pr132.patch)
set -u
PY=/var/home/work/gitdir/tinaforks/tina4-python/.venv/bin/python
D="$(cd "$(dirname "$0")" && pwd)"

for t in stock fixed; do
  W=/var/home/work/.cache/tina4-worktrees/pr132-$t
  [ -d "$W" ] || { echo "missing worktree $W — see readme.md"; exit 2; }
  echo "=== $t ($(git -C "$W" rev-parse --short HEAD))"
  PYTHONPATH=$W TINA4_DEBUG=true "$PY" "$D/drive.py" 2>/dev/null | sed -n '/^\[/,$p' | python3 -c "
import json,sys
for r in json.load(sys.stdin):
    print(f\"  {r['case']:18} status={r['status']:3} body={r['body_bytes']:5} CL={str(r['content_length']):5} toolbar={r['toolbar_present']}\")"
done

echo
echo "=== on a real socket, through uvicorn (keep-alive: DELETE then GET)"
for t in stock fixed; do
  W=/var/home/work/.cache/tina4-worktrees/pr132-$t
  echo "--- $t"
  PYTHONPATH=$W "$PY" "$D/wire.py" $((18900 + RANDOM % 90)) 2>&1 \
    | grep -E "LocalProtocolError|responses seen|total bytes"
done

echo
echo "=== on a real socket, through tina4's OWN dev bridge (tina4 serve)"
for t in stock fixed; do
  W=/var/home/work/.cache/tina4-worktrees/pr132-$t
  echo "--- $t"
  PYTHONPATH=$W "$PY" "$D/wire_builtin.py" $((19000 + RANDOM % 90)) 2>&1 \
    | grep -E "raw bytes|http.client"
done
