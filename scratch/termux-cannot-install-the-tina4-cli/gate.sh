#!/usr/bin/env bash
# Gate: on a FRESH Termux (nothing but the bootstrap + openssh), with only the
# tina4 binary under test in $PREFIX/bin, each language must go from nothing to
# a served app through tina4 alone:
#   1. `tina4 init <lang> app`  -> exit 0, runtime + deps installed by tina4
#   2. `tina4 serve` on it       -> HTTP 200, a tina4 page
#   3. `tina4 install <lang>`    -> exit 0, nothing reported as failed
#   4. `tina4 doctor` in a new login shell -> the language and its package
#      manager are ✓, and tina4<lang> too (not php: install only hints there)
# Each language starts from its own fresh Termux, so no language borrows a
# toolchain another one installed.
# ORDER=install-first runs step 3 before step 1, so install does the installing.
# usage: gate.sh <tina4 android binary> [langs...]   (default: php ruby nodejs python)
set -uo pipefail
BIN=$1; shift
LANGS=${*:-php ruby nodejs python}
VM=/var/home/work/vm
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HERE/gate-out; mkdir -p "$OUT"
SSH=(ssh -o BatchMode=yes -p 8022 127.0.0.1)
fail=0

for l in $LANGS; do
  case $l in php) port=7145; mgr=composer;; python) port=7146; mgr=uv;; ruby) port=7147; mgr=bundler;; nodejs) port=7148; mgr=npm;; esac
  # right after `tina4 install`, the package manager must already be there
  mgrcmd=$(case $l in php) echo composer;; python) echo uv;; ruby) echo bundle;; nodejs) echo npm;; esac)
  "$VM/termux-reset.sh" >"$OUT/$l-reset.txt" 2>&1 || "$VM/termux-reset.sh" >>"$OUT/$l-reset.txt" 2>&1 || { echo "$l: RESET FAILED (see $OUT/$l-reset.txt)"; fail=1; continue; }
  scp -q -P 8022 "$BIN" 127.0.0.1:../usr/bin/tina4
  # PRE: a state to start from, e.g. a runtime installed without its package manager
  [ -n "${PRE:-}" ] && "${SSH[@]}" "$PRE" >"$OUT/$l-pre.txt" 2>&1
  if [ "${ORDER:-}" = install-first ]; then
  "${SSH[@]}" "timeout 1500 tina4 install $l </dev/null; echo INSTALL_RC=\$?; command -v $mgrcmd >/dev/null || echo MANAGER_MISSING" >"$OUT/$l-install.txt" 2>&1
  inst_rc=$(grep -a -o 'INSTALL_RC=[0-9]*' "$OUT/$l-install.txt" | cut -d= -f2)
  inst_fail=$(grep -a -c -E '✗|not found|Could not install|was not installed|MANAGER_MISSING' "$OUT/$l-install.txt")

  "${SSH[@]}" "mkdir -p ~/g && cd ~/g && timeout 1500 tina4 init $l app </dev/null; echo INIT_RC=\$?" >"$OUT/$l-init.txt" 2>&1
  init_rc=$(grep -a -o 'INIT_RC=[0-9]*' "$OUT/$l-init.txt" | cut -d= -f2)

  else
  "${SSH[@]}" "mkdir -p ~/g && cd ~/g && timeout 1500 tina4 init $l app </dev/null; echo INIT_RC=\$?" >"$OUT/$l-init.txt" 2>&1
  init_rc=$(grep -a -o 'INIT_RC=[0-9]*' "$OUT/$l-init.txt" | cut -d= -f2)

  "${SSH[@]}" "timeout 1500 tina4 install $l </dev/null; echo INSTALL_RC=\$?; command -v $mgrcmd >/dev/null || echo MANAGER_MISSING" >"$OUT/$l-install.txt" 2>&1
  inst_rc=$(grep -a -o 'INSTALL_RC=[0-9]*' "$OUT/$l-install.txt" | cut -d= -f2)
  inst_fail=$(grep -a -c -E '✗|not found|Could not install|was not installed|MANAGER_MISSING' "$OUT/$l-install.txt")

  fi
  "${SSH[@]}" "cd ~/g/app 2>/dev/null || exit 9
    tina4 serve --no-browser --no-reload </dev/null >\$TMPDIR/serve.log 2>&1 & pid=\$!
    code=000; for _ in \$(seq 90); do code=\$(curl -s -o \$TMPDIR/body -w '%{http_code}' http://127.0.0.1:$port/); [ \$code != 000 ] && break; kill -0 \$pid 2>/dev/null || break; sleep 2; done
    echo HTTP=\$code TINA4=\$(grep -c -i tina4 \$TMPDIR/body 2>/dev/null)
    kill \$pid 2>/dev/null; sleep 2; pkill -f 'app' 2>/dev/null; tail -5 \$TMPDIR/serve.log" >"$OUT/$l-serve.txt" 2>&1
  http=$(grep -a -o 'HTTP=[0-9]*' "$OUT/$l-serve.txt" | cut -d= -f2); marks=$(grep -a -o 'TINA4=[0-9]*' "$OUT/$l-serve.txt" | cut -d= -f2)

  # A new Termux session: interactive login shell, so PATH is what a user gets.
  "${SSH[@]}" "bash -lic 'tina4 doctor' </dev/null" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' >"$OUT/$l-doctor.txt"
  label=$(case $l in php) echo PHP;; python) echo Python;; ruby) echo Ruby;; nodejs) echo Node.js;; esac)
  drow=$(grep -m1 -E "^  $label " "$OUT/$l-doctor.txt")
  doc_ok=$( [[ $drow =~ ^\ \ $label\ +✓.*✓\ $mgr ]] && echo yes || echo no )
  # tina4 install puts the language CLI on PATH (php only prints a hint, everywhere)
  if [ "$l" != php ] && ! grep -q -E "^  ✓ tina4$l " "$OUT/$l-doctor.txt"; then doc_ok=no-cli; fi
  # Android denies hard links; no uv that tina4 starts should still warn about it.
  if grep -a -q 'Failed to hardlink' "$OUT/$l-init.txt" "$OUT/$l-install.txt"; then doc_ok="$doc_ok+hardlink-warning"; fi

  ok=yes
  [ "${init_rc:-x}" = 0 ] || ok=no; [ "${http:-000}" = 200 ] || ok=no; [ "${marks:-0}" -gt 0 ] || ok=no
  [ "${inst_rc:-x}" = 0 ] || ok=no; [ "$inst_fail" = 0 ] || ok=no; [ "$doc_ok" = yes ] || ok=no
  [ $ok = yes ] || fail=1
  echo "$l: $( [ $ok = yes ] && echo PASS || echo FAIL )  init_rc=${init_rc:-none} http=${http:-none} tina4_marks=${marks:-0} install_rc=${inst_rc:-none} install_failures=$inst_fail doctor=$doc_ok"
done
exit $fail
