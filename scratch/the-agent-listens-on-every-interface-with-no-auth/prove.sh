#!/bin/sh
# sec-01 -- the agent binds 0.0.0.0 with no auth.
#
#   app.ts calls startServer({ basePath: HERE, port: SHELL_PORT })  -- no host.
#   tina4-nodejs resolves it (packages/core/src/server.ts:407):
#       defaultHost = isTruthy(process.env.TINA4_DEBUG) ? "127.0.0.1" : "0.0.0.0"
#       host = config?.host ?? TINA4_HOST ?? HOST ?? defaultHost
#   DISTRIBUTION.md ships PRODUCTION mode (no TINA4_DEBUG) to keep the dev toolbar out.
#   So the hand-delivered binary listens on every interface, with no auth and a run_shell tool.
#
# Three runs. Everything happens inside a network namespace with no route off this machine.
#
#   usage: ./prove.sh <tree>          (default: baseline-main)
# exit 0 = binds loopback by default (fixed).  exit 1 = binds 0.0.0.0 (defect).
set -e
TREE="${1:-/var/home/work/gitdir/tina4-simple-agent-work/baseline-main}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT=8796
STAMP="$(git -C "$TREE" describe --tags --always 2>/dev/null || echo unknown)"
echo "tree     $TREE  ($STAMP)"

run() {
  LABEL="$1"; shift
  TMP="$(mktemp -d /tmp/sec01-XXXX)"
  echo ""
  echo "--- $LABEL ---"
  # HOME/state/projects all redirected: no probe may touch the operator's real
  # ~/.tina4-simple-agent or ~/tina4-projects. TINA4_STATE_DIR alone is not enough (sec-03).
  env -i \
    HOME="$TMP" PATH=/usr/bin:/bin \
    TINA4_AGENT_PORT="$PORT" TINA4_NO_BROWSER=true \
    TINA4_PROJECTS_ROOT="$TMP/projects" TINA4_STATE_DIR="$TMP/state" \
    "$@" \
    unshare -rn "$HERE/inside-netns.sh" "$PORT" "$TREE"
  rm -rf "$TMP"
}

OUT_DEFAULT="$(run 'PRODUCTION DEFAULT -- no TINA4_HOST, no TINA4_DEBUG (what DISTRIBUTION.md ships)')"
echo "$OUT_DEFAULT"
OUT_PINNED="$(run 'WITH TINA4_HOST=127.0.0.1 -- the standing mitigation in this workspace' TINA4_HOST=127.0.0.1)"
echo "$OUT_PINNED"

echo ""
echo "=== verdict ==="
BIND="$(echo "$OUT_DEFAULT" | awk '/^BIND/{print $2}')"
OFF="$(echo "$OUT_DEFAULT" | awk '/^OFF-LOOP/{print $2}')"
echo "default bind        ${BIND:-<none: the server never came up>}"
echo "off-loopback reply  ${OFF:-<none>}"
case "$BIND" in
  0.0.0.0:*|'*:'*|'[::]:'*)
    echo "DEFECT REPRODUCED -- production default listens on every interface, and answered"
    echo "an unauthenticated request from a non-loopback address. exit 1"
    exit 1 ;;
  127.0.0.1:*)
    echo "binds loopback by default. exit 0"
    exit 0 ;;
  *)
    echo "INCONCLUSIVE -- could not read a bind address. exit 2"
    exit 2 ;;
esac
