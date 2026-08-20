#!/usr/bin/env bash
# Proof: @cached decorator never attaches the response cache (stock 3.13.107).
#
# Runs the REAL Tina4 dev server and drives it over real HTTP. Every probe
# prints PASS/FAIL against what SHOULD happen according to documentation,
# so a green run means the framework behaves and a red run localises which
# property is broken.
#
#   ./prove.sh            probe the framework as installed
#
# The server is always stopped by PID. Never pattern-kill here: a pattern
# containing the port also matches the shell running the pattern.

set -uo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-17453}"
BASE="http://127.0.0.1:${PORT}"
SERVER_PID=""
FAILURES=0

mkdir -p logs evidence

cleanup() {
  if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null
    for _ in $(seq 1 20); do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      sleep 0.25
    done
    kill -9 "$SERVER_PID" 2>/dev/null
  fi
}
trap cleanup EXIT INT TERM

start_server() {
  TINA4_PORT="$PORT" TINA4_OVERRIDE_CLIENT=true .venv/bin/python app.py > logs/prove-server.log 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 60); do
    if curl -fsS -m 2 "${BASE}/undecorated" > /dev/null 2>&1; then sleep 0.5; return 0; fi
    kill -0 "$SERVER_PID" 2>/dev/null || { echo "server died on startup:"; tail -20 logs/prove-server.log; return 1; }
    sleep 0.5
  done
  echo "server never became ready:"; tail -20 logs/prove-server.log; return 1
}

# fetch <path> -> sets globals BODY, LAST_XCACHE, LAST_STATUS
BODY=""
LAST_XCACHE=""
LAST_STATUS=""
fetch() {
  local path="$1" hdrs
  hdrs="$(mktemp)"
  BODY="$(curl -fsS -m 5 -D "$hdrs" "${BASE}${path}" 2>/dev/null)" || BODY=""
  LAST_STATUS="$(grep -i '^http/' "$hdrs" | tail -1 | tr -d '\r' | awk '{print $2}')"
  LAST_XCACHE="$(grep -i '^x-cache:' "$hdrs" | head -1 | tr -d '\r' | awk '{print $2}')"
  rm -f "$hdrs"
}

check() { # check <label> <condition-result> <detail>
  if [ "$2" = "yes" ]; then
    printf '  PASS  %s\n' "$1"
  else
    printf '  FAIL  %s\n        %s\n' "$1" "$3"
    FAILURES=$((FAILURES+1))
  fi
}

VERSION="$(.venv/bin/python -c 'import tina4_python;print(tina4_python.__version__)' 2>/dev/null || echo unknown)"
echo
echo "=============================================================="
echo " @cached decorator attach probe — STOCK FRAMEWORK"
echo " tina4-python ${VERSION}   port ${PORT}"
echo "=============================================================="
start_server || exit 1
echo

# ---- 1. /docs-order (@cached above @get - documented order) -------------
echo "1. Route /docs-order — @cached(max_age=120) above @get (documented order)"
fetch /docs-order; A1="$BODY"; A1_X="$LAST_XCACHE"
sleep 0.1
fetch /docs-order; A2="$BODY"; A2_X="$LAST_XCACHE"
echo "   first  request -> X-Cache: ${A1_X:-none}  body: ${A1}"
echo "   second request -> X-Cache: ${A2_X:-none}  body: ${A2}"
check "@cached above @get should serve second response from cache (X-Cache: HIT)" \
      "$([ "$A2_X" = "HIT" ] && echo yes || echo no)" \
      "expected X-Cache: HIT, got '${A2_X:-none}' (body changed: $([ "$A1" != "$A2" ] && echo yes || echo no))"
echo

# ---- 2. /reversed-order (@get above @cached - innermost decorator) ------
echo "2. Route /reversed-order — @get above @cached(max_age=120) (reversed order)"
fetch /reversed-order; B1="$BODY"; B1_X="$LAST_XCACHE"
sleep 0.1
fetch /reversed-order; B2="$BODY"; B2_X="$LAST_XCACHE"
echo "   first  request -> X-Cache: ${B1_X:-none}  body: ${B1}"
echo "   second request -> X-Cache: ${B2_X:-none}  body: ${B2}"
check "@get above @cached should serve second response from cache (X-Cache: HIT)" \
      "$([ "$B2_X" = "HIT" ] && echo yes || echo no)" \
      "expected X-Cache: HIT, got '${B2_X:-none}' (body changed: $([ "$B1" != "$B2" ] && echo yes || echo no))"
echo

# ---- 3. control: /middleware-form (middleware=["ResponseCache:120"]) ----
echo "3. Control — /middleware-form with middleware=[\"ResponseCache:120\"]"
fetch /middleware-form; C1="$BODY"; C1_X="$LAST_XCACHE"
sleep 0.1
fetch /middleware-form; C2="$BODY"; C2_X="$LAST_XCACHE"
echo "   first  request -> X-Cache: ${C1_X:-none}  body: ${C1}"
echo "   second request -> X-Cache: ${C2_X:-none}  body: ${C2}"
check "middleware=[\"ResponseCache:120\"] serves second response from cache (X-Cache: HIT)" \
      "$([ "$C2_X" = "HIT" ] && [ "$C1" = "$C2" ] && echo yes || echo no)" \
      "expected X-Cache: HIT with identical body, got '${C2_X:-none}'"
echo

# ---- 4. control: /undecorated (no cache requested) ----------------------
echo "4. Control — /undecorated (no cache requested)"
fetch /undecorated; D1="$BODY"; D1_X="$LAST_XCACHE"
sleep 0.1
fetch /undecorated; D2="$BODY"; D2_X="$LAST_XCACHE"
echo "   first  request -> X-Cache: ${D1_X:-none}  body: ${D1}"
echo "   second request -> X-Cache: ${D2_X:-none}  body: ${D2}"
check "undecorated route is not cached (no X-Cache, body updates)" \
      "$([ -z "$D1_X" ] && [ -z "$D2_X" ] && [ "$D1" != "$D2" ] && echo yes || echo no)" \
      "expected no X-Cache and fresh body per request"
echo

echo "=============================================================="
if [ "$FAILURES" -eq 0 ]; then
  echo " VERDICT: all properties hold"
else
  echo " VERDICT: ${FAILURES} property/properties broken"
fi
echo "=============================================================="
exit "$FAILURES"
