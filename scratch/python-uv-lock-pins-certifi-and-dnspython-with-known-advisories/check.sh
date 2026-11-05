#!/usr/bin/env bash
# Usage: ./check.sh <path to uv.lock>
# Prints the locked certifi/dnspython versions and the OSV advisories that match them.
set -euo pipefail
for pkg in certifi dnspython; do
  ver=$(python3 -c "import tomllib,sys;print(next(p['version'] for p in tomllib.load(open(sys.argv[1],'rb'))['package'] if p['name']==sys.argv[2]))" "$1" "$pkg")
  ids=$(curl -sf -m 20 https://api.osv.dev/v1/query -d "{\"package\":{\"name\":\"$pkg\",\"ecosystem\":\"PyPI\"},\"version\":\"$ver\"}" \
    | python3 -c 'import json,sys;print(" ".join(v["id"] for v in json.load(sys.stdin).get("vulns",[])) or "none")') || ids="ERROR (OSV unreachable)"
  echo "$pkg $ver: $ids"
done
