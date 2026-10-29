# sourced. start_app <dir> <port> <cmd...>; stop_app. Refuses a busy port, kills what it starts.
W=/var/home/work/.cache/tina4-worktrees
PYT=$W/side1028-python RBT=$W/side1028-ruby NDT=$W/side1028-nodejs PHPT=$W/side1028-php
PYBIN=/var/home/work/gitdir/tinaforks/tina4-python/.venv/bin/python
port_busy(){ ss -ltn 2>/dev/null | /usr/bin/grep -q "[:.]$1 " && return 0; curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$1/" && return 0; return 1; }
wait_free(){ for i in $(seq 60); do port_busy $1 || return 0; sleep 0.25; done; echo "PORT $1 STILL BUSY after stop" >&2; return 1; }
start_app(){ local dir=$1 p=$2; shift 2
  case $p in 76[5-9][0-9]) ;; *) echo "PORT $p outside 7650-7699" >&2; return 1;; esac
  port_busy $p && { echo "PORT $p BUSY before start" >&2; return 1; }
  APP_HOME=$(mktemp -d); APP_PORT=$p; APP_LOG=$(mktemp)
  ( cd "$dir" && exec env HOME=$APP_HOME PORT=$p TINA4_PORT=$p TINA4_DEBUG=false TINA4_OVERRIDE_CLIENT=true TINA4_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef "$@" ) >$APP_LOG 2>&1 &
  APP_PID=$!
  for i in $(seq 120); do curl -s -o /dev/null --max-time 1 http://127.0.0.1:$p/ping && return 0; kill -0 $APP_PID 2>/dev/null || break; sleep 0.25; done
  echo "app in $dir did not start on $p" >&2; tail -5 $APP_LOG >&2; stop_app; return 1; }
killtree(){ local c; for c in $(pgrep -P $1); do killtree $c; done; kill $1 2>/dev/null; }
stop_app(){ killtree $APP_PID; wait $APP_PID 2>/dev/null
  wait_free $APP_PORT; local r=$?; rm -rf "$APP_HOME" "$APP_LOG"; return $r; }
code(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$@"; }
# stage <app dir>: copy an app into the run's temp dir so the framework's scaffolding (data/, .env, logs/) never lands in scratch
stage(){ local dst=$RUN/$(echo "$1" | tr / _); rm -rf "$dst"; cp -r "$HERE/$1" "$dst"; echo "$dst"; }
