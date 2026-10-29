# sourced. start_port <py|php|rb|nd> <port>; stop_port. EXTRA_ENV adds env vars.
# Trees under ~/.cache/tina4-worktrees (override with TINA4_PY/PHP/RB; nd via nd/node_modules/tina4-nodejs symlink):
#   py docfix-dauth02-stock-python, php docfix-dauth02-stock-php, rb docfix-stock-ruby, nd docfix-stock-nodejs (dist built).
port_busy(){ curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$1/" && return 0; ss -ltn 2>/dev/null | grep -q ":$1 "; }
wait_port_free(){ for i in $(seq 60); do port_busy "$1" || return 0; sleep 0.25; done; echo "PORT $1 STILL BUSY after stop"; return 1; }
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); W=$HOME/.cache/tina4-worktrees
PYT=${TINA4_PY:-$W/docfix-dauth02-stock-python}; PHPT=${TINA4_PHP:-$W/docfix-dauth02-stock-php}; RBT=${TINA4_RB:-$W/docfix-stock-ruby}
PYBIN=${PYBIN:-/var/home/work/gitdir/tinaforks/tina4-python/.venv/bin/python}
start_port(){ local l=$1 p=$2; port_busy $p && { echo "PORT $p BUSY before start"; return 1; }; SPORT=$p
  SHOME=$(mktemp -d)
  local ENVV=(${EXTRA_ENV:-} HOME=$SHOME TINA4_OVERRIDE_CLIENT=true TINA4_DEBUG=false TINA4_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef); cd "$HERE/$l"; rm -rf data/sessions* sessions
  case $l in
    py)  env "${ENVV[@]}" PYTHONPATH=$PYT TINA4_PORT=$p PORT=$p $PYBIN app.py --managed >server.log 2>&1 & ;;
    php) env "${ENVV[@]}" php $PHPT/bin/tina4php serve 127.0.0.1:$p >server.log 2>&1 & ;;
    rb)  env "${ENVV[@]}" PORT=$p ruby -I $RBT/lib app.rb >server.log 2>&1 & ;;
    nd)  env "${ENVV[@]}" PORT=$p node app.mjs >server.log 2>&1 & ;;
  esac; SPID=$!; cd - >/dev/null
  for i in $(seq 80); do curl -s -o /dev/null http://127.0.0.1:$p/ping && return 0; sleep 0.25; done; echo "$l did not start"; tail -5 "$HERE/$l/server.log"; return 1; }
stop_port(){ pkill -P $SPID 2>/dev/null; kill $SPID 2>/dev/null; wait $SPID 2>/dev/null; rm -rf "$SHOME"; wait_port_free $SPORT; }
