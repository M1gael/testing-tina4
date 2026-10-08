#!/usr/bin/env bash
# Does a refused TINA4_SECRET leak a stack trace and absolute paths, with no Tina4 error page?
#
# App::start() calls Auth::requireBootSecret() (App.php:539) BEFORE it installs
# Tina4's own exception handler (App.php:568), so the refusal is the one Tina4
# error that no Tina4 handler ever sees: not logged by Tina4, no Tina4 error
# page, and whatever status PHP's default output happens to leave behind.
#
#   ./prove.sh                 # stock tree
#   TREE=<tina4-php tree> ./prove.sh
#
# Cells run index.php under `php -S` -- the front-controller shape, same as
# PHP-FPM/Apache: index.php runs per request, so the refusal is raised per
# request and answers the client rather than the console.
#
#   /hello  a plain route; the refusal happens before it is ever reached
#   /boom   a route that throws AFTER the handler is installed -- the control
#           that shows what Tina4 does with a Throwable it does see
#
# Verdict BUG when a refusal reaches the client as a stack trace, or with a
# status other than 500, or is never written to Tina4's own log.
# Exit 0 no BUG cell, 1 a BUG cell, 2 a server never came up.
set -u
B=$(cd "$(dirname "$0")" && pwd)
WT=${WT:-$(getent passwd "$(id -un)" | cut -d: -f6)/.cache/tina4-worktrees}
TREE=${TREE:-$WT/gi147-stock-php}
PORT=${PORT:-$((18400 + RANDOM % 200))}
W=$(mktemp -d)
cleanup() { fuser -k "$PORT"/tcp >/dev/null 2>&1; rm -rf "$W"; }
trap cleanup EXIT
status=0
GOOD=$(head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')

start() {  # secret display_errors
  fuser -k "$PORT"/tcp >/dev/null 2>&1; sleep 0.2
  rm -rf "$W/logs" "$W/php-error.log"; mkdir -p "$W/logs"
  (cd "$B/app" && TREE=$TREE TINA4_SECRET=$1 TINA4_DEBUG=false TINA4_LOG_DIR=$W/logs \
     exec php -d display_errors="$2" -d log_errors=1 -d error_log="$W/php-error.log" \
          -S 127.0.0.1:"$PORT" index.php) > "$W/srv.log" 2>&1 &
  for _ in $(seq 40); do
    curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/hello" && return 0
    sleep 0.1
  done
  echo "server never came up"; cat "$W/srv.log"; return 2
}

probe() {  # label path expect_ok
  local label=$1 path=$2 expect=$3 code trace paths t4log phplog verdict
  code=$(curl -s -o "$W/body" -w '%{http_code}' --max-time 5 "http://127.0.0.1:$PORT$path")
  trace=no;  grep -q 'Stack trace' "$W/body" && trace=YES
  paths=no;  grep -qF "$TREE/Tina4/" "$W/body" && paths=YES
  # Tina4's logger writes to the process's own stdout/stderr unless TINA4_LOG_DIR
  # is picked up, so the server's captured output is where its lines land.
  t4log=no;  { grep -rqi 'TINA4_SECRET is' "$W/logs" 2>/dev/null \
               || grep -qi 'level.*ERROR.*TINA4_SECRET is' "$W/srv.log" 2>/dev/null; } && t4log=YES
  phplog=no; grep -qi 'TINA4_SECRET is' "$W/php-error.log" 2>/dev/null && phplog=YES
  verdict=ok
  if [ "$expect" = refusal ]; then
    { [ "$trace" = YES ] || [ "$code" != 500 ] || [ "$t4log" = no ]; } && verdict=BUG
  elif [ "$expect" = 200 ]; then
    [ "$code" = 200 ] || verdict=BROKEN
  elif [ "$expect" = handled ]; then
    { [ "$code" = 500 ] && [ "$trace" = no ]; } || verdict=BROKEN
  fi
  printf '%-40s status=%-4s trace=%-4s fwpaths=%-4s tina4-log=%-4s php-log=%-4s %s\n' \
    "$label" "$code" "$trace" "$paths" "$t4log" "$phplog" "$verdict"
  [ "$verdict" = ok ] || status=1
}

echo "tree: $TREE  ($(git -C "$TREE" describe --tags --always 2>/dev/null))"
echo "php:  $(php -r 'echo PHP_VERSION;')  front controller under php -S"
echo

start short On  || exit 2; probe "5-byte secret, display_errors=On"  /hello refusal
start short Off || exit 2; probe "5-byte secret, display_errors=Off" /hello refusal
start "$GOOD" On || exit 2
probe "32-byte secret, /hello   (control)"                           /hello 200
probe "32-byte secret, /boom    (handler IS installed)"              /boom  handled
fuser -k "$PORT"/tcp >/dev/null 2>&1; sleep 0.2

echo
echo "--- tina4 serve, its own server (not a front controller), 5-byte secret:"
SPORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
(cd "$B/app" && TREE=$TREE TINA4_SECRET=short TINA4_NO_BROWSER=true \
   timeout 20 php "$TREE/bin/tina4php" serve --host 127.0.0.1 --port "$SPORT" --no-browser --no-reload) \
   > "$W/serve.log" 2>&1
echo "rc=$?"; head -3 "$W/serve.log"

exit $status
