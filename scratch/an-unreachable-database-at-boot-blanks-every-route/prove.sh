#!/usr/bin/env bash
# Usage: TREE=<tina4-php tree with vendor/> ./prove.sh
# Boots the app under a real `php -S` with a database URL that points at a closed
# port, with and without a migrations/ folder, and prints what a client sees.
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${TREE:?set TREE to a tina4-php checkout with vendor/ installed}"
secret=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
cell() { # $1 label, $2 1=with migrations/
  work=$(mktemp -d); cp "$here/app/index.php" "$work/"
  [ "$2" = 1 ] && cp -r "$here/app/migrations" "$work/"
  port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  ( cd "$work" && TREE="$TREE" TINA4_SECRET="$secret" TINA4_DEBUG="${DEBUG:-false}" TINA4_AUTO_MIGRATE="${AUTO_MIGRATE:-true}" \
      TINA4_DATABASE_URL="${DBURL:-postgres://127.0.0.1:1/x}" \
      exec php -d display_errors=0 -S 127.0.0.1:$port index.php >"$work/srv.log" 2>&1 ) &
  for _ in $(seq 50); do curl -s -o /dev/null "http://127.0.0.1:$port/" && break; sleep 0.1; done
  for path in / /health; do
    out=$(curl -s -o "$work/body" -w '%{http_code}' "http://127.0.0.1:$port$path")
    printf '%-26s GET %-8s %s  %5s bytes  %s\n' "$1" "$path" "$out" "$(wc -c <"$work/body")" "$(head -c 60 "$work/body" | tr '\n' ' ')"
  done
  printf '%-26s log: auto-migration-failed=%s uncaught=%s\n' "$1" \
    "$(grep -c 'Startup auto-migration failed' "$work/srv.log")" "$(grep -c -i 'uncaught' "$work/srv.log")"
  fuser -k -n tcp "$port" >/dev/null 2>&1; wait 2>/dev/null; [ -n "${KEEPLOG:-}" ] && cp "$work/srv.log" "$KEEPLOG.$2"; rm -rf "$work"
}
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(git -C "$TREE" status --porcelain -- Tina4 | wc -l) modified framework files), $(php -r 'echo PHP_VERSION;')"
cell "migrations/ present" 1
cell "control: no migrations/" 0
