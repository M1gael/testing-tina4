#!/usr/bin/env bash
# tina4-python: does the app still serve when the database is unreachable at boot
# and migrations/ holds a .sql file? (The auto-migrator's docstring: "A failure here
# is logged LOUD and the service STILL starts".)
# Usage: TREE=<tina4-python checkout with .venv and psycopg2> ./prove.sh
set -u
TREE=${TREE:?set TREE to a tina4-python checkout with a .venv}
PY=${PY:-$TREE/.venv/bin/python}
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d); export HOME=$work/home; mkdir -p "$HOME"; pid=
trap '[ -n "$pid" ] && kill $pid 2>/dev/null; rm -rf "$work"' EXIT
cp "$here/app.py" "$work/"
echo "tree: $(git -C "$TREE" rev-parse --short HEAD), $(grep -m1 '^version' "$TREE/pyproject.toml"), $($PY -V), psycopg2 $($PY -c 'import psycopg2;print(psycopg2.__version__.split()[0])' 2>&1)"
port=$($PY -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
secret=$(head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')

cell() { local label=$1; shift
  (cd "$work" && exec env TINA4_SECRET=$secret TINA4_DATABASE_URL=postgres://127.0.0.1:1/x "$@" \
     TINA4_PORT=$port TINA4_NO_AI_PORT=true "$PY" app.py --managed) >"$work/srv.log" 2>&1 & pid=$!
  for _ in $(seq 75); do curl -s -o /dev/null "http://127.0.0.1:$port/hello" && break; kill -0 $pid 2>/dev/null || break; sleep 0.2; done
  echo "== $label"
  for p in /hello /health /; do
    local out; out=$(curl -s --max-time 5 -o "$work/body" -w '%{http_code}' "http://127.0.0.1:$port$p") || out="no answer"
    echo "   GET $p: $out, $(wc -c <"$work/body" 2>/dev/null || echo 0) bytes$( [ "$p" = /health ] && printf ', %s' "$(head -c 120 "$work/body" 2>/dev/null)")"
    rm -f "$work/body"
  done
  if kill -0 $pid 2>/dev/null; then kill $pid; wait $pid 2>/dev/null; else echo "   server exited"; fi; pid=
  echo "   log lines about the database or migrations:"
  grep -i -E 'migrat|database|connect' "$work/srv.log" | head -4 | cut -c1-220 | sed 's/^/     | /'
}
rm -rf "$work/migrations"; mkdir -p "$work/migrations"; echo 'SELECT 1;' >"$work/migrations/000001_noop.sql"
cell "unreachable database, migrations/ holds 000001_noop.sql (default log level)"
cell "same, TINA4_LOG_LEVEL=DEBUG" TINA4_LOG_LEVEL=DEBUG
rm -rf "$work/migrations"
cell "control: unreachable database, no migrations/ folder"
