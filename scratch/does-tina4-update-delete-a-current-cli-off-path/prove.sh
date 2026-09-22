#!/usr/bin/env bash
# f-cli-19 — `tina4 update` deletes binaries off PATH with no confirmation, on a
# test that matches version strings a current (v3) CLI can print.
#
# Green (exit 0) = the defect is present, as described.
# Red   (exit 1) = behaviour changed; re-read the mechanism before trusting this row.
#
# Everything happens inside SB. The real PATH is never used: the sandbox PATH
# contains only the decoy dirs plus /usr/bin and /bin, so `which` cannot reach
# any tina4* binary that belongs to this machine.
set -u
SB="${SB:-$HOME/.cache/tina4-update-probe/prove19}"
TAG="${TAG:-v3.8.88}"
rm -rf "$SB"; mkdir -p "$SB"/{bin,home,decoys,vendor/bin,node_modules/.bin,realruby}
# BIN=<path> runs a locally built binary instead of the release: that is how the
# candidate fix is checked against the same measurements.
if [ -n "${BIN:-}" ]; then
  cp "$BIN" "$SB/bin/tina4"
else
  curl -fsSL "https://github.com/tina4stack/tina4/releases/download/$TAG/tina4-linux-amd64" -o "$SB/bin/tina4" || exit 2
fi
chmod +x "$SB/bin/tina4"
echo "CLI under test: $("$SB/bin/tina4" --version)"

mk(){ printf '#!/bin/sh\necho "%s"\n' "$2" > "$1"; chmod +x "$1"; }
run(){ env -i HOME="$SB/home" PATH="$1:/usr/bin:/bin" TERM=dumb "$SB/bin/tina4" update < /dev/null; }
fail=0
check(){ # check <path> <expected: PRESENT|GONE> <label>
  if [ -e "$1" ]; then got=PRESENT; else got=GONE; fi
  if [ "$got" = "$2" ]; then echo "  ok   $3 ($got)"; else echo "  FAIL $3 (expected $2, got $got)"; fail=1; fi
}

echo "--- round 1: decoys print a v3 help screen with no 1./2./Thor/Deprecation"
mk "$SB/decoys/tina4python" "Tina4 Python CLI"
mk "$SB/decoys/tina4php"    "Tina4 PHP CLI v3"
run "$SB/decoys" > "$SB/run1.log" 2>&1
check "$SB/decoys/tina4python" PRESENT "no marker in output -> kept"
check "$SB/decoys/tina4php"    PRESENT "no marker in output -> kept"

echo "--- round 2: version strings, both directions, no prompt (stdin is /dev/null)"
rm -f "$SB"/decoys/*
mk "$SB/decoys/tina4python" "Tina4 Python CLI 3.1.0"
mk "$SB/decoys/tina4php"    "Tina4 PHP CLI 3.13.136"
mk "$SB/decoys/tina4ruby"   "tina4-ruby 0.2.206"
mk "$SB/decoys/tina4nodejs" "Tina4 Node CLI Thor 9.9.9"
run "$SB/decoys" > "$SB/run2.log" 2>&1
check "$SB/decoys/tina4python" GONE    "3.1.0 contains '1.' -> DELETED"
check "$SB/decoys/tina4ruby"   GONE    "0.2.206 contains '2.' -> DELETED"
check "$SB/decoys/tina4nodejs" GONE    "Thor -> DELETED (this one is the intended target)"
check "$SB/decoys/tina4php"    PRESENT "3.13.136 contains neither -> kept"
grep -q 'Remove\|remove' "$SB/run2.log" && echo "  ok   removal is announced, not asked" || { echo "  FAIL no removal in log"; fail=1; }
grep -qi 'y/n\|\[Y/n\]\|continue?' "$SB/run2.log" && { echo "  FAIL a prompt appeared"; fail=1; } || echo "  ok   no confirmation prompt"

echo "--- round 3: the marker can come from an unrelated runtime version, and the skip paths"
rm -f "$SB"/decoys/*
mk "$SB/vendor/bin/tina4python"        "Tina4 Python CLI 3.1.0"
mk "$SB/node_modules/.bin/tina4nodejs" "Tina4 Node CLI Thor 9.9.9"
mk "$SB/decoys/tina4php"               "Tina4 PHP CLI 3.13.136 (PHP 8.2.1)"
mk "$SB/realruby/tina4ruby"            "Tina4 Ruby CLI 3.1.0"
ln -sf "$SB/realruby/tina4ruby" "$SB/decoys/tina4ruby"
run "$SB/vendor/bin:$SB/node_modules/.bin:$SB/decoys" > "$SB/run3.log" 2>&1
check "$SB/decoys/tina4php"               GONE    "current tina4 version, '2.' came from (PHP 8.2.1) -> DELETED"
check "$SB/vendor/bin/tina4python"        PRESENT "path contains vendor -> skipped"
check "$SB/node_modules/.bin/tina4nodejs" PRESENT "path contains node_modules -> skipped"
check "$SB/realruby/tina4ruby"            PRESENT "symlink target survives"
[ -L "$SB/decoys/tina4ruby" ] && { echo "  FAIL symlink still there"; fail=1; } || echo "  ok   the PATH symlink itself was removed"

echo "--- control: doctor removes nothing"
rm -f "$SB"/decoys/*; mk "$SB/decoys/tina4python" "Tina4 Python CLI 3.1.0"
env -i HOME="$SB/home" PATH="$SB/decoys:/usr/bin:/bin" TERM=dumb "$SB/bin/tina4" doctor < /dev/null > "$SB/run5.log" 2>&1
check "$SB/decoys/tina4python" PRESENT "doctor is not the command that deletes"

[ $fail -eq 0 ] && { echo "VERDICT: defect present, as described"; exit 0; } || { echo "VERDICT: behaviour differs — re-read the row"; exit 1; }
