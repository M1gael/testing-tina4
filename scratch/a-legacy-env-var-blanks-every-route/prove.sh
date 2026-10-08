#!/usr/bin/env bash
# Usage: TREE=<tina4-php tree with vendor/> ./prove.sh
# A v3.11-era un-prefixed variable (DATABASE_URL, as a container platform sets it)
# under a real `php -S`: what does a client see, and where does the reason go?
set -u
here=$(cd "$(dirname "$0")" && pwd); : "${TREE:?set TREE to a tina4-php checkout with vendor/}"
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(git -C "$TREE" status --porcelain -- Tina4 | wc -l) modified framework files), $(php -r 'echo PHP_VERSION;')"
for debug in false true; do
  work=$(mktemp -d); cp "$here/app/index.php" "$work/"
  port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  ( cd "$work" && TREE="$TREE" TINA4_DEBUG=$debug TINA4_AUTO_MIGRATE=false TINA4_OVERRIDE_CLIENT=true \
      TINA4_SECRET=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n') DATABASE_URL=sqlite:///legacy.db \
      exec php -S 127.0.0.1:$port index.php >"$work/srv.log" 2>&1 ) &
  for _ in $(seq 50); do curl -s -o /dev/null "http://127.0.0.1:$port/" && break; sleep 0.1; done
  for path in / /health; do
    code=$(curl -s -o "$work/body" -w '%{http_code}' "http://127.0.0.1:$port$path")
    printf 'TINA4_DEBUG=%-5s GET %-8s %s %5s bytes  %s\n' $debug "$path" "$code" "$(wc -c <"$work/body")" "$(head -c 50 "$work/body" | tr '\n' ' ')"
  done
  printf 'TINA4_DEBUG=%-5s server output names the rename: %s\n' $debug "$(grep -c 'TINA4_DATABASE_URL' "$work/srv.log")"
  { fuser -k -n tcp "$port"; wait; } >/dev/null 2>&1; rm -rf "$work"
done
