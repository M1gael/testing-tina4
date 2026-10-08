#!/usr/bin/env bash
# tina4-ruby: with an unreachable database and a migrations/ folder holding a
# .sql file, does the app still start and answer its routes?
# Usage: TREE=<tina4-ruby checkout> BUNDLE_PATH=<installed bundle> ./prove.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${TREE:?set TREE to a tina4-ruby checkout}"
: "${BUNDLE_PATH:?set BUNDLE_PATH to the bundle directory}"
export BUNDLE_PATH BUNDLE_GEMFILE=$TREE/Gemfile
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(sed -n 's/.*VERSION = "\(.*\)"/\1/p' "$TREE/lib/tina4/version.rb"))"
good=$(ruby -rsecurerandom -e "puts SecureRandom.hex(32)")   # never written to disk

cell() { # label, with-migrations (yes/no)
  local work port pid
  work=$(mktemp -d); cp -r "$here/app/." "$work/"; mkdir -p "$work/home"
  [ "$2" = yes ] && { mkdir -p "$work/migrations"; echo 'SELECT 1;' > "$work/migrations/000001_noop.sql"; }
  port=$(ruby -rsocket -e 's=TCPServer.new("127.0.0.1",0); puts s.addr[1]; s.close')
  ( cd "$work" && HOME=$work/home TINA4_SECRET="$good" TINA4_NO_BROWSER=true \
      TINA4_DATABASE_URL=postgres://127.0.0.1:1/x TINA4_PORT=$port TINA4_HOST=127.0.0.1 \
      exec bundle exec ruby -I"$TREE/lib" app.rb >"$work/srv.log" 2>&1 ) &
  pid=$!
  for _ in $(seq 150); do
    kill -0 $pid 2>/dev/null || break
    curl -s -o /dev/null "http://127.0.0.1:$port/" 2>/dev/null && break
    sleep 0.1
  done
  if kill -0 $pid 2>/dev/null; then
    echo "[$1] server UP"
    for p in / /health /hello; do
      echo "    GET $p -> $(curl -s -o "$work/b" -w '%{http_code}' "http://127.0.0.1:$port$p") $(wc -c < "$work/b") bytes: $(head -c 90 "$work/b" | tr '\n' ' ')"
    done
    fuser -k -s $port/tcp 2>/dev/null; kill $pid 2>/dev/null; wait $pid 2>/dev/null
  else
    wait $pid; echo "[$1] process EXITED rc=$?; no listener"
  fi
  echo "    log: $(grep -h -o -E '(Database connect[a-z]*[^"]{0,90}|Startup auto-migration[^"]{0,110}|Applied [0-9]+ pending[^"]{0,40})' "$work/srv.log" "$work"/logs/*.log 2>/dev/null | sort -u | tr '\n' '|' | cut -c1-400)"
  rm -rf "$work"
}
cell "closed-port postgres, migrations/ with one .sql" yes
cell "closed-port postgres, no migrations/ (control) " no
