#!/usr/bin/env bash
# Proves f-cli-05: `tina4 update` reports a local write failure as a missing
# platform build, exits 0 while doing it, and leaves a truncated download.
#
# Stock side runs released 3.8.69 (bin/tina4-3.8.69).
# Fixed side needs a build of fix/update-reports-the-real-download-failure
# with the crate version lowered below 3.8.78, passed as $1.
set -u
cd "$(dirname "$0")"
# bin/ is gitignored -- 11MB release binaries do not belong in the repo.
mkdir -p bin
[ -f bin/tina4-3.8.69 ] || curl -fsSL -o bin/tina4-3.8.69 \
  https://github.com/tina4stack/tina4/releases/download/v3.8.69/tina4-linux-amd64
chmod +x bin/tina4-3.8.69; R=$(mktemp -d); trap 'rm -rf "$R"' EXIT; mkdir -p "$R/home"
fail=0
say(){ printf '\n=== %s ===\n' "$1"; }
mk(){ d="$R/$1"; mkdir -p "$d"; cp "$2" "$d/tina4"; chmod +x "$d/tina4"; }

run_unwritable(){ mk "$1-A" "$2"; chmod 555 "$R/$1-A"
  out=$(cd "$R/$1-A" && HOME=$R/home PATH=/usr/bin:/bin ./tina4 update 2>&1); code=$?
  chmod 755 "$R/$1-A"; left=$(ls "$R/$1-A" | tr '\n' ' '); printf '%s\nEXIT=%s\nfiles: %s\n' "$out" "$code" "$left"; }

run_partial(){ mk "$1-B" "$2"
  out=$(cd "$R/$1-B" && ulimit -f 64 && HOME=$R/home PATH=/usr/bin:/bin ./tina4 update 2>&1); code=$?
  left=$(ls "$R/$1-B" | tr '\n' ' '); printf '%s\nEXIT=%s\nfiles: %s\n' "$out" "$code" "$left"; }

say "1. STOCK 3.8.69 - destination not writable"
o=$(run_unwritable stock bin/tina4-3.8.69); echo "$o"
grep -q "tina4-linux-x86_64" <<<"$o" || { echo "MISS: expected a phantom-name 404"; fail=1; }
grep -q "EXIT=0"             <<<"$o" || { echo "MISS: expected exit 0"; fail=1; }

say "2. STOCK 3.8.69 - write fails partway (leaves a truncated file)"
o=$(run_partial stock bin/tina4-3.8.69); echo "$o"
grep '^files:' <<<"$o" | grep -q "tina4.tmp" || { echo "MISS: expected a leftover tina4.tmp"; fail=1; }
grep -q "EXIT=0"    <<<"$o" || { echo "MISS: expected exit 0"; fail=1; }

say "3. Every generated candidate name, against the published assets"
for n in tina4-linux-amd64 tina4-linux-x86_64 tina4-darwin-arm64 tina4-darwin-aarch64 \
         tina4-macos-arm64 tina4-macos-aarch64 tina4-windows-amd64.exe; do
  printf '  %-26s %s\n' "$n" \
    "$(curl -s -o /dev/null -w '%{http_code}' -L "https://github.com/tina4stack/tina4/releases/download/v3.8.78/$n")"
done
echo "  (only the first of each platform pair is published today; macos-* and"
echo "   linux-x86_64 were real in v3.1.4 / v3.1.9, aarch64 spellings never were)"

if [ $# -ge 1 ] && [ -x "$1" ]; then
  if "$1" --version 2>/dev/null | grep -q "3.8.78"; then
    echo "ABORT: the fixed build reports 3.8.78, which equals the latest release,"
    echo "so \`update\` short-circuits on 'already up to date' and sections 4-5"
    echo "would measure nothing. Rebuild it with the crate version lowered."
    exit 2
  fi
  say "4. FIXED - destination not writable"
  o=$(run_unwritable fixed "$1"); echo "$o"
  grep -qi "this failed on this machine" <<<"$o" || { echo "MISS: no local diagnosis"; fail=1; }
  grep -q "tina4-linux-x86_64"          <<<"$o" && { echo "MISS: still tried a phantom name"; fail=1; }
  grep -q "EXIT=1"                      <<<"$o" || { echo "MISS: expected exit 1"; fail=1; }
  say "5. FIXED - write fails partway, no file left behind"
  o=$(run_partial fixed "$1"); echo "$o"
  grep '^files:' <<<"$o" | grep -q "tina4.tmp" && { echo "MISS: truncated file survived"; fail=1; }
  grep -q "EXIT=1"    <<<"$o" || { echo "MISS: expected exit 1"; fail=1; }
else
  say "4-5. SKIPPED - pass a path to a fixed build to check the other side"
fi

printf '\n%s\n' "$([ $fail -eq 0 ] && echo 'VERDICT: as recorded' || echo 'VERDICT: MISMATCH')"
exit $fail
