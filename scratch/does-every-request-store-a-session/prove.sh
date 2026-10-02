#!/usr/bin/env bash
# Does every request create and store a session, and set a session cookie, in each port?
#
# Per port, against a source tree (TREE_PHP / TREE_PY / TREE_RB / TREE_ND, default the
# stock worktrees under ~/.cache/tina4-worktrees/fauth03-<port>-stock), file session backend
# (TINA4_SESSION_BACKEND=database: SQLite, rows counted instead of files):
#
#   anonymous: a client with NO cookie sends each request three times. Per cell the store is
#              counted before and after (session files; php also counts its native PHPSESSID
#              files) and every Set-Cookie name is collected.
#       static /hello.txt, 404 /nope, /health, /plain (never touches the session),
#       /read (reads a key), /write (sets a key); php also /native-read and /native-write
#       ($_SESSION). A cookie that names an id the store never issued is the last cell.
#   flows:     must keep working: a write resumes on the next request, login (regenerate then
#              set), a flash survives exactly one read; php: $_SESSION write resumes, and
#              session_regenerate_id(true) then write.
#
# Verdict per cell:
#   BUG     a request that writes nothing stored a session or set a session cookie
#   BROKEN  a request that writes stored nothing, set no cookie, or a flow did not resume
#   ok
#
#   ./prove.sh [php python ruby nodejs]
#   PHP_MODE=phps|serve|buffered   php under `php -S` (cli-server SAPI, PHP sends its own headers,
#                                  as under FPM/Apache; default), tina4's own server
#                                  (`php bin/tina4php serve`), or that server with
#                                  output_buffering on (what `serve` does once tina4-php#259 lands)
# Exit 0 all ok, 1 a BUG or BROKEN cell, 2 a server never came up.
set -u
B=$(cd "$(dirname "$0")" && pwd)
WT=${WT:-$(getent passwd "$(id -un)" | cut -d: -f6)/.cache/tina4-worktrees}   # the real HOME: suites run with HOME redirected
TREE_PHP=${TREE_PHP:-$WT/fauth03-php-stock} TREE_PY=${TREE_PY:-$WT/fauth03-py-stock}
TREE_RB=${TREE_RB:-$WT/fauth03-rb-stock} TREE_ND=${TREE_ND:-$WT/fauth03-nd-stock}
PHP_MODE=${PHP_MODE:-phps}
PORTS=("$@"); [ ${#PORTS[@]} -eq 0 ] && PORTS=(php python ruby nodejs)
W=$(mktemp -d); SRV=
cleanup() { [ -n "$SRV" ] && { kill "$SRV" 2>/dev/null; wait "$SRV" 2>/dev/null; }; rm -rf "$W"; }
trap cleanup EXIT
# A random base: python refuses a port that still holds TIME_WAIT sockets from the last run (f-cli-34).
PORT_BASE=${PORT_BASE:-$((18000 + RANDOM % 1500 * 4))}
status=0
held() { ss -ltnp "sport = :$1" 2>/dev/null | grep LISTEN; }

start() {  # lang port
  if held "$2" > /dev/null; then echo "$1: port $2 is already in use"; return 1; fi
  export TINA4_SECRET; TINA4_SECRET=$(head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')
  export TINA4_CSRF=true TINA4_DEBUG=false TINA4_AUTO_MIGRATE=false TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true PORT=$2
  export TINA4_SESSION_PATH=$W/$1-sessions TINA4_PHP_SESSION_PATH=$W/$1-native
  mkdir -p "$W/$1-native"
  [ "${TINA4_SESSION_BACKEND:-file}" = database ] && export TINA4_DATABASE_URL="sqlite:///$W/$1.db"
  case $1 in
    php) local srv=(serve --host 127.0.0.1 --port "$2" --no-browser --no-reload)
         case $PHP_MODE in
           phps)     (cd "$B/php" && TREE=$TREE_PHP exec php -S 127.0.0.1:$2 index.php) ;;
           serve)    (cd "$B/php" && TREE=$TREE_PHP exec php "$TREE_PHP/bin/tina4php" "${srv[@]}") ;;
           buffered) (cd "$B/php" && TREE=$TREE_PHP exec php -d output_buffering=4096 "$TREE_PHP/bin/tina4php" "${srv[@]}") ;;
         esac > "$W/$1.log" 2>&1 & ;;
    python) (cd "$B/python" && PYTHONPATH=$TREE_PY exec "$TREE_PY/.venv/bin/python" app.py) > "$W/$1.log" 2>&1 & ;;
    ruby)   (cd "$B/ruby" && BUNDLE_GEMFILE=$TREE_RB/Gemfile BUNDLE_PATH=${BUNDLE_PATH:-$WT/rb-bundle} RUBYLIB=$TREE_RB/lib exec bundle exec ruby app.rb) > "$W/$1.log" 2>&1 & ;;
    nodejs) sed "s|TREE_ND|$TREE_ND|g" "$B/nodejs/app.mts" > "$B/nodejs/.app-run.mts"
            (cd "$B/nodejs" && TINA4_PORT=$2 TINA4_HOST=127.0.0.1 exec node --import "file://$TREE_ND/node_modules/tsx/dist/loader.mjs" .app-run.mts) > "$W/$1.log" 2>&1 & ;;
  esac
  SRV=$!
  for i in $(seq 200); do
    kill -0 "$SRV" 2>/dev/null || break
    # the server may be a child of the exec'd process (php serve forks), so accept any listener
    if held "$2" > /dev/null; then curl -s -o /dev/null "http://127.0.0.1:$2/plain" && return 0; fi
    sleep 0.1
  done
  echo "$1: server never came up on port $2"; tail -5 "$W/$1.log"; return 1
}
stop() {  # port
  local pids; pids=$(held "$1" | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u)
  kill "$SRV" $pids 2>/dev/null; wait "$SRV" 2>/dev/null; SRV=
  for i in $(seq 50); do held "$1" > /dev/null || return 0; sleep 0.1; done
  echo "port $1 is still held after stopping the server"; exit 3
}

