#!/data/data/com.termux/files/usr/bin/sh
# Run inside Termux: start `tina4 serve` for each scaffolded app, fetch its home
# page, report the HTTP status and whether it is the framework's page, then stop it.
# usage: sh serve-all.sh <dir holding app-python app-php app-ruby app-nodejs> [extra serve args]
base="$1"; shift
export PATH="$HOME/.local/bin:$PATH"
for l in python php ruby nodejs; do
  case $l in php) port=7145;; python) port=7146;; ruby) port=7147;; nodejs) port=7148;; esac
  cd "$base/app-$l" || { echo "$l: no project"; continue; }
  log="$TMPDIR/serve-$l.log"
  tina4 serve --no-browser --no-reload "$@" >"$log" 2>&1 </dev/null &
  pid=$!
  code=000
  for _ in $(seq 60); do
    code=$(curl -s -o "$TMPDIR/body-$l" -w '%{http_code}' "http://127.0.0.1:$port/" 2>/dev/null)
    [ "$code" != 000 ] && break
    kill -0 $pid 2>/dev/null || break
    sleep 2
  done
  tina4mark=$(grep -c -i tina4 "$TMPDIR/body-$l" 2>/dev/null)
  echo "$l: http=$code tina4-in-body=${tina4mark:-0} serve-alive=$(kill -0 $pid 2>/dev/null && echo yes || echo no)"
  [ "$code" = 000 ] && tail -5 "$log" | sed "s/^/    /"
  kill $pid 2>/dev/null; sleep 1
  pkill -f "app-$l" 2>/dev/null
  # anything still holding the port
  for p in $(pgrep -f "$port"); do kill $p 2>/dev/null; done
  sleep 1
done
