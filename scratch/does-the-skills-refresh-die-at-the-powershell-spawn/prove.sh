#!/usr/bin/env bash
# Does the silent skip come from run_status's .unwrap_or(false) swallowing a
# spawn failure?  Single factor: ONE symlink, `sh`, in an otherwise complete
# PATH.  Everything else -- curl, the network, the installer, HOME -- is held
# fixed.  Exit 0 when the two arms differ as the mechanism predicts.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
tina4="$here/tina4-3.8.88-stock"
run="$here/run"; rm -rf "$run"; mkdir -p "$run"

# A PATH farm holding every /usr/bin executable EXCEPT `sh`.
farm="$run/farm"; mkdir -p "$farm"
n=0
for f in /usr/bin/*; do
  b="${f##*/}"
  [ "$b" = "sh" ] && continue
  [ -x "$f" ] || continue
  ln -sf "$f" "$farm/$b" && n=$((n+1))
done
echo "farm: $n executables, sh withheld"
command -v curl >/dev/null || { echo "no curl on this box"; exit 2; }
PATH="$farm" command -v curl >/dev/null || { echo "farm lost curl"; exit 2; }
PATH="$farm" command -v sh    >/dev/null && { echo "farm still has sh -- not a single factor"; exit 2; }

arm () { # $1 = label
  local home="$run/home-$1"; mkdir -p "$home"
  PATH="$farm" HOME="$home" "$tina4" skills all >"$run/$1.out" 2>"$run/$1.err"
  echo "$?" > "$run/$1.code"
}

echo; echo "== A: sh withheld =="
arm A
sed 's/^/  | /' "$run/A.out"; sed 's/^/  E /' "$run/A.err"
echo "  exit=$(cat "$run/A.code")  stdout=$(wc -c <"$run/A.out")b stderr=$(wc -c <"$run/A.err")b"

ln -sf /usr/bin/sh "$farm/sh" 2>/dev/null || ln -sf "$(command -v sh)" "$farm/sh"
echo; echo "== B: identical, plus one symlink: sh =="
arm B
sed 's/^/  | /' "$run/B.out"; sed 's/^/  E /' "$run/B.err"
echo "  exit=$(cat "$run/B.code")  stdout=$(wc -c <"$run/B.out")b stderr=$(wc -c <"$run/B.err")b"

echo
skip='Skills install skipped'
a_skip=$(grep -c "$skip" "$run/A.out")
a_cause=$(grep -cE 'Could not (download|create)' "$run/A.out")
a_quiet=$([ ! -s "$run/A.err" ] && echo yes || echo no)
b_hdr=$(grep -c 'Tina4 Skills Installer' "$run/B.out")
echo "A: skip line=$a_skip  cause line=$a_cause  stderr empty=$a_quiet"
echo "B: installer header=$b_hdr"
if [ "$a_skip" -ge 1 ] && [ "$a_cause" -eq 0 ] && [ "$a_quiet" = yes ] && [ "$b_hdr" -ge 1 ]; then
  echo "VERDICT: reproduced -- withholding the spawned program alone produces the silent skip"; exit 0
fi
echo "VERDICT: NOT reproduced -- the mechanism does not hold here"; exit 1
