#!/bin/sh
# Attacking the sec-01 fix. The axes: which env var is set, to what, and in which mode.
#
# A fix that only ever binds loopback would be safe and useless -- anyone who genuinely wants the
# shell on a LAN must still be able to say so, and both env names the project already documents
# must keep working. So the matrix checks the opt-in as hard as it checks the default.
#
#   usage: ./attack.sh <tree>
set -e
TREE="${1:-/var/home/work/gitdir/tina4-simple-agent-work/scratch}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT=8797
echo "tree  $TREE  ($(git -C "$TREE" describe --tags --always 2>/dev/null))"
echo ""

PASS=0; FAIL=0
cell() {
  WANT_BIND="$1"; WANT_WARN="$2"; NAME="$3"; shift 3
  TMP="$(mktemp -d /tmp/sec01atk-XXXX)"
  OUT="$(env -i HOME="$TMP" PATH=/usr/bin:/bin \
      TINA4_AGENT_PORT="$PORT" TINA4_NO_BROWSER=true \
      TINA4_PROJECTS_ROOT="$TMP/projects" TINA4_STATE_DIR="$TMP/state" \
      "$@" \
      unshare -rn "$HERE/inside-netns.sh" "$PORT" "$TREE" "$TMP/boot.log" 2>&1)"
  BIND="$(echo "$OUT" | awk '/^BIND/{print $2}')"
  WARN="$(echo "$OUT" | awk '/^WARNED/{print $2}')"
  WS="$(echo "$OUT" | awk '/^WSUPGRADE/{print $2}')"
  OK=yes
  case "$BIND" in "$WANT_BIND":*) ;; *) OK=no ;; esac
  [ "$WANT_WARN" = "warn" ] && [ "${WARN:-0}" -lt 1 ] && OK=no
  [ "$WANT_WARN" = "quiet" ] && [ "${WARN:-0}" -ge 1 ] && OK=no
  [ "$WS" = "101" ] || OK=no
  if [ "$OK" = yes ]; then PASS=$((PASS+1)); echo "PASS  $NAME"; else FAIL=$((FAIL+1)); echo "FAIL  $NAME"; fi
  echo "        bind=${BIND:-<none>} want=$WANT_BIND  warned=${WARN:-0} want=$WANT_WARN  ws=${WS:-<none>} want=101"
  rm -rf "$TMP"
}

cell 127.0.0.1 quiet "default: no env at all -> loopback, no warning"
cell 127.0.0.1 quiet "TINA4_DEBUG=true (dev mode) -> still loopback" TINA4_DEBUG=true
cell 0.0.0.0   warn  "TINA4_EXPOSE=true -> every interface, and says so" TINA4_EXPOSE=true
cell 127.0.0.1 quiet "TINA4_EXPOSE=false -> loopback" TINA4_EXPOSE=false
cell 127.0.0.1 quiet "TINA4_EXPOSE=banana (not a truth value) -> loopback" TINA4_EXPOSE=banana
cell 0.0.0.0   warn  "TINA4_HOST=0.0.0.0 still honoured (documented override)" TINA4_HOST=0.0.0.0
cell 0.0.0.0   warn  "HOST=0.0.0.0 still honoured (framework fallback name)" HOST=0.0.0.0
cell 127.0.0.1 quiet "TINA4_HOST beats TINA4_EXPOSE when they disagree" TINA4_HOST=127.0.0.1 TINA4_EXPOSE=true

echo ""
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
