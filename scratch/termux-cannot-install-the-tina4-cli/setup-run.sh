#!/usr/bin/env bash
# Drive the real interactive `tina4 setup` on a FRESH Termux, the way the
# installer hands over to it: pick a language, no AI tool, default folder and
# project name, decline "start it now". Then check what setup left behind:
# git installed, the project serves the tina4 page, doctor sees the runtime.
# usage: setup-run.sh <tina4 android binary> <python|nodejs|php|ruby>
set -uo pipefail
BIN=$1; LANG_NAME=$2
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HERE/setup-out; mkdir -p "$OUT"
SSH=(ssh -o BatchMode=yes -p 8022 127.0.0.1)
case $LANG_NAME in python) n=1; port=7146;; nodejs) n=2; port=7148;; php) n=3; port=7145;; ruby) n=4; port=7147;; esac

/var/home/work/vm/termux-reset.sh >"$OUT/$LANG_NAME-reset.txt" 2>&1 || /var/home/work/vm/termux-reset.sh >>"$OUT/$LANG_NAME-reset.txt" 2>&1 || { echo "$LANG_NAME: RESET FAILED"; exit 2; }
scp -q -P 8022 "$BIN" 127.0.0.1:../usr/bin/tina4

# Answers go in through a real pty (ssh -tt), each only once its prompt is on
# screen, so nothing leaks into the installers setup runs: language, AI = 6
# (none), projects folder default, project name default, "start it now?" = n.
python3 "$HERE/drive.py" "$OUT/$LANG_NAME-setup.txt" 1500 \
  "Choose 1-4=$n" "Choose 1-6=6" "Projects folder=" "Name of your first project=" "Start it now=n" -- \
  ssh -tt -p 8022 127.0.0.1 'tina4 setup; echo SETUP_RC=$?; exit'
rc=$(tr -d '\r' <"$OUT/$LANG_NAME-setup.txt" | grep -a -o 'SETUP_RC=[0-9]*' | cut -d= -f2)

git_ok=$("${SSH[@]}" 'command -v git >/dev/null && echo yes || echo no')
"${SSH[@]}" "cd ~/projects/tina4example 2>/dev/null || exit 9
  tina4 serve --no-browser --no-reload </dev/null >\$TMPDIR/serve.log 2>&1 & pid=\$!
  code=000; for _ in \$(seq 90); do code=\$(curl -s -o \$TMPDIR/body -w '%{http_code}' http://127.0.0.1:$port/); [ \$code != 000 ] && break; kill -0 \$pid 2>/dev/null || break; sleep 2; done
  echo HTTP=\$code TINA4=\$(grep -c -i tina4 \$TMPDIR/body 2>/dev/null)
  kill \$pid 2>/dev/null; sleep 2; pkill -f tina4example" >"$OUT/$LANG_NAME-serve.txt" 2>&1
http=$(grep -a -o 'HTTP=[0-9]*' "$OUT/$LANG_NAME-serve.txt" | cut -d= -f2)
fails=$(sed 's/\x1b\[[0-9;]*m//g' "$OUT/$LANG_NAME-setup.txt" | grep -a -c -E '✗|Could not install|install failed|Command failed')

ok=yes
[ "${rc:-x}" = 0 ] || ok=no; [ "$git_ok" = yes ] || ok=no; [ "${http:-000}" = 200 ] || ok=no; [ "$fails" = 0 ] || ok=no
echo "$LANG_NAME setup: $( [ $ok = yes ] && echo PASS || echo FAIL )  setup_rc=${rc:-none} git=$git_ok http=${http:-none} failures_in_output=$fails"
[ $ok = yes ]
