#!/bin/sh
# Runs INSIDE `unshare -rnm`: a network namespace with no route off this machine, so an app that
# binds every interface here is exposed to nothing. That is the point -- the bind address is the
# claim, and it can be read without ever putting an unauthenticated run_shell on a real LAN.
#
# 10.99.0.1 is added to lo purely as a NON-loopback address to dial. A server bound to 127.0.0.1
# refuses it; a server bound to 0.0.0.0 answers it.
set -e
ip link set lo up
ip addr add 10.99.0.1/32 dev lo
ip addr add 127.0.0.1/8 dev lo 2>/dev/null || true

PORT="$1"; TREE="$2"; LOG="${3:-/tmp/agent-boot.log}"
cd "$TREE"
"$TREE/node_modules/.bin/tsx" app.ts >"$LOG" 2>&1 &
APP=$!

i=0
while [ $i -lt 90 ]; do
  if ss -ltn 2>/dev/null | grep -q ":$PORT "; then break; fi
  sleep 1; i=$((i+1))
done

echo "BIND      $(ss -ltn 2>/dev/null | grep ":$PORT " | awk '{print $4}' | head -1)"
# `|| echo` is wrong here: curl prints the code AND exits non-zero for a 101 upgrade it cannot
# complete, so the fallback string got appended to a perfectly good status. Take the code, ignore
# the exit; 000 already means "never connected".
code() { curl -s -o /dev/null -m 5 -w '%{http_code}' "$@" 2>/dev/null || true; }
echo "LOOPBACK  $(code "http://127.0.0.1:$PORT/api/sessions")"
echo "OFF-LOOP  $(code "http://10.99.0.1:$PORT/api/sessions")"
echo "BODY      $(curl -s -m 5 "http://10.99.0.1:$PORT/api/sessions" 2>/dev/null | head -c 90)"
echo "AUTHHDR   $(code -H 'Authorization:' "http://10.99.0.1:$PORT/api/sessions")"
# 101 = the WebSocket the whole UI runs on actually upgraded. A bind change that quietly broke
# /ws/agent would leave every HTTP check green and the product dead.
echo "WSUPGRADE $(code -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' "http://127.0.0.1:$PORT/ws/agent")"
echo "WARNED    $(grep -c 'NO authentication' "$LOG" 2>/dev/null || echo 0)"

kill -TERM "$APP" 2>/dev/null || true
sleep 1
kill -KILL "$APP" 2>/dev/null || true
