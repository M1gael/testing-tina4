#!/usr/bin/env bash
# Does `tina4 serve` corrupt .env values whose content ends in a single quote?
#
# No network, no framework, no PHP. app.py is a stand-in for the language
# server: `tina4 serve` spawns `python3 app.py --managed`, and the child
# inherits the CLI's own process environment. Dumping that environment is
# enough to see what the framework would have been handed.
#
#   BIN=/path/to/tina4 ./prove.sh
#
# Exit 0 = defect present (values truncated on the default-port path).
set -u
BIN="${BIN:-/var/home/work/.cache/tina4-update-probe/a/bin/tina4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT_EXPLICIT="${PORT_EXPLICIT:-8791}"
cd "$HERE"

echo "# binary:  $BIN"
echo "# version: $("$BIN" --version 2>&1 | head -1)"
echo

run() {           # run <label> <outfile> [extra serve args...]
    local label="$1" out="$2"; shift 2
    rm -f "$out"
    env -u TINA4_CSP -u PLAIN_TRAILING_SQ -u SQ_WRAPPED -u DQ_WRAPPED \
        -u ENDS_DQ -u TRIPLE_SQ -u QUOTED_EMPTY \
        TINA4_NO_BROWSER=true DUMP_TO="$out" \
        timeout 20 "$BIN" serve "$@" >"evidence/serve.$label.log" 2>&1
    echo "## $label"
    if [ -f "$out" ]; then sed 's/^/    /' "$out"; else echo "    (no dump - server never spawned; see evidence/serve.$label.log)"; fi
    echo
}

run default evidence/dump.default.txt
run explicit evidence/dump.explicit.txt -p "$PORT_EXPLICIT"

want_csp="default-src 'self'; form-action 'self'"
got_default="$(sed -n 's/^TINA4_CSP=//p' evidence/dump.default.txt 2>/dev/null)"
got_explicit="$(sed -n 's/^TINA4_CSP=//p' evidence/dump.explicit.txt 2>/dev/null)"

echo "## verdict"
echo "    .env holds:            ${want_csp}"
echo "    serve (default port):  ${got_default:-<none>}"
echo "    serve -p ${PORT_EXPLICIT}:        ${got_explicit:-<none>}"
echo

if [ "$got_default" != "$want_csp" ] && [ -n "$got_default" ]; then
    echo "    DEFECT PRESENT: default-port serve handed the child a truncated value."
    echo "    lost $(( ${#want_csp} - ${#got_default} )) character(s) off the end."
    exit 0
fi
echo "    NOT REPRODUCED: value survived intact."
exit 1
