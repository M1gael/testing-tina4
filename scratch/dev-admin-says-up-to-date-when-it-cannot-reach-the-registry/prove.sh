#!/usr/bin/env bash
# Proves: the dev-admin version check answers "you are up to date" when it could not
# reach the package registry at all.
#
# Method: scaffold a project, pin a framework version that is deliberately OLD, then ask
# /__dev/api/version-check twice — once with the network up, once with https_proxy pointed
# at a dead port. The two answers should differ. They do not: offline, the endpoint returns
# HTTP 200 with latest == current, which the dev toolbar renders as a green
# "You are up to date!".
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/app"
OLD_VERSION="${OLD_VERSION:-3.13.125}"   # any released version that is not the latest

command -v tina4 >/dev/null || { echo "tina4 CLI not on PATH"; exit 2; }
command -v uv    >/dev/null || { echo "uv not on PATH"; exit 2; }

echo "== tina4 CLI: $(tina4 --version)"

if [ ! -d "$APP" ]; then
  echo "== scaffolding $APP"
  tina4 init python "$APP" > "$HERE/scaffold.log" 2>&1 </dev/null || { tail -5 "$HERE/scaffold.log"; exit 2; }
fi

( cd "$APP" && uv add "tina4-python==$OLD_VERSION" >/dev/null 2>&1 ) || { echo "could not pin $OLD_VERSION"; exit 2; }
installed=$( cd "$APP" && uv run python -c 'import tina4_python; print(tina4_python.__version__)' )
echo "== framework pinned at $installed (deliberately behind latest)"

ask() {  # $1 = label, rest = env for the server
  local label="$1"; shift
  ( cd "$APP" && env "$@" TINA4_DEBUG=1 uv run python app.py --managed > "$HERE/server-$label.log" 2>&1 & )
  local port=""
  for _ in $(seq 1 60); do
    port=$(grep -oE 'http://127\.0\.0\.1:[0-9]+' "$HERE/server-$label.log" 2>/dev/null | head -1 | sed 's/.*://')
    [ -n "$port" ] && break
    curl -s --max-time 1 http://127.0.0.1:1 >/dev/null 2>&1
  done
  [ -z "$port" ] && { echo "no port in server-$label.log"; return 1; }
  local body
  body=$(curl -sS --noproxy '*' --retry 30 --retry-connrefused --retry-delay 1 --max-time 45 \
           "http://127.0.0.1:$port/__dev/api/version-check")
  local pid
  pid=$(ss -lptn "sport = :$port" 2>/dev/null | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)
  [ -n "$pid" ] && kill "$pid" 2>/dev/null
  echo "$body"
}

echo "== asking with the network up"
online=$(ask online PATH="$PATH")
echo "   $online"

echo "== asking with the registry unreachable (https_proxy to a dead port)"
offline=$(ask offline PATH="$PATH" https_proxy=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9)
echo "   $offline"

echo
case "$online" in
  *"\"latest\":\"$installed\""*)
      echo "INCONCLUSIVE: $installed is the current latest release — pick an older OLD_VERSION."
      exit 2 ;;
esac

# With a local checkout given, prove the other side: the same two questions
# against the fix, where the offline answer has to report itself.
if [ -n "${FIXED_PATH:-}" ]; then
  echo
  echo "== installing the fix from $FIXED_PATH"
  ( cd "$APP" && uv add --editable "$FIXED_PATH" >/dev/null 2>&1 ) || { echo "could not install the fix"; exit 2; }
  fixed_online=$(ask fixed-online PATH="$PATH")
  fixed_offline=$(ask fixed-offline PATH="$PATH" https_proxy=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9)
  echo "   online:  $fixed_online"
  echo "   offline: $fixed_offline"
  echo
  case "$fixed_offline" in
    *'"latest": null'*|*'"latest":null'*)
        echo "FIXED: offline, the check reports that it did not happen." ;;
    *)  echo "NOT FIXED: offline answer still names a version: $fixed_offline"; exit 2 ;;
  esac
  case "$fixed_online" in
    *'"latest": null'*|*'"latest":null'*)
        echo "REGRESSION: the online check now fails too: $fixed_online"; exit 2 ;;
    *)  echo "FIXED: online, the check still reports a version."; exit 0 ;;
  esac
fi

case "$offline" in
  *"\"latest\":\"$installed\""*)
      echo "REPRODUCED: offline, the framework reports latest == current ($installed)."
      echo "The dev toolbar renders that as a green \"You are up to date!\" — the user is"
      echo "several releases behind and is told the opposite. The toolbar's own offline"
      echo "branch (\"Could not check for updates (offline?)\") never fires, because the"
      echo "server answered 200."
      exit 1 ;;
  *)  echo "NOT REPRODUCED: offline answer differs from current — the failure is being reported."
      exit 0 ;;
esac
