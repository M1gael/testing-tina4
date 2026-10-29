#!/usr/bin/env bash
# Everything left, in order, on the one emulator. Results go to final-run.txt.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
WT=$HOME/.cache/tina4-worktrees/android-cli
FIXED=$HERE/tina4-fixed-android-x86_64
LOG=$HERE/final-run.txt
: >"$LOG"
say() { echo "$*" | tee -a "$LOG"; }

say "== disk at start: $(df -h / | awk 'NR==2{print $4" free"}')"
say "== component pass 2"
"$HERE/gate-components-2.sh" "$WT" >/dev/null 2>&1; cat "$HERE/gate-components-2.txt" >>"$LOG"

say "== installer (hosted install.sh, local release with tina4-android-amd64)"
"$HERE/installer-run.sh" "$FIXED" 2>&1 | tail -1 | tee -a "$LOG"

say "== tina4 setup, fresh Termux, each language"
for l in python nodejs php ruby; do "$HERE/setup-run.sh" "$FIXED" "$l" 2>&1 | tail -1 | tee -a "$LOG"; done

say "== final gate, both orders"
rm -rf "$HERE/gate-out"
"$HERE/gate.sh" "$FIXED" 2>&1 | tee -a "$LOG"; mv "$HERE/gate-out" "$HERE/gate-out-final" 2>/dev/null
ORDER=install-first "$HERE/gate.sh" "$FIXED" 2>&1 | tee -a "$LOG"; rm -rf "$HERE/gate-out-final-install-first"; mv "$HERE/gate-out" "$HERE/gate-out-final-install-first" 2>/dev/null
say "== disk at end: $(df -h / | awk 'NR==2{print $4" free"}')"
say "== FINISHED"
