#!/usr/bin/env bash
# CLI-FW-02 — does `tina4 serve` kill whatever holds its port, Tina4 or not?
#
# Every case runs in a fresh temp project with a hermetic env. The holder is a
# `python3 -m http.server` on a test port; the project's app.py is a stand-in
# that sleeps, so nothing but the holder ever binds the port.
#
#   BIN=/path/to/tina4 ./prove.sh
#
# Prints one line per case: whether the holder survived. The policy the four
# framework ports already ship (TAKEOVER-DEC-01) is: reclaim only a holder whose
# PID is recorded in data/.tina4-serve-<port>.pid; refuse anything else.
# Exit 0 = the CLI follows that policy in every case. Exit 1 = it does not.
set -u
BIN="${BIN:-$HOME/.cache/tina4-update-probe/a/bin/tina4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "# binary: $BIN ($("$BIN" --version 2>&1 | head -1))"
fail=0

case_() { # case_ <label> <port> <pidfile: none|holder|other> <how: explicit|default> <want: survives|reclaimed>
  local label=$1 port=$2 pidf=$3 how=$4 want=$5 d holder got
  if ss -ltn | grep -q ":$port "; then echo "  SKIP $label: port $port already in use here"; fail=1; return; fi
  d=$(mktemp -d); printf 'tina4_python\n' > "$d/requirements.txt"
  printf 'import time; time.sleep(3)\n' > "$d/app.py"
  [ "$how" = default ] && printf 'TINA4_PORT=%s\n' "$port" > "$d/.env"
  (cd "$d" && exec python3 -m http.server "$port" --bind 127.0.0.1 >/dev/null 2>&1) & holder=$!
  for _ in $(seq 50); do ss -ltn | grep -q ":$port " && break; sleep 0.1; done
  mkdir -p "$d/data"
  case $pidf in holder) echo "$holder" > "$d/data/.tina4-serve-$port.pid";;
                other)  echo 999999 > "$d/data/.tina4-serve-$port.pid";; esac
  local args=(serve); [ "$how" = explicit ] && args+=(-p "$port")
  (cd "$d" && env -i HOME="$d" PATH=/usr/bin:/bin TERM=dumb TINA4_NO_BROWSER=true \
      timeout 10 "$BIN" "${args[@]}" > "$HERE/evidence/$label.log" 2>&1)
  if kill -0 "$holder" 2>/dev/null; then got=survives; else got=reclaimed; fi
  kill "$holder" 2>/dev/null; wait "$holder" 2>/dev/null
  if [ "$got" = "$want" ]; then echo "  ok   $label: holder $got"; else echo "  FAIL $label: holder $got, policy says $want"; fail=1; fi
  echo "       cli: $(grep -m1 -E 'Port [0-9]+ (in use|is held)|Reclaimed|freed|non-Tina4' "$HERE/evidence/$label.log")"
  rm -rf "$d"
}

case_ foreign-explicit      8941 none   explicit survives
case_ foreign-default       8942 none   default  survives
case_ stale-pidfile-other   8943 other  explicit survives
case_ own-server-explicit   8944 holder explicit reclaimed
case_ own-server-default    8945 holder default  reclaimed
exit $fail
