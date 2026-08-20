#!/usr/bin/env bash
# Proof: ServiceRunner.stop() does not stop class-based Service instances and leaks threads.
#
# Probes ServiceRunner lifecycle:
#   - Control: plain callable registered via register() observing ctx.stop_event
#   - Target:  class-based Service registered via register_service() observing self.should_stop()
#
# Usage:
#   ./prove.sh            probe stock framework (fails: class service leaks thread, stop() blocks 5s)
#   ./prove.sh --fixed    apply candidate patch (.fw16-candidate.patch), probe, restore venv, verify MD5
#
# Re-runnable by anyone.

set -euo pipefail
cd "$(dirname "$0")"

# Source the shared patch manager
# shellcheck source=/dev/null
source "../lib/candidate-patch.sh"

SITE_DIR="$(patch_site_dir)"
TARGET_REL="service/__init__.py"
TARGET_ABS="${SITE_DIR}/${TARGET_REL}"
PATCH_FILE="$(realpath "../.fw16-candidate.patch")"

STOCK_MD5="$(md5sum "$TARGET_ABS" | cut -d' ' -f1)"

cleanup() {
  if [ "${MODE_FIXED:-0}" -eq 1 ]; then
    patch_restore
    patch_verify_restored "$STOCK_MD5"
  fi
}
trap cleanup EXIT INT TERM

MODE_FIXED=0
MODE_LABEL="STOCK FRAMEWORK (as installed)"

if [ "${1:-}" = "--fixed" ]; then
  MODE_FIXED=1
  MODE_LABEL="WITH CANDIDATE FIX (.fw16-candidate.patch)"
  echo "Applying candidate patch to ${TARGET_REL}..."
  patch_apply "$PATCH_FILE" "$TARGET_REL"
  echo "  patch applied successfully"
fi

VERSION="$(.venv/bin/python -c 'import tina4_python;print(getattr(tina4_python, "__version__", "unknown"))' 2>/dev/null || echo unknown)"

echo
echo "=============================================================="
echo " ServiceRunner Stop Thread Leak Proof — ${MODE_LABEL}"
echo " tina4-python ${VERSION}"
echo "=============================================================="
echo

.venv/bin/python prove.py
