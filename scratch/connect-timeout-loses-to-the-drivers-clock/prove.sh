#!/usr/bin/env bash
# Proof: the framework's connect-timeout message loses to the driver's own,
# because the framework times the bound on CLOCK_MONOTONIC and libpq times its
# connect_timeout on CLOCK_REALTIME.
#
#   ./prove.sh              probe the stock released framework   (leaks)
#   ./prove.sh --fixed      apply .fw18-candidate-ab.patch       (holds)
#   ./prove.sh --fixed a    dual-clock gate only
#   ./prove.sh --fixed b    strict driver option only            (leaks at 2.0x)
#
# Re-runnable by anyone with gcc. No mocks, no monkeypatching: a real listening
# socket, the real PostgreSQLAdapter, and a real clock made to diverge.

set -euo pipefail
cd "$(dirname "$0")"

# shellcheck source=/dev/null
source "../lib/candidate-patch.sh"

SITE_DIR="$(patch_site_dir)"
TARGET_REL="database/adapter.py"
TARGET_ABS="${SITE_DIR}/${TARGET_REL}"
STOCK_MD5="$(md5sum "$TARGET_ABS" | cut -d' ' -f1)"

MODE_FIXED=0
VARIANT="ab"
if [ "${1:-}" = "--fixed" ]; then
  MODE_FIXED=1
  VARIANT="${2:-ab}"
fi
PATCH_FILE="$(realpath "../.fw18-candidate-${VARIANT}.patch")"

cleanup() {
  if [ "$MODE_FIXED" -eq 1 ]; then
    patch_restore
    patch_verify_restored "$STOCK_MD5"
  fi
  rm -f /tmp/fw18-gtod.$$
}
trap cleanup EXIT INT TERM

case "$VARIANT" in
  a)  LABEL="CANDIDATE A — dual-clock gate only" ;;
  b)  LABEL="CANDIDATE B — strict driver option only" ;;
  ab) LABEL="CANDIDATE A+B — dual-clock gate and strict driver option" ;;
  *)  echo "unknown variant: $VARIANT"; exit 2 ;;
esac
[ "$MODE_FIXED" -eq 1 ] || LABEL="STOCK FRAMEWORK (as released, unpatched)"

gcc -shared -fPIC -O2 -o skew.so skew.c -ldl

VERSION="$(.venv/bin/python -c 'import tina4_python;print(getattr(tina4_python,"__version__","unknown"))' 2>/dev/null || echo unknown)"
DRIVER="$(.venv/bin/python -c 'import psycopg2;print(psycopg2.__version__.split()[0], psycopg2.__libpq_version__)')"

echo
echo "=================================================================="
echo " PY-FW-18 — the framework's connect-timeout message loses a race"
echo " ${LABEL}"
echo " tina4-python ${VERSION}   psycopg2/libpq ${DRIVER}"
echo "=================================================================="
echo
if [ "$MODE_FIXED" -eq 1 ]; then
  echo "Applying $(basename "$PATCH_FILE") to ${TARGET_REL}..."
  patch_apply "$PATCH_FILE" "$TARGET_REL"
  echo "  applied; stock md5 was ${STOCK_MD5}"
  echo
fi

echo "-- The two clocks, straight out of the driver binary -------------"
SO="$(echo "${SITE_DIR%/tina4_python}"/psycopg2/_psycopg*.so)"
echo "  nm -D --undefined-only $(basename "$SO")"
nm -D --undefined-only "$SO" | grep -E "gettimeofday|clock_gettime" | sed 's/^/    /' || true
echo "    (gettimeofday is CLOCK_REALTIME. No clock_gettime import at all,"
echo "     so nothing in libpq reads the monotonic clock the framework uses.)"
echo

run() {  # run <rate> <mode>
  TINA4_DATABASE_CONNECT_TIMEOUT=2 SKEW_RATE="$1" LD_PRELOAD=./skew.so \
    .venv/bin/python prove.py "$2" 2>&1 | grep -v '^\[' || true
}

echo "-- Controls: clocks agree, so the promise holds ------------------"
run 1.0 silent
run 1.0 dribble
echo
echo "-- Clocks diverge: realtime runs ahead of monotonic --------------"
run 1.3 dribble
run 2.0 dribble
echo
echo "-- How wide the window is on the silent server (the CI case) -----"
TINA4_DATABASE_CONNECT_TIMEOUT=2 SKEW_LOG="/tmp/fw18-gtod.$$" SKEW_RATE=1.0 \
  LD_PRELOAD=./skew.so .venv/bin/python prove.py exposure 2>&1 | grep -v '^\[' || true
echo
