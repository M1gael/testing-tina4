#!/usr/bin/env bash
# Proves f-cli-10: `tina4 books` and `tina4 docs` report a local write failure as a
# network problem (or as nothing at all), exit 0 while doing it, and leave a truncated
# zip behind.
#
# Stock side runs the released 3.8.78 binary, which is upstream `c02cb48` verbatim.
# Fixed side takes a build of the fix branch as $1.
set -u
cd "$(dirname "$0")"
mkdir -p bin
[ -f bin/tina4-3.8.78 ] || curl -fsSL -o bin/tina4-3.8.78 \
  https://github.com/tina4stack/tina4/releases/download/v3.8.78/tina4-linux-amd64
chmod +x bin/tina4-3.8.78

FIXED="${1:-}"
R=$(mktemp -d); trap 'rm -rf "$R"' EXIT; mkdir -p "$R/home"
fail=0
say(){ printf '\n=== %s ===\n' "$1"; }

# $1 label  $2 binary  $3 subcommand  $4 "project" to make it a detectable tina4 app
run_partial(){
  d="$R/$1"; mkdir -p "$d"; cp "$2" "$d/tina4"; chmod +x "$d/tina4"
  [ "${4:-}" = "project" ] && : > "$d/app.py"
  out=$(cd "$d" && ulimit -f 1 && HOME=$R/home PATH=/usr/bin:/bin ./tina4 "$3" 2>&1); code=$?
  left=$(cd "$d" && ls -A | grep -v '^tina4$' | grep -v '^app.py$' | tr '\n' ' ')
  printf '%s\nEXIT=%s\nleft: %s\n' "$out" "$code" "$left"
}

check(){ # $1 output  $2 pattern  $3 message
  grep -q "$2" <<<"$1" || { echo "MISS: $3"; fail=1; }
}

say "1. STOCK 3.8.78 — tina4 books, the write fails"
o=$(run_partial stock-books bin/tina4-3.8.78 books); echo "$o"
check "$o" "Check your connection"  "expected the stock build to blame the connection"
check "$o" "EXIT=0"                 "expected exit 0"
grep '^left:' <<<"$o" | grep -q 'tina4-book.zip' || { echo "MISS: expected a leftover tina4-book.zip"; fail=1; }

say "2. STOCK 3.8.78 — tina4 docs, the write fails"
o=$(run_partial stock-docs bin/tina4-3.8.78 docs project); echo "$o"
check "$o" "Download failed\."      "expected the stock build's bare failure line"
check "$o" "EXIT=0"                 "expected exit 0"
grep '^left:' <<<"$o" | grep -q '.tina4-docs.zip' || { echo "MISS: expected a leftover .tina4-docs.zip"; fail=1; }

if [ -z "$FIXED" ]; then
  echo; echo "(no fixed binary given — stock side only)"
  [ $fail -eq 0 ] && { echo "REPRODUCED: both commands misreport, exit 0, and leave a partial zip."; exit 1; }
  echo "STOCK SIDE DID NOT BEHAVE AS RECORDED"; exit 2
fi

say "3. FIXED — tina4 books, the write fails"
o=$(run_partial fixed-books "$FIXED" books); echo "$o"
check "$o" "Could not download"     "expected the fix to name a local failure"
check "$o" "EXIT=1"                 "expected exit 1"
grep '^left:' <<<"$o" | grep -q 'tina4-book.zip' && { echo "MISS: the partial zip was not cleaned up"; fail=1; }
grep -q "Check your connection" <<<"$o" && { echo "MISS: still blaming the connection"; fail=1; }

say "4. FIXED — tina4 docs, the write fails"
o=$(run_partial fixed-docs "$FIXED" docs project); echo "$o"
check "$o" "Could not download"     "expected the fix to name a local failure"
check "$o" "EXIT=1"                 "expected exit 1"
grep '^left:' <<<"$o" | grep -q '.tina4-docs.zip' && { echo "MISS: the partial zip was not cleaned up"; fail=1; }

echo
[ $fail -eq 0 ] && { echo "PASS: stock misreports, fixed names the real failure, exits 1, cleans up."; exit 0; }
echo "FAILURES ABOVE"; exit 2
