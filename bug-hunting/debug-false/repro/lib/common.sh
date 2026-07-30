#!/usr/bin/env bash
# Shared helpers for the probe scripts. Sourced, not executed.

REPRO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOCKAPP="$REPRO_DIR/mockapp"
LIB="$REPRO_DIR/lib"
RUN_DIR="$REPRO_DIR/.runs"
mkdir -p "$RUN_DIR"

c_reset=$'\033[0m'; c_dim=$'\033[2m'; c_bold=$'\033[1m'
c_red=$'\033[31m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_blue=$'\033[34m'

say()   { printf '%s\n' "$*"; }
head1() { printf '\n%s%s%s\n' "$c_bold" "$*" "$c_reset"; }
head2() { printf '\n%s%s%s\n' "$c_blue" "$*" "$c_reset"; }
dim()   { printf '%s%s%s\n' "$c_dim" "$*" "$c_reset"; }
pass()  { printf '  %sPASS%s  %s\n' "$c_green" "$c_reset" "$*"; }
fail()  { printf '  %sFAIL%s  %s\n' "$c_red" "$c_reset" "$*"; }
warn()  { printf '  %sNOTE%s  %s\n' "$c_yellow" "$c_reset" "$*"; }

need() {
  command -v "$1" >/dev/null 2>&1 || {
    say "Missing required command: $1"
    exit 2
  }
}

ensure_deps() {
  need curl
  need python3
  need tina4
  if [ ! -x "$MOCKAPP/.venv/bin/python" ]; then
    head2 "Installing mockapp dependencies (first run only)"
    need uv
    (cd "$MOCKAPP" && uv sync) || exit 2
  fi
}

# start_server <port> <debug-value> [logfile]
# Writes a scratch .env, points $BROWSER at the shim, launches `tina4 serve`,
# and waits for the port to answer. Exports SERVER_LOG and BROWSER_LOG.
start_server() {
  local port="$1" debug="$2"
  SERVER_LOG="${3:-$RUN_DIR/serve-$port.log}"
  BROWSER_LOG="$RUN_DIR/browser-$port.log"
  export BROWSER_LOG
  : > "$BROWSER_LOG"

  local envfile="$RUN_DIR/env-$port"
  {
    printf 'TINA4_DEBUG=%s\n' "$debug"
    printf 'TINA4_LOG_LEVEL=ALL\n'
    printf 'TINA4_DATABASE_URL=sqlite:///data/app.db\n'
  } > "$envfile"

  export TINA4_ENV_FILE="$envfile"
  export BROWSER="$LIB/fake-browser.sh"
  # Make sure a stale value from the caller's shell can't mask the finding.
  unset TINA4_NO_BROWSER

  ( cd "$MOCKAPP" && tina4 serve -p "$port" ) > "$SERVER_LOG" 2>&1 &
  SERVER_PID=$!

  local i
  for i in $(seq 1 90); do
    curl -sf -o /dev/null "http://localhost:$port/hello/one" && return 0
    # With TINA4_DEBUG=false there is no landing page, so also accept any answer.
    curl -s -o /dev/null --max-time 1 "http://localhost:$port/" && return 0
    sleep 0.5
  done
  return 1
}

stop_server() {
  local port="$1"
  pkill -f "tina4 serve -p $port" >/dev/null 2>&1
  [ -n "${SERVER_PID:-}" ] && kill "$SERVER_PID" >/dev/null 2>&1
  sleep 1
  unset TINA4_ENV_FILE BROWSER
  return 0
}

http_code() { curl -s -o /dev/null -w '%{http_code}' "$1"; }
page_title() { curl -s "$1" | grep -oE '<title>[^<]*</title>' | head -1; }

# The dev footer's own count. Scoped to the toolbar div so page prose can never
# be mistaken for it (that mistake cost an hour the first time round).
footer_route_count() {
  curl -s "$1" \
    | tr '>' '>\n' \
    | grep -A1 'id="tina4-dev-toolbar"' -m1 >/dev/null 2>&1
  curl -s "$1" \
    | python3 -c '
import re, sys
html = sys.stdin.read()
i = html.find("tina4-dev-toolbar")
if i == -1:
    print("")
    raise SystemExit
m = re.search(r">(\d+) routes<", html[i:])
print(m.group(1) if m else "")
'
}

dev_api_route_count() {
  curl -s "$1/__dev/api/routes" \
    | python3 -c 'import sys,json
try:
    print(json.load(sys.stdin).get("count",""))
except Exception:
    print("")'
}
