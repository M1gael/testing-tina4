#!/bin/bash
# Gate: revert each logical piece of the held fix alone and show prove.sh goes red.
# Usage: FIXED_DOCS=<fixed docs tree> FIXED_BOOK=<fixed book tree> ./gate.sh
# Pieces: each of the 8 files whole; and each of 4 hunk groups across all 8 files.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
RT=${RT:-$HOME/.cache/tina4-worktrees/verify-1029/d-cli-02}
: "${FIXED_DOCS:?}" "${FIXED_BOOK:?}"
DP=${DP:-$HOME/.cache/tina4-worktrees/docfix-dcli02-docs.fix.patch}
BP=${BP:-$HOME/.cache/tina4-worktrees/docfix-dcli02-book.fix.patch}
G="$RT/gate"; rm -rf "$G"; mkdir -p "$G"
FILES="docs/python docs/php docs/ruby docs/nodejs book-1-python book-2-php book-3-ruby book-4-nodejs"
path(){ case $1 in docs/*) echo "$1/19-scaffolding.md";; *) echo "$1/chapters/19-scaffolding.md";; esac; }
fresh(){ # minimal copy of the 8 fixed files (prove.py reads nothing else)
  local f r s; rm -rf "$G/d" "$G/b"
  for f in $FILES; do
    case $f in docs/*) r="$G/d"; s="$FIXED_DOCS";; *) r="$G/b"; s="$FIXED_BOOK";; esac
    mkdir -p "$(dirname "$r/$(path $f)")"; cp "$s/$(path $f)" "$r/$(path $f)"
  done; }
red=0; green=0
judge(){ out=$(DOCS="$G/d" BOOK="$G/b" RT="$RT" "$HERE/prove.sh"); rc=$?
  if [ $rc -eq 0 ]; then echo "GREEN  $1  <- piece did not gate"; green=$((green+1))
  else echo "red    $1  rc=$rc  $(tail -1 <<<"$out")"; red=$((red+1)); fi; }
for f in $FILES; do
  fresh
  case $f in docs/*) (cd "$G/d" && git apply -R --include="$(path $f)" "$DP");;
             *)      (cd "$G/b" && git apply -R --include="$(path $f)" "$BP");; esac
  judge "file $f"; DOCS="$G/d" BOOK="$G/b" RT="$RT" "$HERE/prove.sh" | grep "^BAD" | tr "\n" " "; echo
done
for grp in intro block table crud; do
  fresh
  python3 -I "$HERE/revert_group.py" "$grp" "$G/d" "$G/b" || { echo "revert $grp failed"; exit 2; }
  judge "group $grp (all 8 files)"
done
echo "GATE: red=$red green=$green"
[ $green -eq 0 ]
