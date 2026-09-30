#!/usr/bin/env bash
# The issue's three requests against a stock `tina4 init php` project under `tina4 serve`.
#
# prove.sh serves a hand-written app; this uses what the CLI actually scaffolds. It adds only
# the issue's two routes, then serves with the Rust CLI and drives the issue's curl sequence.
#
#   TINA4=<tina4 3.8.94> ./scaffold.sh                  the version `init` installs
#   TINA4=<tina4 3.8.94> VERSION=v3.x-dev ./scaffold.sh upstream's v3 branch head
#
# Exit 0: the session survived /regen. Exit 1: it did not. Exit 2: nothing measured.
set -u
TINA4=${TINA4:-tina4}
WORK=${WORK:-$HOME/.cache/tina4-worktrees/php-session-regen}
D=$WORK/scaffold${VERSION:+-$VERSION}
PORT=${PORT:-17962}
H=$WORK/home-init      # isolated HOME: keeps global tina4 skills and config out of the scaffold
mkdir -p "$H"

if [ ! -f "$D/index.php" ]; then
  rm -rf "$D"
  HOME=$H "$TINA4" init php "$D" < /dev/null > "$WORK/scaffold-init.log" 2>&1 \
    || { echo "SKIP: tina4 init php failed"; tail -5 "$WORK/scaffold-init.log"; exit 2; }
fi
if [ -n "${VERSION:-}" ]; then
  composer require --no-interaction --no-progress -q -W --working-dir="$D" "tina4stack/tina4php:$VERSION" \
    || { echo "SKIP: composer require $VERSION failed"; exit 2; }
fi
grep -q ob_start "$D/index.php" && echo "NOTE: this scaffold's index.php calls ob_start()"
cat > "$D/src/routes/regen.php" <<'PHP'
<?php
use Tina4\Router;

// The two routes from tina4-php issue 253, verbatim.
Router::post("/regen", function ($request, $response) {
    session_regenerate_id(true);   // e.g. login fixation defence
    $_SESSION["hit"] = ($_SESSION["hit"] ?? 0) + 1;
    return $response(["id" => session_id(), "hit" => $_SESSION["hit"]]);
})->noAuth();

Router::get("/whoami", function ($request, $response) {
    return $response(["id" => session_id(), "hit" => $_SESSION["hit"] ?? null]);
});
PHP

ss -ltn | grep -q ":$PORT " && { echo "SKIP: port $PORT is busy"; exit 2; }
log=$WORK/scaffold-serve.log
(cd "$D" && exec env HOME="$H" TINA4_NO_BROWSER=true "$TINA4" serve --host 127.0.0.1 --port "$PORT" --no-browser --no-reload) \
  > "$log" 2>&1 < /dev/null &
stop() {  # the CLI moves php into its own process group, so match on working directory
  for p in /proc/[0-9]*; do [ "$(readlink "$p/cwd" 2>/dev/null)" = "$D" ] && kill "${p#/proc/}" 2>/dev/null; done
  for _ in $(seq 1 40); do ss -ltn | grep -q ":$PORT " || return 0; sleep 0.25; done
  echo "WARN: port $PORT still bound"
}
up=0
for _ in $(seq 1 80); do curl -s -o /dev/null "http://127.0.0.1:$PORT/whoami" && { up=1; break; }; sleep 0.25; done
[ $up = 1 ] || { echo "SKIP: tina4 serve never answered on $PORT"; tail -5 "$log"; stop; exit 2; }

j=$WORK/scaffold-jar; rm -f "$j"*
ck() { grep -io '^set-cookie: PHPSESSID=[^;]\{0,6\}' "$1" | head -1 | cut -c13-; }
b1=$(curl -s -c "$j" -D "$j.h1" "http://127.0.0.1:$PORT/whoami")
c2=$(curl -s -b "$j" -c "$j" -D "$j.h2" -o "$j.b2" -w '%{http_code}' -X POST "http://127.0.0.1:$PORT/regen")
b3=$(curl -s -b "$j" -D "$j.h3" "http://127.0.0.1:$PORT/whoami")
stop

ver=$(php -r '$j=json_decode(file_get_contents($argv[1]),true); foreach(($j["packages"]??$j) as $p) if($p["name"]==="tina4stack/tina4php") echo $p["version"]," @ ",substr($p["dist"]["reference"]??"",0,8);' "$D/vendor/composer/installed.json")
echo "stock \`tina4 init php\` · tina4php $ver · $("$TINA4" --version) · PHP $(php -r 'echo PHP_VERSION;')"
echo "1 GET  /whoami  $b1  cookie:$(ck "$j.h1")"
echo "2 POST /regen   HTTP $c2 $( [ "$c2" = 200 ] && cat "$j.b2")  cookie:$(ck "$j.h2")"
echo "3 GET  /whoami  $b3  cookie:$(ck "$j.h3")"
err=$(grep -o 'session_regenerate_id(): [^{"]*' "$log" | head -1)
[ -n "$err" ] && echo "log: $err"

id2=$(php -r 'echo json_decode(file_get_contents($argv[1]),true)["id"]??"";' "$j.b2" 2>/dev/null)
id3=$(php -r 'echo json_decode($argv[1],true)["id"]??"";' "$b3" 2>/dev/null)
if [ "$c2" = 200 ] && [ -n "$id2" ] && [ "$id3" = "$id2" ]; then echo "verdict: kept"; exit 0; fi
echo "verdict: lost"; exit 1