files() { find "$1" -type f 2>/dev/null | wc -l; }
store() {  # lang: session records held, files or (TINA4_SESSION_BACKEND=database) tina4_session rows
  if [ "${TINA4_SESSION_BACKEND:-file}" = database ]; then
    [ -f "$W/$1.db" ] && sqlite3 -cmd ".timeout 5000" "$W/$1.db" "select count(*) from tina4_session" 2>/dev/null || echo 0
  else files "$W/$1-sessions"; fi
}
cookies() { grep -i '^set-cookie:' "$1" | sed 's/^[Ss]et-[Cc]ookie: *//; s/=.*//' | sort -u | tr '\n' ' '; }

n=0
for lang in "${PORTS[@]}"; do
  port=$((PORT_BASE + n)); n=$((n + 1)); u="http://127.0.0.1:$port"
  label=$lang; [ "$lang" = php ] && label="php ($PHP_MODE)"
  start "$lang" "$port" || { status=2; [ -n "$SRV" ] && stop "$port"; continue; }
  # the boot probe above was itself an anonymous /plain: start the count from what it left
  echo "== $label, session code: $(curl -s "$u/where")"
  fw=$W/$lang-sessions nat=$W/$lang-native
  cells="static:/hello.txt 404:/nope health:/health plain:/plain read:/read write:/write"
  [ "$lang" = php ] && cells="$cells native-read:/native-read native-write:/native-write"
  cells="$cells unknown-cookie-read:/read"
  for cell in $cells; do
    name=${cell%%:*} path=${cell#*:}
    f0=$(store "$lang") n0=$(files "$nat"); : > "$W/h"
    for i in 1 2 3; do
      if [ "$name" = unknown-cookie-read ]; then
        curl -s -o /dev/null -D - -H "Cookie: tina4_session=$(head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n')" "$u$path" >> "$W/h"
      else curl -s -o /dev/null -D - "$u$path" >> "$W/h"; fi
    done
    code=$(grep -m1 '^HTTP' "$W/h" | awk '{print $2}')
    df=$(( $(store "$lang") - f0 )) dn=$(( $(files "$nat") - n0 )); ck=$(cookies "$W/h")
    case $name in
      write)        [ "$df" -eq 3 ] && [[ "$ck" == *tina4_session* ]] && v=ok || v="BROKEN: a write must store and set its cookie" ;;
      native-write) [ "$dn" -eq 3 ] && [[ "$ck" == *PHPSESSID* ]] && v=ok || v="BROKEN: a \$_SESSION write must store and set its cookie" ;;
      *)            [ "$df" -eq 0 ] && [ "$dn" -eq 0 ] && [ -z "$ck" ] && v=ok || v="BUG: stores or sets a cookie without a write" ;;
    esac
    [ "$name" = write ] && [ "$dn" -ne 0 ] && v="BUG: a tina4 session write also stored a native session"
    [ "$name" = native-write ] && [ "$df" -ne 0 ] && v="BUG: a \$_SESSION write also stored a tina4 session"
    if [ "$name" = native-write ] && [ "$PHP_MODE" = serve ] && [ "$dn" -eq 0 ] && [ "$df" -eq 0 ]; then
      v="not counted: under serve the native session never starts (f-auth-01)"
    fi
    [[ "$v" = ok || "$v" = "not counted"* ]] || status=1
    if [ "$lang" = php ]; then extra=", native files +$dn"; else extra=; fi
    printf '  %-20s %-4s x3: session records +%s%s, Set-Cookie: %-26s %s\n' "$name" "$code" "$df" "$extra" "${ck:-none}" "$v"
  done

  # flows that must keep working
  flow() {  # name expected  then the requests, each "path"; the last one's body must equal expected
    local name=$1 want=$2; shift 2; rm -f "$W/jar"; local body
    for p in "$@"; do body=$(curl -s -b "$W/jar" -c "$W/jar" "$u$p"); done
    if [ "$body" = "$want" ]; then v=ok; else v="BROKEN: wanted '$want'"; status=1; fi
    printf '  flow %-25s last body %-18s %s\n' "$name" "'$body'" "$v"
  }
  flow write-then-read user=alice /write /read
  flow login-then-read user=alice /login /read
  flow plain-then-login-then-read user=alice /plain /read /login /read
  flow flash-once flash=saved /flash-set /flash-get
  flow flash-gone flash=- /flash-set /flash-get /flash-get
  # a stored session's read-only request: no new record, and (except python, which re-sets its
  # cookie on every response: f-auth-07) no cookie
  rm -f "$W/jar"; curl -s -o /dev/null -b "$W/jar" -c "$W/jar" "$u/write"; f0=$(store "$lang")
  curl -s -o /dev/null -D "$W/h" -b "$W/jar" -c "$W/jar" "$u/read"
  printf '  flow %-25s session records +%s, Set-Cookie: %s\n' stored-read "$(( $(store "$lang") - f0 ))" "$(cookies "$W/h")"
  if [ "$lang" = php ]; then
    # under `serve` the native session never starts at all (f-auth-01, tina4-php#259): known, not this row
    native_flow() { if [ "$PHP_MODE" = serve ]; then local s=$status; flow "$@"; status=$s; echo "    (serve: f-auth-01, not counted)"; else flow "$@"; fi; }
    rm -f "$W/jar"; curl -s -o /dev/null -b "$W/jar" -c "$W/jar" "$u/native-write"; n0=$(files "$nat")
    curl -s -o /dev/null -D "$W/h" -b "$W/jar" -c "$W/jar" "$u/native-read"
    printf '  flow %-25s native files +%s, Set-Cookie: %s\n' native-stored-read "$(( $(files "$nat") - n0 ))" "$(cookies "$W/h")"
    n0=$(files "$nat")
    curl -s -o /dev/null -D "$W/h" -H "Cookie: PHPSESSID=$(head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n')" "$u/native-read"
    printf '  flow %-25s native files +%s, Set-Cookie: %s (PHP adopts an unknown id unless strict mode; not this row)\n' unknown-native-cookie "$(( $(files "$nat") - n0 ))" "$(cookies "$W/h")"
    # a logged-in user posts a form: form_token() binds to the native session id (Frond), and
    # CsrfMiddleware (TINA4_CSRF=true) refuses a post from any other id
    rm -f "$W/jar"; curl -s -o /dev/null -b "$W/jar" -c "$W/jar" "$u/login-token"
    tok=$(curl -s -b "$W/jar" -c "$W/jar" "$u/form")
    code=$(curl -s -o "$W/body" -w '%{http_code}' -b "$W/jar" -c "$W/jar" -d "formToken=$tok" "$u/submit")
    if [ "$code" = 200 ]; then v=ok; else v="BROKEN: wanted 200 'submitted'"; status=1; fi
    printf '  flow %-25s POST /submit %s %-26s %s\n' logged-in-form-post "$code" "'$(tr -d '\n ' < "$W/body" | head -c 24)'" "$v"
    native_flow native-write-then-read native=set /native-write /native-read
    native_flow native-login-then-read native=set /native-login /native-read
    native_flow native-plain-write-read native=set /plain /native-write /native-read
  fi
  stop "$port"
done
rm -f "$B/nodejs/.app-run.mts"
exit $status
