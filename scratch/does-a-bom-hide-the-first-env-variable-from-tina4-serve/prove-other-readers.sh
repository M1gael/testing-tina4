#!/usr/bin/env bash
# f-cli-25, the CLI's other .env readers. Each case runs in a fresh temp project
# with a hermetic env (no real PATH, no real HOME). Prints one line per reader.
#
#   BIN=/path/to/tina4 ./prove-other-readers.sh
#
# Exit 0 = every reader mishandles a BOM. Exit 1 = at least one reads it correctly.
set -u
BIN="${BIN:-$HOME/.cache/tina4-update-probe/a/bin/tina4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BOM=$'\xef\xbb\xbf'
echo "# binary: $BIN ($("$BIN" --version 2>&1 | head -1))"
bad=0; good=0
mkp() { d=$(mktemp -d); printf 'tina4_python\n' > "$d/requirements.txt"; echo "$d"; }
hx() { env -i HOME="$1/.home" PATH="$1/.bin:/usr/bin:/bin" TERM=dumb "${@:2}"; }

# 1. tina4 env --sync: reads .env, adds scanned vars that are missing, writes back.
d=$(mkp); printf '%sTINA4_DEBUG=true\nOTHER=1\n' "$BOM" > "$d/.env"
printf 'import os\nos.environ.get("TINA4_DEBUG")\n' > "$d/app.py"
(cd "$d" && hx "$d" "$BIN" env --sync > "$d/sync.log" 2>&1)
n=$(grep -c 'TINA4_DEBUG=' "$d/.env"); v=$(grep -a '^TINA4_DEBUG=' "$d/.env" | head -1)
cp "$d/.env" "$HERE/evidence/env-sync.after.env"
if [ "$n" -gt 1 ] || [ "$v" != "TINA4_DEBUG=true" ]; then echo "  BOM-BROKEN env --sync: $n TINA4_DEBUG lines, clean one reads '${v:-<none>}'"; bad=$((bad+1))
else echo "  ok         env --sync: TINA4_DEBUG=true kept, once"; good=$((good+1)); fi
rm -rf "$d"

# 2. tina4 env --migrate --yes: renames legacy keys.
d=$(mkp); printf '%sDATABASE_URL=sqlite:///x.db\nSECRET=s\n' "$BOM" > "$d/.env"
(cd "$d" && hx "$d" "$BIN" env --migrate --yes > "$d/mig.log" 2>&1)
cp "$d/.env" "$HERE/evidence/env-migrate.after.env"
if grep -aq 'TINA4_DATABASE_URL=' "$d/.env"; then echo "  ok         env --migrate: DATABASE_URL renamed"; good=$((good+1))
else echo "  BOM-BROKEN env --migrate: first key DATABASE_URL not renamed (SECRET: $(grep -ac '^TINA4_SECRET=' "$d/.env") renamed)"; bad=$((bad+1)); fi
rm -rf "$d"

# 3. TINA4_NO_BROWSER from .env: serve must not open a browser. A fake xdg-open
#    on PATH records whether it was called. The stand-in child exits at once.
d=$(mkp); mkdir -p "$d/.bin"; printf '%sTINA4_NO_BROWSER=true\n' "$BOM" > "$d/.env"
printf '#!/bin/sh\necho "$@" >> "%s/opened"\n' "$d" > "$d/.bin/xdg-open"; chmod +x "$d/.bin/xdg-open"
printf 'import time; time.sleep(4)\n' > "$d/app.py"
(cd "$d" && hx "$d" timeout 12 "$BIN" serve > "$d/serve.log" 2>&1)
if [ -s "$d/opened" ]; then echo "  BOM-BROKEN TINA4_NO_BROWSER: browser opened ($(cat "$d/opened"))"; bad=$((bad+1))
else echo "  ok         TINA4_NO_BROWSER: no browser"; good=$((good+1)); fi
cp "$d/serve.log" "$HERE/evidence/no-browser.serve.log"
# Control for 3: without a BOM the same .env must suppress the browser, or the
# probe cannot tell the two apart.
rm -f "$d/opened"; printf 'TINA4_NO_BROWSER=true\n' > "$d/.env"
(cd "$d" && hx "$d" timeout 12 "$BIN" serve > /dev/null 2>&1)
[ -s "$d/opened" ] && echo "  CONTROL FAILED: browser opened without a BOM too"
rm -f "$d/opened"; : > "$d/.env"
(cd "$d" && hx "$d" timeout 12 "$BIN" serve > /dev/null 2>&1)
[ -s "$d/opened" ] || echo "  CONTROL FAILED: browser never opens here, probe is blind"
rm -rf "$d"

echo "# $bad broken, $good ok"
[ $good -eq 0 ]
