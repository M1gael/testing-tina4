#!/usr/bin/env bash
# Pyodide (node) half of the proof. Needs: node 22, npm, uv, a tina4-python checkout.
# Usage: ./prove.sh /path/to/tina4-python-checkout
set -euo pipefail
SRC=${1:?tina4-python checkout}; HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d)
(cd "$SRC" && uv build --wheel -q -o "$W/whl" .)
cd "$W" && npm init -y >/dev/null && npm i -q pyodide@314.0.7 >/dev/null
cp "$HERE/pyodide-run.mjs" "$W/"
node pyodide-run.mjs "$W"/whl/tina4_python-*.whl "$HERE/testclient.py" "$HERE/direct-await.py" 2>&1 | grep -E "TestClient|direct await"
