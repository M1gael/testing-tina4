#!/usr/bin/env bash
#
# prove.sh [script-under-test]
#
# Default is ./stock-sync-tina4-skills.sh — a byte-for-byte copy of
# scripts/sync-tina4-skills.sh at tina4-python origin/v3,
# md5 93e24f04394dec1f2dc1f72ca653e6d7.
#
# Pass a candidate fix as $1 to run the same fixtures against it.
#
#   Fixture C  negative control — every copy present, consistent and clean UTF-8
#   Fixture A  no sibling repos beside tina4-python
#   Fixture B  all three siblings present; every .claude copy matches canonical,
#              the .agents/.cursor maintainer stubs carry BOM + mojibake, and the
#              tina4-developer-<lang> copies have drifted inside each repo
#
# A gate doing its job fails A and B, names what is wrong in each, and passes C.
# C is not decoration: a gate that fails everything is not a gate, and the three
# new assertions are exactly the kind that produce false positives.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
raw="${1:-$here/stock-sync-tina4-skills.sh}"
script="$(cd "$(dirname "$raw")" && pwd)/$(basename "$raw")"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT

echo "script under test : $script"
echo "md5               : $(md5sum "$script" | cut -d' ' -f1)"
echo

run() {
  local root="$work/$1"
  bash "$here/build-fixture.sh" "$root" "$1" "$script"
  ( cd "$root/tina4-python" && HOME="$root/home" bash scripts/sync-tina4-skills.sh --check ) \
    > "$work/$1.out" 2>&1
  echo $? > "$work/$1.code"
}

defects=0
report() {  # $1 = label, $2 = present(1/0), $3 = detail
  if [ "$2" -eq 1 ]; then echo "    DEFECT PRESENT  $1"; echo "      $3"; defects=$((defects+1));
  else echo "    gated          $1"; echo "      $3"; fi
}

# ---------------------------------------------------------------- fixture A
run A; codeA=$(cat "$work/A.code")
echo "=== FIXTURE A — tina4-python alone, no siblings on disk ==="
sed 's/^/    /' "$work/A.out"; echo "    exit: $codeA"; echo
namedA=$(grep -cE 'tina4-php|tina4-ruby|tina4-nodejs' "$work/A.out")
report "f-ai-05(1) absent siblings skipped in silence" \
  "$([ "$codeA" -eq 0 ] && [ "$namedA" -eq 0 ] && echo 1 || echo 0)" \
  "exit $codeA, three ungated repos, named in output: $namedA"
echo

# ---------------------------------------------------------------- fixture B
run B; codeB=$(cat "$work/B.code")
echo "=== FIXTURE B — siblings present; .claude clean, .agents/.cursor corrupt and drifted ==="
sed 's/^/    /' "$work/B.out"; echo "    exit: $codeB"; echo

bom=$(find "$work/B" \( -path '*/.agents/*' -o -path '*/.cursor/*' \) -name SKILL.md \
      -exec sh -c 'head -c3 "$1" | od -An -tx1 | tr -d " " | grep -q efbbbf' _ {} \; -print | wc -l)
namedEnc=$(grep -ciE 'bom|encoding|mojibake' "$work/B.out")
report "f-ai-03 / f-ai-05(2) BOM + mojibake in .agents/.cursor" \
  "$([ "$codeB" -eq 0 ] && [ "$namedEnc" -eq 0 ] && echo 1 || echo 0)" \
  "$bom corrupt files planted, encoding mentioned in output: $namedEnc"

drift=$(find "$work/B" -path '*/.agents/skills/tina4-developer-*' -name SKILL.md | wc -l)
namedDev=$(grep -c 'tina4-developer' "$work/B.out")
report "f-ai-07 tina4-developer-<lang> drifted inside each repo" \
  "$([ "$codeB" -eq 0 ] && [ "$namedDev" -eq 0 ] && echo 1 || echo 0)" \
  "$drift drifted copies planted, tina4-developer mentioned in output: $namedDev"
echo

# ------------------------------------------- fixture C (negative control)
run C; codeC=$(cat "$work/C.code")
echo "=== FIXTURE C — negative control: everything present, consistent, clean ==="
sed 's/^/    /' "$work/C.out"; echo "    exit: $codeC"; echo
if [ "$codeC" -ne 0 ]; then
  echo "    FALSE POSITIVE — the gate rejects a clean tree. It is not usable."
  falsepos=1
else
  echo "    clean tree accepted, exit 0. No false positive."
  falsepos=0
fi
echo

if [ "$falsepos" -eq 1 ]; then
  echo "VERDICT: unusable — fails its own negative control."
  exit 2
fi
if [ "$defects" -gt 0 ]; then
  echo "VERDICT: $defects of 3 defects reproduce against this script."
  exit 1
fi
echo "VERDICT: all 3 gated, and a clean tree still passes."
