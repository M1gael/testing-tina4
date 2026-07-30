#!/usr/bin/env bash
# Run every probe in order. Claim A and D are fully automatic; B has one half
# that needs a human eye, so that probe pauses and waits for you.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/lib/common.sh"
ensure_deps

printf '%s\n' "$c_bold=== debug-false repro suite ===$c_reset"
dim "mock app: $MOCKAPP"
dim "run logs: $RUN_DIR"

bash "$HERE/probe-a-browser.sh"
bash "$HERE/probe-d-asktina4.sh"
bash "$HERE/probe-bc-footer.sh"

printf '\n%s\n' "$c_bold=== done ===$c_reset"
dim "Full write-up with source references: ../README.md"
