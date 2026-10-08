#!/usr/bin/env bash
# tina4-nodejs parity for tina4-php#278: can an app bound the SMTP wait?
#
#   TREE_ND=<tina4-nodejs source tree, node_modules installed> ./prove.sh
#
# Cells run in parallel against ../blackhole-smtp.py (accepts, never speaks):
# the default, TINA4_MAIL_TIMEOUT=2, and a `timeout: 2` option. A fourth cell
# connects to full-backlog.py (SYN dropped) to see whether the CONNECT phase is
# bounded at all; it is capped at CONNECT_CAP (default 45) s by `timeout`. A fifth
# cell sends with implicit TLS to the silent listener (handshake never answered),
# capped at TLS_CAP (default 90) s.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${TREE_ND:?set TREE_ND to a tina4-nodejs tree}"
NODEBIN=$(dirname "$(readlink -f "$(command -v node)")")
echo "tree: $(git -C "$TREE_ND" rev-parse --short HEAD) ($(git -C "$TREE_ND" describe --tags 2>/dev/null)); node $(node --version)"
OUT=$(mktemp -d); trap 'kill $BH $FB 2>/dev/null; rm -rf "$OUT"' EXIT
python3 "$HERE/../blackhole-smtp.py" > "$OUT/bh.port" & BH=$!
python3 "$HERE/full-backlog.py" > "$OUT/fb.port" & FB=$!
sleep 1.5; BP=$(cat "$OUT/bh.port"); FP=$(cat "$OUT/fb.port")
send() { env -i HOME="$OUT" PATH="$NODEBIN:/usr/bin:/bin" "${@:3}" timeout "$2" \
  node --import "file://$TREE_ND/node_modules/tsx/dist/loader.mjs" "$HERE/send.mts" "$TREE_ND" 127.0.0.1 $1 ${EXTRA:-} \
  || echo "ELAPSED>=${2}s OUTCOME=still waiting when capped (timeout rc=$?)"; }
pids=()
( echo "default:                  $(send $BP 60)" ) > "$OUT/1" & pids+=($!)
( echo "TINA4_MAIL_TIMEOUT=2:     $(send $BP 60 TINA4_MAIL_TIMEOUT=2)" ) > "$OUT/2" & pids+=($!)
( echo "option {timeout: 2}:      $(EXTRA='{"timeout":2}' send $BP 60)" ) > "$OUT/3" & pids+=($!)
( echo "connect, SYN dropped:     $(send $FP ${CONNECT_CAP:-45})" ) > "$OUT/4" & pids+=($!)
( echo "implicit TLS (ssl):       $(EXTRA='{"encryption":"ssl"}' send $BP ${TLS_CAP:-90})" ) > "$OUT/5" & pids+=($!)
wait "${pids[@]}"
cat "$OUT"/1 "$OUT"/2 "$OUT"/3 "$OUT"/4 "$OUT"/5
