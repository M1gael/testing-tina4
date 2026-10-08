#!/usr/bin/env bash
# tina4-nodejs parity for tina4-php#279: the dev toolbar is put into pages for
# a peer the /__dev gate refuses.
#
#   TREE_ND=<tina4-nodejs source tree, node_modules installed> LAN_IP=<this host's non-loopback IPv4> ./prove.sh
#
# The app runs with TINA4_DEBUG=true bound to 0.0.0.0 (TINA4_HOST=0.0.0.0). Each
# request is sent once from loopback (dialling 127.0.0.1) and once from the
# LAN address (dialling LAN_IP, so the socket peer is LAN_IP), always with
# `Host: localhost:<port>`, which the Host allow-list accepts, and no Origin /
# Sec-Fetch-Site (a direct navigation). Prints the status of /__dev,
# /__dev/toolbar.js and /__dev/toolbar.css, and whether /hello (HTML) and a 404
# page carry the toolbar markup.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${TREE_ND:?set TREE_ND to a tina4-nodejs tree}"
LAN_IP=${LAN_IP:-$(ip -4 -o addr show scope global | awk '{split($4,a,"/"); print a[1]; exit}')}
[ -n "$LAN_IP" ] || { echo "no non-loopback IPv4 found; set LAN_IP"; exit 2; }
NODEBIN=$(dirname "$(readlink -f "$(command -v node)")")
echo "tree: $(git -C "$TREE_ND" rev-parse --short HEAD) ($(git -C "$TREE_ND" describe --tags 2>/dev/null)); node $(node --version); LAN peer $LAN_IP"
RUN=$(mktemp -d); trap 'fuser -k "$P/tcp" >/dev/null 2>&1; rm -rf "$RUN"' EXIT
sed "s|TREE_ND|$TREE_ND|g" "$HERE/app.mts" > "$RUN/app.mts"; mkdir -p "$RUN/home"
P=$(python3 -c 'import socket;s=socket.socket();s.bind(("0.0.0.0",0));print(s.getsockname()[1])')
(cd "$RUN" && exec env -i HOME="$RUN/home" PATH="$NODEBIN:/usr/bin:/bin" TINA4_PORT="$P" TINA4_HOST=0.0.0.0 \
   TINA4_NO_AI_PORT=true TINA4_DEBUG=true TINA4_SECRET="$(python3 -c 'import secrets;print(secrets.token_hex(32))')" \
   node --import "file://$TREE_ND/node_modules/tsx/dist/loader.mjs" app.mts) > "$RUN/srv.log" 2>&1 &
for _ in $(seq 100); do curl -s -o /dev/null "http://127.0.0.1:$P/hello" && break; sleep 0.1; done
for peer in 127.0.0.1 "$LAN_IP"; do
  echo "== peer $peer"
  for path in /__dev /__dev/toolbar.js /__dev/toolbar.css; do
    r=$(curl -s --max-time 5 -H "Host: localhost:$P" -w ' %{http_code}' "http://$peer:$P$path")
    printf '   %-20s %s  %s\n' "$path" "${r##* }" "$(printf '%s' "${r% *}" | head -c 70 | tr '\n' ' ' | grep -o '{"ok".*' || true)"
  done
  for path in /hello /nothing-here; do
    r=$(curl -s --max-time 5 -H "Host: localhost:$P" -w ' %{http_code}' "http://$peer:$P$path")
    printf '   %-20s %s  toolbar markup: %s, toolbar.css link: %s, toolbar.js script: %s\n' "$path" "${r##* }" \
      "$(printf '%s' "$r" | grep -c 'id="tina4-dev-toolbar"')" "$(printf '%s' "$r" | grep -c '/__dev/toolbar.css')" "$(printf '%s' "$r" | grep -c '/__dev/toolbar.js')"
  done
done
