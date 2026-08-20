#!/usr/bin/env bash
# Proof: ResponseCache replays one session's response to another.
#
# Runs the REAL Tina4 dev server and drives it over real HTTP. Every probe
# prints PASS/FAIL against what SHOULD happen, so a green run means the
# framework is behaving and a red run localises which property broke.
#
#   ./prove.sh            probe the framework as installed
#   ./prove.sh --fixed    same probes with the candidate patch applied,
#                         then restore the venv
#
# The server is always stopped by PID. Never pattern-kill here: a pattern
# containing the port also matches the shell running the pattern.

set -uo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-17451}"
BASE="http://127.0.0.1:${PORT}"
SITE="$(.venv/bin/python -c 'import tina4_python,os;print(os.path.dirname(tina4_python.__file__))')"
CACHE_PY="${SITE}/cache/__init__.py"
BACKUP="$(mktemp -t cache-stock-XXXXXX.py)"
PATCH="../.fw17-candidate.patch"
SERVER_PID=""
FAILURES=0

cleanup() {
  if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null
    for _ in $(seq 1 20); do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      sleep 0.25
    done
    kill -9 "$SERVER_PID" 2>/dev/null
  fi
  if [ -s "$BACKUP" ]; then
    cp "$BACKUP" "$CACHE_PY"
    echo "  venv restored from backup"
  fi
  rm -f "$BACKUP"
}
trap cleanup EXIT INT TERM

start_server() {
  TINA4_PORT="$PORT" TINA4_OVERRIDE_CLIENT=true .venv/bin/python app.py > logs/prove-server.log 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 60); do
    if curl -fsS -m 2 "${BASE}/public/anon" > /dev/null 2>&1; then sleep 0.5; return 0; fi
    kill -0 "$SERVER_PID" 2>/dev/null || { echo "server died on startup:"; tail -20 logs/prove-server.log; return 1; }
    sleep 0.5
  done
  echo "server never became ready:"; tail -20 logs/prove-server.log; return 1
}

# fetch <path> [cookie] -> sets globals BODY and LAST_XCACHE.
# Deliberately NOT used via $( ): a command substitution runs this in a subshell,
# so the globals it sets would be discarded and X-Cache would read as unset.
BODY=""
LAST_XCACHE=""
fetch() {
  local path="$1" cookie="${2:-}" hdrs
  hdrs="$(mktemp)"
  if [ -n "$cookie" ]; then
    BODY="$(curl -fsS -m 5 -D "$hdrs" -H "Cookie: session=${cookie}" "${BASE}${path}" 2>/dev/null)"
  else
    BODY="$(curl -fsS -m 5 -D "$hdrs" "${BASE}${path}" 2>/dev/null)"
  fi
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

if [ "${1:-}" = "--fixed" ]; then
  echo "Applying candidate patch to the installed framework (will be restored)."
  cp "$CACHE_PY" "$BACKUP"
  # Only the cache/__init__.py hunk — the patch also carries a framework test
  # file that has no meaning inside site-packages.
  awk '/^diff --git a\/tina4_python\/cache\/__init__\.py/{p=1} /^diff --git/&&!/cache\/__init__\.py/{p=0} p' "$PATCH" > "${BACKUP}.hunk"
  # Apply in a scratch tree OUTSIDE any git repo. site-packages lives under
  # .venv/, which this repo gitignores, and `git apply` silently SKIPS a patch
  # whose target is an ignored path — it reports success and changes nothing.
  STAGE="$(mktemp -d)"
  mkdir -p "${STAGE}/tina4_python/cache"
  cp "$CACHE_PY" "${STAGE}/tina4_python/cache/__init__.py"
  if ! ( cd "$STAGE" && git apply -p1 "${BACKUP}.hunk" ); then
    echo "patch failed to apply"; rm -rf "$STAGE" "${BACKUP}.hunk"; exit 1
  fi
  if cmp -s "$CACHE_PY" "${STAGE}/tina4_python/cache/__init__.py"; then
    echo "patch applied but changed nothing — refusing to report a fixed run"
    rm -rf "$STAGE" "${BACKUP}.hunk"; exit 1
  fi
  cp "${STAGE}/tina4_python/cache/__init__.py" "$CACHE_PY"
  rm -rf "$STAGE" "${BACKUP}.hunk"
  find "$SITE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
  echo "  patch applied"
  MODE="WITH CANDIDATE FIX"
else
  MODE="STOCK FRAMEWORK (as installed)"
fi

VERSION="$(.venv/bin/python -c 'import tina4_python;print(tina4_python.__version__)' 2>/dev/null || echo unknown)"
echo
echo "=============================================================="
echo " ResponseCache cross-session replay — ${MODE}"
echo " tina4-python ${VERSION}   port ${PORT}"
echo "=============================================================="
start_server || exit 1
echo

# ---- 1. cross-session replay -------------------------------------------
echo "1. Two sessions, same URL /account/balance"
fetch /account/balance alice_session_token; A="$BODY"; A_X="$LAST_XCACHE"
fetch /account/balance bob_session_token;   B="$BODY"; B_X="$LAST_XCACHE"
echo "   ALICE sent Cookie: session=alice_session_token"
echo "     -> X-Cache: ${A_X:-none}  ${A}"
echo "   BOB   sent Cookie: session=bob_session_token"
echo "     -> X-Cache: ${B_X:-none}  ${B}"
case "$B" in *"Alice"*) LEAK=yes;; *) LEAK=no;; esac
check "BOB must NOT receive Alice's body" \
      "$([ "$LEAK" = no ] && echo yes || echo no)" \
      "BOB received Alice's account data — cross-user leak"
echo

# ---- 2. no-store opt-out ------------------------------------------------
echo "2. Response sets Cache-Control: no-store on /account/no-store"
fetch /account/no-store alice_session_token
fetch /account/no-store bob_session_token; NB="$BODY"
case "$NB" in *"Alice"*) NLEAK=yes;; *) NLEAK=no;; esac
echo "   BOB -> ${NB}"
check "no-store must prevent storage" \
      "$([ "$NLEAK" = no ] && echo yes || echo no)" \
      "no-store was ignored; Alice's body replayed to BOB"
echo

# ---- 3. control: public pages must STILL cache --------------------------
echo "3. Control — Cache-Control: public must still cache (cookies present)"
fetch /public/catalog alice_session_token
fetch /public/catalog bob_session_token
CX="$LAST_XCACHE"
echo "   second request X-Cache: ${CX:-none}"
check "public response still served from cache" \
      "$([ "$CX" = "HIT" ] && echo yes || echo no)" \
      "expected X-Cache: HIT, got '${CX:-none}' — the fix disabled caching outright"
echo

# ---- 4. control: cookieless traffic unaffected --------------------------
echo "4. Control — no cookie at all must still cache"
fetch /public/anon
fetch /public/anon
AX="$LAST_XCACHE"
echo "   second request X-Cache: ${AX:-none}"
check "cookieless response still served from cache" \
      "$([ "$AX" = "HIT" ] && echo yes || echo no)" \
      "expected X-Cache: HIT, got '${AX:-none}'"
echo

echo "=============================================================="
if [ "$FAILURES" -eq 0 ]; then
  echo " VERDICT: all properties hold"
else
  echo " VERDICT: ${FAILURES} property/properties broken"
fi
echo "=============================================================="
exit "$FAILURES"
