#!/usr/bin/env bash
# f-cli-25 — does a UTF-8 BOM at the start of .env hide its first variable from
# `tina4 serve`? No network, no framework: app.py dumps the env it was handed.
#
#   BIN=/path/to/tina4 ./prove.sh
#
# Exit 0 = defect present. Exit 1 = first variable arrived intact.
set -u
BIN="${BIN:-$HOME/.cache/tina4-update-probe/a/bin/tina4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
echo "# binary:  $BIN ($("$BIN" --version 2>&1 | head -1))"

run() {  # run <label> <bom: yes|no>
    local label="$1"
    if [ "$2" = yes ]; then printf '\xef\xbb\xbf' > .env; else : > .env; fi
    printf 'FIRST_KEY=first\nSECOND_KEY=second\n' >> .env
    rm -f "evidence/dump.$label.txt"
    env -i HOME="$HERE/evidence" PATH=/usr/bin:/bin TINA4_NO_BROWSER=true \
        DUMP_TO="evidence/dump.$label.txt" \
        timeout 20 "$BIN" serve > "evidence/serve.$label.log" 2>&1
    echo "## $label (.env starts: $(head -c 3 .env | od -An -tx1 | tr -s ' '))"
    sed 's/^/    /' "evidence/dump.$label.txt" 2>/dev/null || echo "    (no dump)"
}

run nobom no
run bom yes
rm -f .env

got() { sed -n "s/^$1=//p" "evidence/dump.$2.txt" 2>/dev/null; }
echo "## verdict"
[ "$(got FIRST_KEY nobom)" = first ] || { echo "    control failed: no-BOM run lost FIRST_KEY"; exit 2; }
if [ "$(got FIRST_KEY bom)" != first ] && [ "$(got SECOND_KEY bom)" = second ]; then
    echo "    DEFECT PRESENT: with a BOM, FIRST_KEY=$(got FIRST_KEY bom), SECOND_KEY intact."
    exit 0
fi
echo "    NOT REPRODUCED: FIRST_KEY=$(got FIRST_KEY bom) with a BOM."
exit 1
