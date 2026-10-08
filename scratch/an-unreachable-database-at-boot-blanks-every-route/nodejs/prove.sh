#!/usr/bin/env bash
# tina4-nodejs parity for tina4-php#276 case 2: an unreachable database at boot
# while migrations/ holds a .sql file. Does the server start, and what do
# GET /, /health and /hello answer?
#
#   TREE_ND=<tina4-nodejs source tree, node_modules installed> ./prove.sh
#
# TINA4_DATABASE_URL points at a closed port. Cells vary migrations/ (one
# SELECT 1 file, or none) and src/orm/ (present or not: Node runs its ORM init,
# and the auto-migrator with it, only when src/orm/ or src/models/ exists).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${TREE_ND:?set TREE_ND to a tina4-nodejs tree}"
NODEBIN=$(dirname "$(readlink -f "$(command -v node)")")
echo "tree: $(git -C "$TREE_ND" rev-parse --short HEAD) ($(git -C "$TREE_ND" describe --tags 2>/dev/null)); node $(node --version)"
freeport() { python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
show() { local r; r=$(curl -s -i --max-time 5 "http://127.0.0.1:$1$2" 2>/dev/null)
  printf '%-7s %s, %s bytes: %s\n' "$2" "$(printf '%s' "$r" | head -1 | tr -d '\r')" \
    "$(printf '%s' "$r" | sed '1,/^\r\?$/d' | wc -c)" "$(printf '%s' "$r" | sed '1,/^\r\?$/d' | head -c 70 | tr '\n' ' ')"; }
cell() {  # name migrations(yes|no) orm(yes|no)
  local RUN; RUN=$(mktemp -d); sed "s|TREE_ND|$TREE_ND|g" "$HERE/app.mts" > "$RUN/app.mts"
  [ "$2" = yes ] && mkdir -p "$RUN/migrations" && echo 'SELECT 1;' > "$RUN/migrations/000001_noop.sql"
  [ "$3" = yes ] && mkdir -p "$RUN/src/orm"
  local P; P=$(freeport); mkdir -p "$RUN/home"
  (cd "$RUN" && exec env -i HOME="$RUN/home" PATH="$NODEBIN:/usr/bin:/bin" TINA4_PORT="$P" TINA4_HOST=127.0.0.1 \
     TINA4_NO_AI_PORT=true TINA4_DEBUG=false TINA4_LOG_LEVEL=DEBUG TINA4_SECRET="$(python3 -c 'import secrets;print(secrets.token_hex(32))')" \
     TINA4_DATABASE_URL=postgres://127.0.0.1:1/x \
     node --import "file://$TREE_ND/node_modules/tsx/dist/loader.mjs" app.mts) > "$RUN/srv.log" 2>&1 &
  local pid=$! up=no
  for _ in $(seq 100); do
    curl -s -o /dev/null "http://127.0.0.1:$P/hello" 2>/dev/null && { up=yes; break; }
    kill -0 $pid 2>/dev/null || break; sleep 0.1
  done
  echo "== $1 (migrations/: $2, src/orm/: $3) listener: $up"
  if [ $up = yes ]; then show $P /; show $P /health; show $P /hello; fi
  echo "   console: $(grep -i -E 'migrat|ORM not available|database|ECONNREFUSED' "$RUN/srv.log" | grep -v -i 'warning.*sqlite is an experimental' | cut -c1-160 | head -4 | tr '\n' '|')"
  kill -0 $pid 2>/dev/null || { wait $pid; echo "   process exited $?"; }
  fuser -k "$P/tcp" >/dev/null 2>&1; kill $pid 2>/dev/null; wait $pid 2>/dev/null; rm -rf "$RUN"
}
cell migrations-and-orm-dir     yes yes
cell migrations-no-orm-dir      yes no
cell control-orm-dir-no-migrations no yes
cell control-neither            no  no
