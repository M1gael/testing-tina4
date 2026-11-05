#!/usr/bin/env bash
# Revert each fixed page on its own (one hunk each) and confirm prove.sh goes red; restore after.
set -u
W=${W:-$HOME/.cache/tina4-worktrees}; red=0; green=0
for spec in "DOCS dorm04-tina4-documentation" "BOOK dorm04-tina4-book"; do set -- $spec
  t=$W/$2; for f in $(git -C "$t" diff --name-only); do
    cp "$t/$f" "$t/$f.gatebak"; git -C "$t" show "HEAD:$f" > "$t/$f"
    env $1="$t" "$(dirname "$0")/prove.sh" >/dev/null 2>&1; rc=$?
    mv "$t/$f.gatebak" "$t/$f"
    if [ $rc = 1 ]; then red=$((red+1)); echo "red   $2/$f"; else green=$((green+1)); echo "GREEN $2/$f rc=$rc"; fi
  done; done
echo "red=$red green=$green"; [ $green = 0 ]
