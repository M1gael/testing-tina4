#!/usr/bin/env bash
# Claims B and C — the dev footer.
#
#   B: there is no environment flag that suppresses the toolbar, and its close
#      button does not persist (unlike the dashboard overlay beside it).
#   C: the footer's route count and the /__dev dashboard's route count are
#      computed from the same table but disagree, permanently.
#
# B's "comes back on each click" half needs a human eye — the script prints the
# URL to click and what to look for.
set -u
. "$(dirname "$0")/lib/common.sh"
ensure_deps

PORT="${1:-7363}"

head1 "Claims B & C — the dev footer"

if ! start_server "$PORT" true; then
  fail "server never came up — see $SERVER_LOG"
  stop_server "$PORT"
  exit 1
fi
BASE="http://localhost:$PORT"
PAGE="$BASE/hello/one"

# ── B2: is there any flag that turns the toolbar off? ────────────────────────
head2 "B — looking for an off-switch"

PKG="$(cd "$MOCKAPP" && .venv/bin/python -c 'import tina4_python,os;print(os.path.dirname(tina4_python.__file__))')"
VER="$(cd "$MOCKAPP" && .venv/bin/python -c 'import tina4_python;print(tina4_python.__version__)')"
dim "tina4-python $VER at $PKG"

HITS="$(grep -rEl 'NO_TOOLBAR|HIDE_TOOLBAR|DEV_TOOLBAR|TINA4_TOOLBAR' "$PKG" --include='*.py' 2>/dev/null | wc -l)"
if [ "$HITS" -eq 0 ]; then
  fail "CONFIRMED: no TINA4_NO_TOOLBAR / TINA4_DEV_TOOLBAR style flag exists anywhere in the package."
else
  pass "Found $HITS file(s) mentioning a toolbar flag — this may be fixed in your version:"
  grep -rEn 'NO_TOOLBAR|HIDE_TOOLBAR|DEV_TOOLBAR|TINA4_TOOLBAR' "$PKG" --include='*.py' | head -5
fi

say ""
dim "  The neighbouring knobs all exist but none of them hides the footer:"
for v in TINA4_NO_RELOAD TINA4_NO_BROWSER TINA4_NO_AI_PORT TINA4_SUPPRESS; do
  n="$(grep -rl "$v" "$PKG" --include='*.py' 2>/dev/null | wc -l)"
  printf '    %-22s present in %s file(s)\n' "$v" "$n"
done

# Prove TINA4_NO_RELOAD is not it: toolbar still renders with it set.
say ""
dim "  Checking whether TINA4_NO_RELOAD suppresses the toolbar (it should not):"
BEFORE="$(curl -s "$PAGE" | grep -c 'id="tina4-dev-toolbar"')"
say "    toolbar div present on $PAGE : $BEFORE"

# ── B1: does the close button persist? ──────────────────────────────────────
head2 "B — does the footer's X button persist?"
TOOLBAR_HTML="$(curl -s "$PAGE" | python3 -c '
import sys
html = sys.stdin.read()
i = html.find("tina4-dev-toolbar")
print(html[i:i+6000] if i != -1 else "")
')"

CLOSE_LINE="$(printf '%s' "$TOOLBAR_HTML" | grep -o "onclick=\"this.parentElement.style.display='none'\"" | head -1)"
OVERLAY_KEY="$(printf '%s' "$TOOLBAR_HTML" | grep -o "tina4_dev_overlay_open" | head -1)"

if [ -n "$CLOSE_LINE" ]; then
  fail "CONFIRMED: the X is inline-only — ${CLOSE_LINE}"
  say "         No localStorage, no cookie. Every HTML response re-injects the bar."
else
  pass "The close button no longer looks inline-only — inspect it by hand."
fi
if [ -n "$OVERLAY_KEY" ]; then
  warn "And yet the dashboard overlay in the SAME bar persists via localStorage['$OVERLAY_KEY']."
  say "         One dismissal survives a reload, the other does not."
fi

# ── C: the two counts ───────────────────────────────────────────────────────
head2 "C — footer count vs dashboard count"
FOOT="$(footer_route_count "$PAGE")"
API="$(dev_api_route_count "$BASE")"
say "  dev footer (raw table)          : ${FOOT:-?}"
say "  /__dev/api/routes (filtered)    : ${API:-?}"

if [ -n "$FOOT" ] && [ -n "$API" ] && [ "$FOOT" != "$API" ]; then
  fail "CONFIRMED: two numbers for one router table, off by $((FOOT - API))."
elif [ -n "$FOOT" ] && [ "$FOOT" = "$API" ]; then
  pass "The counts agree on this run."
else
  warn "Could not read one of the counts — check $PAGE by hand."
fi

say ""
dim "  Which route is being dropped:"
curl -s "$BASE/__dev/api/routes" | python3 -c '
import sys, json
d = json.load(sys.stdin)
paths = {r["path"] for r in d["routes"]}
for p in ("/__health", "/health", "/swagger", "/__frond/live/{name}"):
    print(f"    {p:26} in dashboard list: {p in paths}")
'
say ""
dim "  Both health endpoints answer, but only one is listed:"
for p in /__health /health; do
  printf '    %-12s HTTP %s\n' "$p" "$(http_code "$BASE$p")"
done
cat <<'TXT'

    core/server.py
      _HEALTH_PATH = os.environ.get("TINA4_HEALTH_PATH", "/__health")
      Router.add("GET", _HEALTH_PATH, _health_handler)
      if _HEALTH_PATH != "/health":
          Router.add("GET", "/health", _health_handler)

    dev_admin/__init__.py
      internal_prefixes = ("/__dev", "/health", "/swagger")
      if path.startswith(internal_prefixes): continue

  "/__health".startswith("/health") is False, so the alias is hidden and the
  canonical route is listed as if it were one of yours. An app route named
  /healthz would be swallowed the same way.
TXT

# ── C: where the number comes from ──────────────────────────────────────────
head2 "C — where the count comes from"
curl -s "$BASE/__dev/api/routes" | python3 -c '
import sys, json, collections
d = json.load(sys.stdin)
by = collections.Counter(r["module"] for r in d["routes"])
for m, c in by.most_common():
    tag = "  <- AutoCRUD: 5 routes per auto_crud model" if m.startswith("tina4_python.crud") else ""
    print(f"    {c:4}  {m}{tag}")
'
cat <<'TXT'

  The count is honest. AutoCRUD generates five REST routes per model carrying
  auto_crud = True, so ~20 CRUD models alone reach ~100 routes. Delete a model
  from src/orm/models.py, restart, and the number drops by exactly 5.

  What is missing is any label or drill-down: the footer renders a bare
  "{route_count} routes" with no tooltip and no link.
TXT

# ── the human half of B ─────────────────────────────────────────────────────
head2 "B — the part you have to see for yourself"
cat <<TXT
  The server is still running. Open this and follow the page:

      $PAGE

    1. Dismiss the footer with its X, then click "page two". It is back.
    2. Open the footer's "Dashboard" link, then reload. The overlay stays open.
       The X you just used did not stick. Same bar, two behaviours.

  Press Enter here when you are done and the server will be shut down.
TXT
read -r _ || true
stop_server "$PORT"
say "Server stopped."
