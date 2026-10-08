#!/usr/bin/env bash
# tina4-python: is the dev toolbar injected into pages for a peer that /__dev refuses?
# The server binds 0.0.0.0; the same requests come once from 127.0.0.1 and once from
# this machine's own LAN address (the kernel then uses that address as the source,
# so the app sees a non-loopback peer, as it sees a Docker gateway). The Host header
# is one the allow-list accepts, so only the peer gate decides.
# Usage: TREE=<tina4-python checkout with .venv> ./prove.sh
set -u
TREE=${TREE:?set TREE to a tina4-python checkout with a .venv}
PY=${PY:-$TREE/.venv/bin/python}
here=$(cd "$(dirname "$0")" && pwd)
lan=$(ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -1)
[ -n "$lan" ] || { echo "no non-loopback IPv4 address on this machine"; exit 2; }
work=$(mktemp -d); export HOME=$work/home; mkdir -p "$HOME"; pid=
trap '[ -n "$pid" ] && kill $pid 2>/dev/null; rm -rf "$work"' EXIT
cp "$here/app.py" "$work/"
port=$($PY -c 'import socket;s=socket.socket();s.bind(("",0));print(s.getsockname()[1])')
token=$(head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n')
echo "tree: $(git -C "$TREE" rev-parse --short HEAD), $(grep -m1 '^version' "$TREE/pyproject.toml"), $($PY -V); LAN peer $lan"

serve() {
  (cd "$work" && exec env TINA4_DEBUG=true TINA4_HOST=0.0.0.0 TINA4_NO_AI_PORT=true TINA4_PORT=$port "$@" \
     TINA4_SECRET="$(head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')" "$PY" app.py --managed) >"$work/srv.log" 2>&1 & pid=$!
  for _ in $(seq 75); do curl -s -o /dev/null "http://127.0.0.1:$port/hello" && break; sleep 0.2; done
}
stop() { kill $pid 2>/dev/null; wait $pid 2>/dev/null; pid=; }
probe() { local peer=$1; shift
  local js css dev page err
  js=$(curl -s -o "$work/b" -w '%{http_code}' -H "Host: localhost:$port" "$@" "http://$peer:$port/__dev/toolbar.js"); err=$(head -c 80 "$work/b" | tr -d '\n')
  css=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: localhost:$port" "$@" "http://$peer:$port/__dev/toolbar.css")
  dev=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: localhost:$port" "$@" "http://$peer:$port/__dev")
  page=$(curl -s -H "Host: localhost:$port" "$@" "http://$peer:$port/hello" | grep -c 'id="tina4-dev-toolbar"')
  echo "   toolbar.js $js, toolbar.css $css, /__dev $dev; toolbar in /hello: $page$( [ "$js" = 403 ] && printf '; refusal: %s' "$err")"
}
serve
echo "== peer 127.0.0.1";                probe 127.0.0.1
echo "== peer $lan (non-loopback)";      probe "$lan"
stop
serve TINA4_MCP_TOKEN=$token
echo "== peer $lan, TINA4_MCP_TOKEN set, no header (what a browser sends)"; probe "$lan"
echo "== peer $lan, TINA4_MCP_TOKEN set, Authorization: Bearer";         probe "$lan" -H "Authorization: Bearer $token"
stop
