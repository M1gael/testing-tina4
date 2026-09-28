#!/usr/bin/env bash
# Boot released tina4-python under each (mode, secret) cell; report refused or booted.
# rc 1 + "TINA4_SECRET" on stderr = refused. Still running at the cap = booted.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-$HERE/.venv/bin/python}
port=8970
run() { # label, then env assignments
  local label=$1; shift
  local proj; proj=$(mktemp -d)
  printf 'from tina4_python.core import run\nrun()\n' > "$proj/app.py"
  (cd "$proj" && env -i HOME="$proj" PATH=/usr/bin:/bin LANG=C.UTF-8 TINA4_PORT=$port TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true "$@" \
     timeout 8 "$PY" app.py >"$proj/out" 2>&1); local rc=$?
  local verdict=booted; [ $rc -ne 124 ] && verdict="refused rc=$rc"
  local msg; msg=$(grep -m1 -o 'Auth: TINA4_SECRET[^;]*' "$proj/out")
  local minted=no; grep -q '^TINA4_SECRET=' "$proj/.env.local" 2>/dev/null && minted=yes
  printf '%-44s %-14s minted=%-3s %s\n' "$label" "$verdict" "$minted" "$msg"
  port=$((port+1)); rm -rf "$proj"
}
S31=$(printf 'a%.0s' $(seq 31)); S32=$(printf 'a%.0s' $(seq 32)); HEX=$("$PY" -c "import secrets;print(secrets.token_hex(32))")
run "dev, unset"                     TINA4_DEBUG=true
run "dev, 31 bytes"                  TINA4_DEBUG=true TINA4_SECRET=$S31
run "dev, 32 bytes"                  TINA4_DEBUG=true TINA4_SECRET=$S32
run "dev, 'secret' (6 bytes)"        TINA4_DEBUG=true TINA4_SECRET=secret
run "no debug, unset"
run "no debug, 31 bytes"             TINA4_SECRET=$S31
run "no debug, token_hex(32) (64 chars)" TINA4_SECRET=$HEX
run "production, 32 bytes"           TINA4_ENV=production TINA4_SECRET=$S32
run "dev + CI=true, unset"           TINA4_DEBUG=true CI=true
