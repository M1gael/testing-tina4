#!/usr/bin/env bash
# Claim A — `tina4 serve` opens a browser window even when TINA4_DEBUG=false,
# and the page it opens onto is a 404.
#
# Runs the server twice, once with debug off and once with it on, and reports
# what the framework opened versus what was actually there to see.
set -u
. "$(dirname "$0")/lib/common.sh"
ensure_deps

PORT_OFF="${1:-7361}"
PORT_ON="${2:-7362}"

head1 "Claim A — browser auto-open vs TINA4_DEBUG"
dim "A shim on \$BROWSER records any window the framework opens. No framework code is touched."

run_one() {
  local port="$1" debug="$2"
  head2 "TINA4_DEBUG=$debug   (port $port)"
  if ! start_server "$port" "$debug"; then
    fail "server never came up — see $SERVER_LOG"
    stop_server "$port"
    return 1
  fi
  sleep 4   # the framework opens the browser on a 2s timer

  local title code opened
  title="$(page_title "http://localhost:$port/")"
  code="$(http_code "http://localhost:$port/")"
  opened="$(cat "$BROWSER_LOG")"

  say "  GET /              -> $code  ${title:-（no title)}"
  say "  GET /__dev         -> $(http_code "http://localhost:$port/__dev")"
  say "  browser opened     -> ${opened:-（nothing)}"
  stop_server "$port"

  if [ "$debug" = "false" ]; then
    if [ -n "$opened" ] && [ "$code" = "404" ]; then
      fail "CONFIRMED: a browser window was opened onto a 404 with debug off."
      return 0
    fi
    if [ -z "$opened" ]; then
      pass "No browser opened with debug off — this looks fixed in your version."
      return 0
    fi
    warn "A browser opened, but / did not return 404 (got $code). Read the output above."
  else
    [ -n "$opened" ] && pass "Browser opened onto a real landing page — correct behaviour."
  fi
  return 0
}

run_one "$PORT_OFF" false
run_one "$PORT_ON" true

head2 "What to make of it"
cat <<'TXT'
  The browser open is gated only on --no-browser / TINA4_NO_BROWSER. It is never
  gated on TINA4_DEBUG, while the landing page it lands on IS. So a production
  run pops a window onto "404 — Not Found".

    core/server.py
      _skip_browser = no_browser or os.environ.get("TINA4_NO_BROWSER", ...)
      if not _skip_browser:
          _open_browser(f"http://{display}:{port}")

  `is_debug` is already computed ~35 lines above that call. Adding it to the
  condition is the whole fix. Same applies to `tina4 serve --production`.
TXT
