#!/usr/bin/env bash
# Does upstream's own regression fixture for tina4-php#253 still pass once its server prints
# a banner, as `tina4 serve` always does?
#
# The fix (f6fbd8a4) is tested by tests/SessionRegenerateNativeCookieTest.php, which boots
# tests/fixtures/session_regenerate_native_server.php with TINA4_SUPPRESS=true. This runs that
# fixture, unmodified apart from its autoload path, against the Packagist `v3.x-dev` install
# that prove.sh makes, once with the banner suppressed and once without, and drives the issue's
# three requests.
#
#   ./upstream-fixture.sh          needs ../../../tinaforks/tina4-php with origin/v3 fetched
#
# Exit 0: the fixture keeps the session through /regen only when the banner is suppressed.
# Exit 1: anything else. Exit 2: nothing measured.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=${REPO:-$HERE/../../../tinaforks/tina4-php}
WORK=${WORK:-$HOME/.cache/tina4-worktrees/php-session-regen}
V=$WORK/v3.x-dev
F=$V/upfix
[ -f "$V/vendor/autoload.php" ] || { echo "SKIP: run VERSIONS=v3.x-dev ./prove.sh first"; exit 2; }
ref=$(php -r '$j=json_decode(file_get_contents($argv[1]),true); foreach(($j["packages"]??$j) as $p) if($p["name"]==="tina4stack/tina4php") echo $p["dist"]["reference"];' "$V/vendor/composer/installed.json")
rm -rf "$F"; mkdir -p "$F/tmp"
git -C "$REPO" show "$ref:tests/fixtures/session_regenerate_native_server.php" 2>/dev/null \
  | sed "s#__DIR__ . '/../../vendor/autoload.php'#__DIR__ . '/../vendor/autoload.php'#" > "$F/server.php"
grep -q "/../vendor/autoload.php" "$F/server.php" || { echo "SKIP: fixture not found at $ref"; exit 2; }
secret=$(php -r 'echo bin2hex(random_bytes(32));')
echo "tina4php v3.x-dev @ ${ref:0:8} · PHP $(php -r 'echo PHP_VERSION;') · fixture from the same commit"

cookie() { grep -io '^set-cookie: PHPSESSID=[^;]\{0,6\}' "$1" | head -1 | cut -c13-; }
status=0
for sup in true false; do
  port=$((17990 + ${#sup}))
  env -C "$V" TMPDIR="$F/tmp" TINA4_OVERRIDE_CLIENT=true TINA4_SUPPRESS=$sup TINA4_AUTO_MIGRATE=false \
    TINA4_DEBUG=false TINA4_NO_BROWSER=true TINA4_SECRET="$secret" \
    php "$F/server.php" "$port" > "$F/log-$sup.txt" 2>&1 < /dev/null &
  pid=$!
  up=0
  for _ in $(seq 1 40); do curl -s -o /dev/null "http://127.0.0.1:$port/whoami" && { up=1; break; }; sleep 0.25; done
  if [ $up = 0 ]; then echo "SKIP: fixture never answered on $port"; kill $pid 2>/dev/null; exit 2; fi
  jar=$F/jar-$sup
  b1=$(curl -s -c "$jar" -D "$F/h1" "http://127.0.0.1:$port/whoami")
  code=$(curl -s -b "$jar" -c "$jar" -D "$F/h2" -o "$F/b2" -w '%{http_code}' -X POST "http://127.0.0.1:$port/regen")
  b3=$(curl -s -b "$jar" -D "$F/h3" "http://127.0.0.1:$port/whoami")
  b2=$( [ "$code" = 200 ] && cat "$F/b2" || echo "(HTML error page)")
  echo "TINA4_SUPPRESS=$sup"
  echo "  1 GET /whoami   $b1  set:$(cookie "$F/h1")"
  echo "  2 POST /regen   HTTP $code $b2  set:$(cookie "$F/h2")"
  echo "  3 GET /whoami   $b3  set:$(cookie "$F/h3")"
  err=$(grep -o 'session_regenerate_id(): [^{"]*' "$F/log-$sup.txt" | head -1)
  [ -n "$err" ] && echo "  log: $err"
  id2=$(php -r 'echo json_decode(file_get_contents($argv[1]),true)["id"]??"";' "$F/b2" 2>/dev/null)
  id3=$(php -r 'echo json_decode($argv[1],true)["id"]??"";' "$b3" 2>/dev/null)
  kept=0
  [ "$code" = 200 ] && [ -n "$id2" ] && [ "$id3" = "$id2" ] && kept=1
  if [ $sup = true ] && [ $kept = 0 ]; then status=1; fi
  if [ $sup = false ] && [ $kept = 1 ]; then status=1; fi
  kill $pid 2>/dev/null; wait $pid 2>/dev/null
done
for _ in $(seq 1 20); do ss -ltn | grep -qE ':1799[45] ' || break; sleep 0.25; done
ss -ltn | grep -qE ':1799[45] ' && echo "WARN: a fixture port is still bound"
[ $status = 0 ] && echo "verdict: kept only with the banner suppressed" || echo "verdict: unexpected"
exit $status
