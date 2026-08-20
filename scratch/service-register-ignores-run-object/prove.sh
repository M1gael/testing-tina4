#!/usr/bin/env bash
# Proof: ServiceRunner.register() ignores plain class instances with run() method.
#
# Probes ServiceRunner handler registration & execution:
#   - Target:  plain class instance implementing run() & stop() (Chapter 27 contract)
#   - Control 1: plain callable registered via register(handler)
#   - Control 2: class-based Service registered via register_service(instance)
#   - Type check: invalid non-callable objects rejected at register() time
#
# Usage:
#   ./prove.sh            probe stock framework (fails: plain class instance run() ignored)
#   ./prove.sh --fixed    apply candidate patches (.fw16-candidate.patch + .fw02-candidate.patch),
#                         probe, restore venv, verify MD5
#
# Re-runnable by anyone.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "../lib/candidate-patch.sh"

SITE="$(patch_site_dir)"
TARGET="${SITE}/service/__init__.py"

if [ ! -f "$TARGET" ]; then
    echo "Error: target file not found: $TARGET" >&2
    exit 1
fi

STOCK_MD5="$(md5sum "$TARGET" | cut -d' ' -f1)"

MODE_FIXED=0
MODE_LABEL="STOCK FRAMEWORK (as installed)"

if [ "${1:-}" = "--fixed" ]; then
    MODE_FIXED=1
    MODE_LABEL="WITH CANDIDATE FIXES (.fw16 + .fw02)"
    echo "Applying candidate patches to service/__init__.py..."
    echo "  Stock MD5: $STOCK_MD5"

    TRUE_BACKUP="$(mktemp -t true-stock-service-XXXXXX)"
    cp "$TARGET" "$TRUE_BACKUP"

    cleanup() {
        local exit_code=$?
        echo ""
        echo "Restoring stock framework..."
        cp "$TRUE_BACKUP" "$TARGET"
        rm -f "$TRUE_BACKUP"
        find "$SITE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
        _PATCH_TARGET="$TARGET"
        patch_verify_restored "$STOCK_MD5"
        exit "$exit_code"
    }
    trap cleanup EXIT INT TERM

    PATCH1="$(realpath ../.fw16-candidate.patch)"
    PATCH2="$(realpath ../.fw02-candidate.patch)"

    echo "  Applying patch 1: .fw16-candidate.patch..."
    patch_apply "$PATCH1" service/__init__.py

    echo "  Applying patch 2: .fw02-candidate.patch..."
    patch_apply "$PATCH2" service/__init__.py

    PATCHED_MD5="$(md5sum "$TARGET" | cut -d' ' -f1)"
    echo "  Patched MD5: $PATCHED_MD5"
fi

VERSION="$(.venv/bin/python -c 'import tina4_python;print(getattr(tina4_python, "__version__", "unknown"))' 2>/dev/null || echo unknown)"

echo
echo "=============================================================="
echo " ServiceRunner Plain Object run() Proof — ${MODE_LABEL}"
echo " tina4-python ${VERSION}"
echo "=============================================================="
echo

.venv/bin/python prove.py
