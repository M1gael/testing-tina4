#!/usr/bin/env bash
# DOCS=<tina4-documentation tree> ./prove.sh   or   BOOK=<tina4-book tree> ./prove.sh
# PASS rc0 / FAIL rc1 / ERROR rc2 (missing interpreter, generator failure, missing page).
set -u
for t in python3 php ruby node; do command -v $t >/dev/null || { echo "ERROR: $t missing"; exit 2; }; done
exec python3 -I "$(dirname "$0")/prove.py"
