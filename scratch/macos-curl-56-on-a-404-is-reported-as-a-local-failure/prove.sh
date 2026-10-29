#!/bin/bash
# Usage: prove.sh <tina4 binary>. Runs `tina4 update` from a throwaway install dir
# under a stand-in for macOS curl 8.7.1 (exit 56 for HTTP errors and write errors).
# Prints PASS/FAIL per case; exits non-zero if any case fails.
BIN=$(readlink -f "$1"); D=$(cd "$(dirname "$0")" && pwd); fails=0
run() { # name, expect-regex, reject-regex, env...
  local name=$1 want=$2 reject=$3; shift 3
  local t; t=$(mktemp -d); cp "$BIN" "$t/tina4"
  [ -n "$DEVFULL" ] && ln -s /dev/full "$t/tina4.tmp"
  out=$(cd "$t" && env HOME="$t/home" PATH="$D/bin:/usr/bin:/bin" "$@" timeout 120 ./tina4 update 2>&1)
  if grep -qE "$want" <<<"$out" && ! grep -qE "$reject" <<<"$out"; then echo "PASS $name"; else echo "FAIL $name"; fails=$((fails+1)); fi
  printf '%s\n' "$out" > "$D/logs/$name.log"
  rm -rf "$t"
}
mkdir -p "$D/logs"
# 1: the field report (3.8.105 tagged, not published). v9.9.8 has no assets either: every name 404s, curl says (56).
run 404-under-56 "no build|not published|refused|404" "asset is fine" FAKE_LATEST=v9.9.8
# 2: a write failure that curl reports as 56 must still name the directory.
DEVFULL=1 run write-under-56 "could not write the file" "printed its own reason|publishes no asset" FAKE_LATEST=v9.9.9 FAKE_SERVE_FROM=v3.8.106
DEVFULL=
# 3: control, curl's real codes (22 on a 404): unchanged behaviour.
run 404-under-22 "no build|not published|refused|404" "asset is fine" FAKE_LATEST=v9.9.8 REAL_PASSTHRU=1
exit $fails
