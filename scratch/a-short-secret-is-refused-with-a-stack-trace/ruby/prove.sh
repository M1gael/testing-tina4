#!/usr/bin/env bash
# tina4-ruby: how does a client see a boot refused for a short TINA4_SECRET?
# Usage: TREE=<tina4-ruby checkout> BUNDLE_PATH=<installed bundle> ./prove.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${TREE:?set TREE to a tina4-ruby checkout}"
: "${BUNDLE_PATH:?set BUNDLE_PATH to a directory holding the bundle of TREE}"
export BUNDLE_PATH BUNDLE_GEMFILE=$TREE/Gemfile
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(sed -n 's/.*VERSION = "\(.*\)"/\1/p' "$TREE/lib/tina4/version.rb"))"
good=$(ruby -rsecurerandom -e "puts SecureRandom.hex(32)")   # never written to disk

cell() { # label, secret, debug
  local work port pid status body
  work=$(mktemp -d); cp -r "$here/app/." "$work/"; mkdir -p "$work/home"
  port=$(ruby -rsocket -e 's=TCPServer.new("127.0.0.1",0); puts s.addr[1]; s.close')
  ( cd "$work" && HOME=$work/home TINA4_SECRET="$2" TINA4_DEBUG="$3" TINA4_NO_BROWSER=true \
      TINA4_PORT=$port TINA4_HOST=127.0.0.1 \
      exec bundle exec ruby -I"$TREE/lib" app.rb >"$work/srv.log" 2>&1 ) &
  pid=$!
  for _ in $(seq 100); do
    kill -0 $pid 2>/dev/null || break
    curl -s -o /dev/null "http://127.0.0.1:$port/" 2>/dev/null && break
    sleep 0.1
  done
  if kill -0 $pid 2>/dev/null; then
    status=$(curl -s -o "$work/body" -w '%{http_code}' "http://127.0.0.1:$port/hello")
    body=$(head -c 300 "$work/body" | tr '\n' ' ')
    echo "[$1] server UP; GET /hello -> $status; trace/paths in body: $(grep -c -E 'lib/tina4|\.rb:[0-9]+' "$work/body")"
    fuser -k -s $port/tcp 2>/dev/null; kill $pid 2>/dev/null; wait $pid 2>/dev/null
  else
    wait $pid; local rc=$?
    status=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/hello" 2>/dev/null)
    echo "[$1] process EXITED rc=$rc; no listener (curl: $status)"
    echo "    first error line: $(grep -m1 -E 'Error|error' "$work/srv.log" | sed "s|$TREE|<tree>|g; s|$work|<app>|g" | cut -c1-220)"
  fi
  rm -rf "$work"
}
cell "20-byte secret, TINA4_DEBUG=false" "short-secret-20bytes" false
cell "20-byte secret, TINA4_DEBUG=true " "short-secret-20bytes" true
cell "64-hex secret (control)          " "$good" false
