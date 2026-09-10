#!/bin/sh
# Proves: the skills installer re-learns a dead host once per file.
#
# Everything runs on loopback against ./mirror, so there is no network dependency and
# no way for a real CDN outage to show up as a failure here. If ./mirror is missing,
# run ./fetch-mirror.sh 3.13.135 once (that step does need the network).
#
# Two halves:
#   1. the installer as the reporter ran it (v3.8.85, two tiers) -- stock vs candidate
#   2. the three-tier installer on origin/main -- gated by the repo's own test harness
#
# Usage: ./prove.sh [path-to-tina4-checkout]
set -u
here="$(cd "$(dirname "$0")" && pwd)"
fork="${1:-/var/home/work/gitdir/tinaforks/tina4}"
pass=0; fail=0; skip=0
ok()   { pass=$((pass+1)); echo "    PASS $1"; }
bad()  { fail=$((fail+1)); echo "    FAIL $1"; }
skp()  { skip=$((skip+1)); echo "    SKIP $1"; }
eq()   { [ "$2" = "$3" ] && ok "$1 ($2)" || bad "$1: expected $3, got $2"; }

if [ ! -d "$here/mirror" ]; then
  echo "no ./mirror -- run ./fetch-mirror.sh 3.13.135 first"; exit 2
fi

# run_two_tier <script> <mode> <retry_count> -> "<exit> <primary_requests> <files>"
run_two_tier() {
  cf="$here/.count.$$"; rm -f "$cf"
  COUNT_FILE="$cf" MODE="$2" python3 "$here/hosts.py" 8901 8902 > "$here/.srv.$$" 2>&1 &
  srv=$!
  until grep -q primary= "$here/.srv.$$" 2>/dev/null; do sleep 0.2; done
  box="$(mktemp -d)"
  env TINA4_SKILLS_TARGET=claude TINA4_SKILLS_HOME="$box" \
      TINA4_SKILLS_PRIMARY_ROOT=http://127.0.0.1:8901 \
      TINA4_SKILLS_MIRROR_ROOT=http://127.0.0.1:8902 \
      TINA4_SKILLS_RETRY_DELAY=0 TINA4_SKILLS_RETRY_COUNT="$3" \
      sh "$1" > "$here/.run.$$" 2>&1
  rc=$?
  primary="$(sed -n 's/.*primary=\([0-9]*\) .*/\1/p' "$cf")"
  files="$(find "$box" -type f | wc -l)"
  kill "$srv" 2>/dev/null; wait "$srv" 2>/dev/null
  rm -rf "$box" "$here/.srv.$$" "$here/.count.$$"
  echo "$rc ${primary:-0} $(echo $files)"
}

echo "########## 1. the installer the report came from (v3.8.85, two tiers) ##########"
echo "  the primary answers 503 for everything; one attempt per source (retry_count=0)"
set -- $(run_two_tier "$here/stock-install-skills.sh" dead-primary 0)
eq "stock: doomed requests to the dead host" "$2" "48"
eq "stock: files installed anyway"           "$3" "48"
eq "stock: exit code"                        "$1" "0"
echo "    ^ 48 files, 48 separate discoveries that the same host is down"

set -- $(run_two_tier "$here/fixed-install-skills.sh" dead-primary 0)
eq "fixed: doomed requests to the dead host" "$2" "1"
eq "fixed: files installed"                  "$3" "48"
eq "fixed: exit code"                        "$1" "0"

echo "  the cost is a function of the retry walk, not of the outage (retry_count=3):"
set -- $(run_two_tier "$here/stock-install-skills.sh" dead-primary 3)
eq "stock at retry_count=3"                  "$2" "192"
set -- $(run_two_tier "$here/fixed-install-skills.sh" dead-primary 3)
eq "fixed at retry_count=3"                  "$2" "4"

echo "  a healthy host must behave exactly as before:"
set -- $(run_two_tier "$here/stock-install-skills.sh" live-primary 0)
stock_live="$2"
set -- $(run_two_tier "$here/fixed-install-skills.sh" live-primary 0)
eq "fixed matches stock when nothing is down" "$2" "$stock_live"

echo "  a 404 is not an outage -- one missing file must not cost the whole host:"
set -- $(MIRROR_MISSING="tina4-developer-php/references/realtime.md" RECOVER_AFTER=1 \
         run_two_tier "$here/fixed-install-skills.sh" recover 0)
eq "fixed: written-off host asked again for the one file only it has" "$2" "2"
eq "fixed: install still completes"                                   "$3" "48"

echo "########## 2. the three-tier installer on origin/main ##########"
if [ ! -d "$fork/.git" ]; then
  skp "no checkout at $fork"
elif ! command -v python3 >/dev/null 2>&1; then
  skp "python3 not available"
else
  cur="$(cd "$fork" && git rev-parse --abbrev-ref HEAD)"
  echo "  checkout: $fork on $cur"
  if (cd "$fork" && timeout 600 python3 tests/skills_installer_http.py shell >/dev/null 2>&1); then
    ok "all five harness contracts pass on this working tree"
  else
    bad "the harness does not pass on this working tree"
  fi
  keep="$(mktemp)"; cp "$fork/install-skills.sh" "$keep"
  (cd "$fork" && git checkout origin/main -- install-skills.sh 2>/dev/null)
  if (cd "$fork" && timeout 600 python3 tests/skills_installer_http.py shell >/dev/null 2>&1); then
    bad "the outage contract passes against origin/main -- it does not gate the fix"
  else
    ok "the outage contract fails against origin/main, so it gates the fix"
  fi
  cp "$keep" "$fork/install-skills.sh"; rm -f "$keep"
  ok "working tree restored"
fi

rm -f "$here"/.run.$$ 2>/dev/null
echo
echo "  pass=$pass fail=$fail skip=$skip"
if [ "$fail" -gt 0 ]; then echo "  FAIL"; exit 1; fi
if [ "$skip" -gt 0 ]; then echo "  PASS (partial: $skip skipped)"; exit 0; fi
echo "  PASS"
