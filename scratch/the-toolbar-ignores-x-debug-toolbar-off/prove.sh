#!/usr/bin/env bash
# Usage: TREE=<tina4-php tree with vendor/> ./prove.sh
# Dev mode, loopback caller: does a route answering `X-Debug-Toolbar: off` still get the toolbar?
set -u
here=$(cd "$(dirname "$0")" && pwd); : "${TREE:?set TREE}"
work=$(mktemp -d); cp -r "$here/app/." "$work/"
port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
( cd "$work" && TREE="$TREE" TINA4_DEBUG=true TINA4_LOG_LEVEL=NONE TINA4_OVERRIDE_CLIENT=true TINA4_AUTO_MIGRATE=false \
    TINA4_SECRET=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n') exec php -S 127.0.0.1:$port index.php >/dev/null 2>&1 ) &
for _ in $(seq 50); do curl -s -o /dev/null "http://127.0.0.1:$port/on" && break; sleep 0.1; done
echo "tree: $(git -C "$TREE" rev-parse --short HEAD), $(php -r 'echo PHP_VERSION;')"
for p in /on /off /doc-example; do
  printf '%-12s toolbar markers: %s   X-Debug-Toolbar header sent: %s\n' "$p" \
    "$(curl -s "http://127.0.0.1:$port$p" | grep -c 'tina4-dev-toolbar')" \
    "$(curl -s -D - -o /dev/null "http://127.0.0.1:$port$p" | grep -ci '^x-debug-toolbar')"
done
fuser -k -n tcp "$port" >/dev/null 2>&1; wait 2>/dev/null; rm -rf "$work"
