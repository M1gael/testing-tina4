#!/usr/bin/env bash
# Does `migrate` exit non-zero when the database cannot be used?
#
#   ./prove.sh php|python|ruby|nodejs <framework source tree>
#
# php runs php/prove.sh (a `tina4php init` project whose index.php boots the
# App). The others run the tree's own CLI in <port>/, a project holding one
# migration, once per failure shape. PostgreSQL shapes run only when $PG
# (user:pass@host:port, a server with database "app") answers.
#
# python needs a python with psycopg2 for the postgres shapes: set $PY.
set -u
PORT=${1:?usage: prove.sh php|python|ruby|nodejs <tree>}
SRC=$(cd "${2:?usage: prove.sh <port> <tree>}" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
[ "$PORT" = php ] && exec "$HERE/php/prove.sh" "$SRC"

PG=${PG:-u:Zq9SecretPw@127.0.0.1:55433}
cd "$HERE/$PORT" || exit 2
export HOME=$(mktemp -d)
trap 'rm -rf .env .env.local app.db app.db-shm app.db-wal data logs out.txt migrations/20260102000000_broken.sql' EXIT

case $PORT in
  python) CMD=("${PY:-python3}" -c 'import sys; from tina4_python.cli import main; sys.argv[0]="tina4python"; main()' migrate)
          export PYTHONPATH="$SRC" ;;
  ruby)   CMD=(ruby -I "$SRC/lib" "$SRC/exe/tina4ruby" migrate) ;;
  nodejs) CMD=("$SRC/node_modules/.bin/tsx" "$SRC/packages/cli/src/bin.ts" migrate) ;;
  *) echo "unknown port $PORT"; exit 2 ;;
esac

fail=0
check() { # check <expect: zero|nonzero> <label> <url-or-empty> [env...]
  local expect=$1 label=$2 url=$3; shift 3
  if [ -n "$url" ]; then printf 'TINA4_DATABASE_URL=%s\n' "$url" > .env; else rm -f .env; fi
  env TINA4_SECRET=prove-script-secret-0123456789abcdef "$@" timeout 60 "${CMD[@]}" > out.txt 2>&1
  local rc=$?
  local ok=no
  { [ "$expect" = zero ] && [ $rc -eq 0 ]; } || { [ "$expect" = nonzero ] && [ $rc -ne 0 ] && [ $rc -ne 124 ]; } && ok=yes
  [ $ok = yes ] || fail=1
  [ $rc -eq 124 ] && label="$label (TIMED OUT after 60s)"
  printf '%-4s exit=%-3s %s\n' "$([ $ok = yes ] && echo ok || echo BAD)" "$rc" "$label"
}

pg_up=no
command -v pg_isready > /dev/null && pg_isready -q -h "$(echo "$PG" | sed 's/.*@//;s/:.*//')" -p "${PG##*:}" && pg_up=yes

check nonzero "sqlite: file cannot be opened"           "sqlite:////nonexistent-dir/x.db"
check nonzero "unsupported scheme"                      "nosuch://u:pw@127.0.0.1/app"
check nonzero "mysql: nothing listening"                "mysql://u:pw@127.0.0.1:59998/app"
check nonzero "unsupported scheme, auto-migrate off"    "nosuch://u:pw@127.0.0.1/app" TINA4_AUTO_MIGRATE=false
if [ $pg_up = yes ]; then
  H=${PG#*@}
  check nonzero "postgres: nothing listening on the port" "postgres://${PG%@*}@127.0.0.1:59999/app"
  check nonzero "postgres: bad credentials"               "postgres://${PG%%:*}:wrong@$H/app"
  check nonzero "postgres: database does not exist"       "postgres://${PG%@*}@$H/nosuchdb"
  check nonzero "postgres: host does not resolve"         "postgres://${PG%@*}@nosuchhost.invalid:5432/app"
else
  echo "skip postgres shapes (no server at $PG)"
fi
case $PORT in
  ruby)   check nonzero "nothing configured"              "" ;;
  *)      echo "skip nothing-configured ($PORT defaults to a local SQLite file)" ;;
esac
check zero    "sqlite: reachable, migration applies"    "sqlite:///app.db"
echo "CREATE TABLE broken (" > migrations/20260102000000_broken.sql
check nonzero "sqlite: reachable, a migration errors"   "sqlite:///app.db"
rm -f out.txt

echo
[ $fail = 0 ] && echo "VERDICT: migrate fails on every unusable database" || echo "VERDICT: DEFECT - migrate reported success for a database it could not use"
exit $fail
