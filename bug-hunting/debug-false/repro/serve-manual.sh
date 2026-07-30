#!/usr/bin/env bash
# Serve the mock app for HAND verification — no probes, no assertions, no
# teardown. Prints what to look at, then hands the terminal to `tina4 serve`.
#
#   ./serve-manual.sh              # TINA4_DEBUG=true  on port 7400
#   ./serve-manual.sh false        # TINA4_DEBUG=false on port 7400
#   ./serve-manual.sh true 7411    # pick a port
#   ./serve-manual.sh false 7400 shim
#
# Unlike the probe scripts this lets your REAL browser open, because claim A is
# "a browser window appears on a 404" and you have to watch that happen. Pass a
# third argument of `shim` to route the open through lib/fake-browser.sh instead
# and just print the URL it wanted.
#
# Ctrl-C stops the server.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib/common.sh"

DEBUG="${1:-true}"
PORT="${2:-7400}"
MODE="${3:-real}"

case "$DEBUG" in
  true|false) ;;
  *) say "First argument must be 'true' or 'false' (got '$DEBUG')."; exit 2 ;;
esac

ensure_deps

ENVFILE="$RUN_DIR/env-manual-$PORT"
{
  printf 'TINA4_DEBUG=%s\n' "$DEBUG"
  printf 'TINA4_LOG_LEVEL=ALL\n'
  printf 'TINA4_DATABASE_URL=sqlite:///data/app.db\n'
} > "$ENVFILE"
export TINA4_ENV_FILE="$ENVFILE"

# A stale TINA4_NO_BROWSER in your shell would mask claim A entirely.
unset TINA4_NO_BROWSER

if [ "$MODE" = "shim" ]; then
  BROWSER_LOG="$RUN_DIR/browser-manual-$PORT.log"
  export BROWSER_LOG
  : > "$BROWSER_LOG"
  export BROWSER="$HERE/lib/fake-browser.sh"
fi

BASE="http://localhost:$PORT"

head1 "Mock app — TINA4_DEBUG=$DEBUG on port $PORT"
say "  tina4 CLI      : $(tina4 --version 2>/dev/null | head -1)"
say "  tina4-python   : $(cd "$MOCKAPP" && uv run python -c 'import tina4_python;print(tina4_python.__version__)' 2>/dev/null | tail -1)"
say "  env file       : $ENVFILE"
if [ "$MODE" = "shim" ]; then
  say "  browser        : shimmed, opens are logged to $BROWSER_LOG"
else
  say "  browser        : real — a window will open by itself, that is the point"
fi

if [ "$DEBUG" = "true" ]; then
  head2 "What to check with debug ON"
  say "  B1  $BASE/hello/one"
  say "      Dismiss the footer with its x, then click 'page two'. Footer returns."
  say "      Then open the footer's 'Dashboard' link and RELOAD — the overlay"
  say "      stays open. Same bar, only one of the two remembers anything."
  say ""
  say "  B2  No env flag hides the footer. Nothing to try; the flag does not exist."
  say "      Only TINA4_DEBUG=false hides it, and that removes the error overlay,"
  say "      live reload, /__dev and Swagger with it."
  say ""
  say "  C   Footer count vs $BASE/__dev/api/routes count."
  say "      The page prints both and diffs them for you. Expect a gap of 1."
  say "      The missing entry is GET /health."
  say ""
  say "  C   Comment out a model in mockapp/src/orm/models.py and restart:"
  say "      the count drops by exactly 5."
else
  head2 "What to check with debug OFF"
  say "  A   Watch for a browser window opening on its own, at $BASE"
  say "      That URL is a 404 — there is no landing page with debug off."
  say "      Nothing asked for that window. That is the whole finding."
  say ""
  say "  A   $BASE/          -> 404"
  say "      $BASE/__dev     -> 404"
  say "      $BASE/hello/one -> 200, and no footer on it"
  say ""
  say "  A   Same thing happens with --production. Try:"
  say "        cd mockapp && tina4 serve -p $PORT --production"
  say "      Suppressing it needs --no-browser or TINA4_NO_BROWSER=true."
fi

head2 "Serving — Ctrl-C to stop"
say ""

cd "$MOCKAPP" || exit 2
exec tina4 serve -p "$PORT"
