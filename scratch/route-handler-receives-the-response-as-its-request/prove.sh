#!/usr/bin/env bash
# Reproduce: a tina4-nodejs route handler whose first parameter is not literally
# named `req` or `request` receives the RESPONSE object in its place.
#
# Runs the released invokeRouteHandler bytes out of the installed package — no
# server, no network, no patched workspace.
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${TINA4_NODEJS_VERSION:-3.13.103}"

if [ ! -d node_modules/tina4-nodejs ]; then
  echo "installing tina4-nodejs@${VERSION} ..."
  npm install --silent --no-audit --no-fund "tina4-nodejs@${VERSION}"
fi

echo "tina4-nodejs $(node -p "require('./node_modules/tina4-nodejs/package.json').version")"
echo
node argprobe.mjs 2>/dev/null

cat <<'EOF'

VERDICT
  PASS lines  — the framework handed the handler (request, response).
  FAIL lines  — the framework handed the handler (response, response), or nothing.

  Any FAIL row is the defect: the request never reaches the handler, so
  `req.user`, `req.session` and `req.cookies` all read as unavailable inside a
  route the router has already authenticated.
EOF
