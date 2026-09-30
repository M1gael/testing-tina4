#!/usr/bin/env bash
# Does tina4-php lose the native session after session_regenerate_id() under
# `tina4 serve`? (tina4-php issue 253)
#
# Installs each framework version from Packagist into $WORK/<version> (reused if
# present), serves app/ under each server mode, and drives the issue's three
# requests with a cookie jar:
#   1. GET  /whoami   establish a session
#   2. POST /regen    session_regenerate_id(true); $_SESSION["hit"]++
#   3. GET  /whoami   does the session come back?
# Controls, same flow: POST /set (no regenerate) and POST /regen-keep
# (session_regenerate_id(false)). Then the same for Tina4's own session
# ($request->session, tina4_session cookie): POST /t-set, and POST /t-regen
# (Session::regenerate()) after a /t-set.
#
#   ./prove.sh
#   VERSIONS=3.13.141 MODES="cli phps" ./prove.sh
#   VERSIONS=v3.x-dev ./prove.sh        upstream's v3 branch head, as Packagist names it
#
# Modes: cli      `tina4 serve` (the Rust CLI; TINA4=<path> overrides `tina4` on PATH)
#        direct   `php vendor/bin/tina4php serve` (the same socket server, no CLI;
#                 needs TINA4_OVERRIDE_CLIENT=true)
#        serial   direct with TINA4_SERVE_FORK=false (no fork per request; Windows
#                 always runs this way)
#        buffered direct with `php -d output_buffering=4096`, so the server's own
#                 startup output does not mark headers as sent (an instrument,
#                 not a supported setup: the CLI SAPI hardcodes output_buffering=0)
#        phps     `php -S` (the cli-server SAPI)
#
# PRESTART=1 makes app/index.php call session_start() itself before the router runs.
# OB_APP=1 makes it call ob_start() and leave the buffer open, so the serve command's
# startup output lands in that buffer and headers are not marked sent.
#
# Exit 0: every stock socket-server cell (cli, direct, serial) kept the native
# session per client through /set and /regen. Exit 1: at least one did not (lost
# it, or served one client's session to another). The buffered and phps cells are
# instruments and controls; they never set the exit status. Exit 2: Packagist
# unreachable or a server never came up; nothing was measured.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
VERSIONS=${VERSIONS:-3.13.138 3.13.139 3.13.141}
MODES=${MODES:-cli direct serial buffered phps}
WORK=${WORK:-$HOME/.cache/tina4-worktrees/php-session-regen}
TINA4=${TINA4:-tina4}
SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
tmp=$(mktemp -d)
LOGS=${LOGS:-$WORK/logs}; mkdir -p "$LOGS"
port=17870
status=0 cells=0 bad=0
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/home"

install() {  # version -> project dir
  local p="$WORK/$1"
  if [ "$(cd "$p" 2>/dev/null && composer show tina4stack/tina4php 2>/dev/null | awk '/^versions/{print $4}')" != "$1" ]; then
    rm -rf "$p"; mkdir -p "$p"
    printf '{"require": {"tina4stack/tina4php": "%s"}, "config": {"preferred-install": "dist"}}\n' "$1" > "$p/composer.json"
    (cd "$p" && composer install --no-interaction --no-progress -q) || { echo "SKIP: composer install $1 failed"; exit 2; }
  fi
  cp -r "$HERE/app/." "$p/"
  rm -rf "$p/data/sessions-php" "$p/data/sessions" "$p/data/sessions-app"
  echo "$p"
}

start() {  # mode dir port log
  local mode=$1 dir=$2 p=$3 log=$4
  local base=(env TINA4_SECRET="$SECRET" TINA4_DEBUG="${DEBUG:-true}" TINA4_NO_BROWSER=true)
  local srv=(serve --host 127.0.0.1 --port "$p" --no-browser --no-reload)
  case $mode in
    cli)    (cd "$dir" && exec "${base[@]}" HOME="$tmp/home" "$TINA4" "${srv[@]}") ;;
    direct) (cd "$dir" && exec "${base[@]}" TINA4_OVERRIDE_CLIENT=true php vendor/bin/tina4php "${srv[@]}") ;;
    serial) (cd "$dir" && exec "${base[@]}" TINA4_OVERRIDE_CLIENT=true TINA4_SERVE_FORK=false php vendor/bin/tina4php "${srv[@]}") ;;
    buffered) (cd "$dir" && exec "${base[@]}" TINA4_OVERRIDE_CLIENT=true php -d output_buffering=4096 vendor/bin/tina4php "${srv[@]}") ;;
    phps)   (cd "$dir" && exec "${base[@]}" php -S "127.0.0.1:$p" -t . index.php) ;;
  esac >"$log" 2>&1 </dev/null &
}

