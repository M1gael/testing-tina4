#!/usr/bin/env bash
# Revert each hunk of each held patch alone from the fixed tree; prove.sh must go red.
set -u
here=$(cd "$(dirname "$0")" && pwd)
W=${W:-$HOME/.cache/tina4-worktrees/verify-1029/d-orm-02}
P=${P:-$HOME/.cache/tina4-worktrees}
red=0; green=0
for side in docs book; do
  patch=$P/docfix-dorm02-$side.fix.patch
  n=$(grep -c '^@@' "$patch")
  for i in $(seq 1 "$n"); do
    t=$(mktemp -d); cp -r "$W/fixed/$side/." "$t/"
    # one-hunk patch: file header + hunk i
    awk -v i="$i" '/^@@/{h++} h==0||h==i' "$patch" > "$t.hunk"
    (cd "$t" && git apply -R "$t.hunk") || { echo "$side hunk $i: REVERT FAILED"; exit 2; }
    head=$(grep -m1 '^@@' "$t.hunk")
    var=$( [ $side = docs ] && echo DOCS || echo BOOK )
    out=$(env $var="$t" "$here/prove.sh"); rc=$?
    v=$(grep VERDICT <<<"$out")
    if (( rc == 1 )); then red=$((red+1)); s=RED; else green=$((green+1)); s="STAYED rc=$rc"; fi
    echo "$side hunk $i ${head%% @@*} @@ -> $s | $v"
    rm -rf "$t" "$t.hunk"
  done
done
echo "GATE: $red red, $green not red"
(( green == 0 ))
