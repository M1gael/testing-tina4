#!/usr/bin/env bash
#   TREE_ND=<tina4-nodejs source tree, node_modules installed> ./prove.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${TREE_ND:?set TREE_ND to a tina4-nodejs tree}"
NODEBIN=$(dirname "$(readlink -f "$(command -v node)")")
echo "tree: $(git -C "$TREE_ND" rev-parse --short HEAD) ($(git -C "$TREE_ND" describe --tags 2>/dev/null)); node $(node --version)"
env -i HOME="${TMPDIR:-/tmp}" PATH="$NODEBIN:/usr/bin:/bin" node --no-warnings --import "file://$TREE_ND/node_modules/tsx/dist/loader.mjs" "$HERE/check.mts" "$TREE_ND"