stop() {  # dir port: every process whose cwd is the project dir is ours
  local p pids=""
  for p in /proc/[0-9]*; do [ "$(readlink "$p/cwd" 2>/dev/null)" = "$1" ] && pids="$pids ${p#/proc/}"; done
  [ -n "$pids" ] && { kill $pids 2>/dev/null; sleep 0.5; kill -9 $pids 2>/dev/null; }
  for _ in $(seq 20); do ss -ltn | grep -q "127.0.0.1:$2 " || return 0; sleep 0.25; done
  echo "WARN: port $2 still bound after stop"
}

sid() { grep -i "^set-cookie: $2=" "$1" | sed "s/.*$2=\([^;]*\).*/\1/" | cut -c1-6 | paste -sd, - | sed 's/^$/-/'; }
field() { python3 -c 'import json,sys
try: d=json.loads(sys.argv[1])
except Exception: print("?"); sys.exit()
v=d.get(sys.argv[2]); print("null" if v is None else (str(v)[:6] if sys.argv[2]=="id" else v))' "$1" "$2"; }

flow() {  # port route [first] [who] [cookie]: step 1 = first, 2 = POST route, 3 = GET who
  local u="http://127.0.0.1:$1" route=$2 first=${3:-GET:/whoami} who=${4:-/whoami} ck=${5:-PHPSESSID}
  local jar="$tmp/jar" b1 b2 b3
  rm -f "$jar"
  b1=$(curl -s -c "$jar" -D "$tmp/h1" -X "${first%%:*}" "$u${first#*:}")
  b2=$(curl -s -b "$jar" -c "$jar" -D "$tmp/h2" -X POST "$u$route")
  b3=$(curl -s -b "$jar" -c "$jar" -D "$tmp/h3" "$u$who")
  local verdict=lost shared=""
  [ "$(field "$b3" hit)" = "$(field "$b2" hit)" ] && [ "$(field "$b3" id)" = "$(field "$b2" id)" ] && verdict=kept
  # A fresh cookie jar must start empty; a hit here was written by an earlier client.
  case "$(field "$b1" hit)" in null|\?) ;; *) [ "${first%%:*}" = GET ] && shared="  SHARED: fresh client saw hit=$(field "$b1" hit)";; esac
  printf '%-11s 1 %s/%s set:%s | 2 %s/%s set:%s | 3 %s/%s set:%s  %s\n' "$route" \
    "$(field "$b1" id)" "$(field "$b1" hit)" "$(sid "$tmp/h1" "$ck")" \
    "$(field "$b2" id)" "$(field "$b2" hit)" "$(sid "$tmp/h2" "$ck")" \
    "$(field "$b3" id)" "$(field "$b3" hit)" "$(sid "$tmp/h3" "$ck")" "$verdict$shared"
  [ $verdict = kept ] && [ -z "$shared" ]
}

command -v "$TINA4" >/dev/null || { case " $MODES " in *" cli "*) echo "SKIP: no tina4 CLI (set TINA4=)"; exit 2;; esac; }
echo "CLI: $("$TINA4" --version 2>/dev/null) · $(php -r 'echo "PHP ", PHP_VERSION;') · debug=${DEBUG:-true} · prestart=${PRESTART:-0} · ob_app=${OB_APP:-0}"
for v in $VERSIONS; do
  dir=$(install "$v") || exit 2
  for m in $MODES; do
    port=$((port+1)); log="$LOGS/$v-$m.log"
    start "$m" "$dir" "$port" "$log"
    up=0; for _ in $(seq 60); do [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/probe")" = 200 ] && { up=1; break; }; sleep 0.5; done
    if [ $up = 0 ]; then echo "SKIP: $v $m never answered on $port"; tail -5 "$log"; stop "$dir" "$port"; exit 2; fi
    probe=$(curl -s "http://127.0.0.1:$port/probe")
    echo "== $v $m  probe: $probe"
    ok=1
    flow "$port" /set || ok=0
    flow "$port" /regen || ok=0
    case $m in cli|direct|serial) cells=$((cells+1)); [ $ok = 1 ] || { bad=$((bad+1)); status=1; };; esac
    flow "$port" /regen-keep || true
    flow "$port" /t-set GET:/t-who /t-who tina4_session || true
    flow "$port" /t-regen POST:/t-set /t-who tina4_session || true
    echo "   session files: native $(ls "$dir/data/sessions-php" 2>/dev/null | wc -l), app-started $(ls "$dir/data/sessions-app" 2>/dev/null | wc -l)"
    stop "$dir" "$port"
    rm -rf "$dir/data/sessions-php" "$dir/data/sessions" "$dir/data/sessions-app"
  done
done
echo "native \$_SESSION not kept per client (/set or /regen) in $bad of $cells stock socket-server cells"
exit $status
