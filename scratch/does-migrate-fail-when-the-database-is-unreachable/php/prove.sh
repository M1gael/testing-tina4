#!/usr/bin/env bash
# Does `tina4php migrate` exit non-zero when the database cannot be used?
#
#   ./prove.sh <tina4-php source tree with vendor/ installed>
#
# Runs the tree's own bin/tina4php from this project (a stock `tina4php init`
# app whose index.php boots the App), once per failure shape, and prints the
# exit status. PostgreSQL shapes run only when $PG (user:pass@host:port, a
# server with database "app") answers; otherwise they are skipped, not failed.
set -u
SRC=$(cd "${1:?usage: prove.sh <tina4-php tree>}" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
PG=${PG:-u:Zq9SecretPw@127.0.0.1:55433}
cd "$HERE"
export HOME=$(mktemp -d)
ln -sfn "$SRC/vendor" vendor
trap 'rm -rf vendor .env .env.local app.db logs .tina4 migrations/20260102000000_broken.sql' EXIT

fail=0
check() { # check <expect: zero|nonzero> <label> <url> [env...]
  local expect=$1 label=$2 url=$3; shift 3
  printf 'TINA4_DEBUG=true\nTINA4_DATABASE_URL=%s\n' "$url" > .env
  rm -f .env.local
  env "$@" timeout 60 php "$SRC/bin/tina4php" migrate > /dev/null 2>&1
  local rc=$?
  local ok=no
  { [ "$expect" = zero ] && [ $rc -eq 0 ]; } || { [ "$expect" = nonzero ] && [ $rc -ne 0 ] && [ $rc -ne 124 ]; } && ok=yes
  [ $ok = yes ] || fail=1
  printf '%-4s exit=%-3s %s\n' "$([ $ok = yes ] && echo ok || echo BAD)" "$rc" "$label"
}

pg_up=no
php -r '$c=@pg_connect("host=".$argv[1]." port=".$argv[2]." dbname=app user=".$argv[3]." password=".$argv[4]." connect_timeout=3"); exit($c?0:1);' \
  "$(echo "$PG" | sed 's/.*@//;s/:.*//')" "${PG##*:}" "${PG%%:*}" "$(echo "$PG" | sed 's/^[^:]*://;s/@.*//')" 2>/dev/null && pg_up=yes

rm -f app.db
check nonzero "sqlite: file cannot be opened"            "sqlite:////nonexistent-dir/x.db"
check nonzero "unsupported scheme"                       "nosuch://u:pw@127.0.0.1/app"
check nonzero "mysql: nothing listening (or no driver)"  "mysql://u:pw@127.0.0.1:59998/app"
check nonzero "sqlite: unopenable, TINA4_AUTO_MIGRATE=false" "sqlite:////nonexistent-dir/x.db" TINA4_AUTO_MIGRATE=false
if [ $pg_up = yes ]; then
  H=${PG#*@}
  check nonzero "postgres: nothing listening on the port" "postgres://${PG%@*}@127.0.0.1:59999/app"
  check nonzero "postgres: bad credentials"               "postgres://${PG%%:*}:wrong@$H/app"
  check nonzero "postgres: database does not exist"       "postgres://${PG%@*}@$H/nosuchdb"
  check nonzero "postgres: host does not resolve"         "postgres://${PG%@*}@nosuchhost.invalid:5432/app"
else
  echo "skip postgres shapes (no server at $PG)"
fi
check zero    "sqlite: reachable, migration applies"     "sqlite:///app.db"
echo "CREATE TABLE broken (" > migrations/20260102000000_broken.sql
check nonzero "sqlite: reachable, a migration errors"    "sqlite:///app.db"

echo
[ $fail = 0 ] && echo "VERDICT: migrate fails on every unusable database" || echo "VERDICT: DEFECT - migrate reported success for a database it could not use"
exit $fail
