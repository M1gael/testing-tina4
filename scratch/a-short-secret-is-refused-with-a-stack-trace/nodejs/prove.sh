#!/usr/bin/env bash
# tina4-nodejs parity for tina4-php#276 case 1: what does a CLIENT see when the
# app boots with a TINA4_SECRET shorter than 32 bytes?
#
#   TREE_ND=<tina4-nodejs source tree, node_modules installed> ./prove.sh
#
# Each cell boots the app in a throwaway dir with a clean environment, then asks
# GET /hello. Prints: whether anything listened, the HTTP status and body (and
# whether the body holds a stack trace or a file path), and the process exit.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${TREE_ND:?set TREE_ND to a tina4-nodejs tree}"
NODE=$(command -v node); NODEBIN=$(dirname "$(readlink -f "$NODE")")
RUN=$(mktemp -d); trap 'rm -rf "$RUN"' EXIT
sed "s|TREE_ND|$TREE_ND|g" "$HERE/app.mts" > "$RUN/app.mts"
echo "tree: $(git -C "$TREE_ND" rev-parse --short HEAD) ($(git -C "$TREE_ND" describe --tags 2>/dev/null)); node $(node --version)"
freeport() { python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
cell() {  # name secret debug
  local P; P=$(freeport); mkdir -p "$RUN/home"
  (cd "$RUN" && exec env -i HOME="$RUN/home" PATH="$NODEBIN:/usr/bin:/bin" TINA4_PORT="$P" TINA4_HOST=127.0.0.1 \
     TINA4_NO_AI_PORT=true TINA4_DEBUG="$3" TINA4_SECRET="$2" \
     node --import "file://$TREE_ND/node_modules/tsx/dist/loader.mjs" app.mts) > "$RUN/srv.log" 2>&1 &
  local pid=$! up=no
  for _ in $(seq 80); do
    if curl -s -o /dev/null "http://127.0.0.1:$P/hello" 2>/dev/null; then up=yes; break; fi
    kill -0 $pid 2>/dev/null || break; sleep 0.1
  done
  local resp; resp=$(curl -s -i --max-time 5 "http://127.0.0.1:$P/hello" 2>&1); local rc=$?
  local status; status=$(printf '%s' "$resp" | head -1 | tr -d '\r')
  local body; body=$(printf '%s' "$resp" | sed '1,/^\r\?$/d')
  local trace=no paths=no
  printf '%s' "$body" | grep -q -E '^\s+at |Stack trace|Error:' && trace=yes
  printf '%s' "$body" | grep -q -E '/packages/core/|/var/|/home/|\.ts:' && paths=yes
  sleep 0.3; local exitc=running
  if ! kill -0 $pid 2>/dev/null; then wait $pid; exitc="exited $?"; fi
  echo "== $1 (TINA4_DEBUG=$3, secret ${#2} bytes)"
  echo "   listener: $up; curl rc=$rc; status: ${status:-<none>}; body: $(printf '%s' "$body" | head -c 60 | tr '\n' ' ')"
  echo "   body trace: $trace; body paths: $paths; process: $exitc"
  echo "   server console (first lines): $(grep -m3 -E 'TINA4_SECRET|Error|at ' "$RUN/srv.log" | tr '\n' '|' | cut -c1-220)"
  fuser -k "$P/tcp" >/dev/null 2>&1; kill $pid 2>/dev/null; wait $pid 2>/dev/null
}
cell short-secret-prod short-secret-20bytes false
cell short-secret-dev  short-secret-20bytes true
cell control-64-hex    "$(python3 -c 'import secrets;print(secrets.token_hex(32))')" false
