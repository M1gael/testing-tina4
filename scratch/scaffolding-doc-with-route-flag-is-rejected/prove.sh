#!/bin/bash
# Usage: DOCS=<tina4-documentation tree> BOOK=<tina4-book tree> ./prove.sh
# RT = runtime built by setup.sh (outside scratch). rc 0 = PASS, 1 = wrong docs found, 2 = setup.
RT=${RT:-$HOME/.cache/tina4-worktrees/verify-1029/d-cli-02}
: "${DOCS:?set DOCS (or none)}" "${BOOK:?set BOOK (or none)}"
[ -x "$RT/shims/tina4" ] || { echo "no runtime at $RT; run setup.sh"; exit 2; }
exec python3 -I "$(dirname "$0")/prove.py" "$DOCS" "$BOOK" "$RT"
