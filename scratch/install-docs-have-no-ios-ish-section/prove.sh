#!/bin/sh
# prove.sh: does a docs tree cover iOS (iSH) install, and is its hosted installer the CLI tip's?
# Usage: DOCS=<docs tree root> [CLI=<tina4 CLI tree>] prove.sh   rc!=0 when coverage is missing.
# Scope: every .md under $DOCS/docs except docs/public (skills/installer copies) and node_modules.
set -u
CLI=${CLI:-$HOME/.cache/tina4-worktrees/verify-1029/fw-cli}
cd "$DOCS/docs" || exit 2
n=$(find . -name '*.md' -not -path './public/*' -not -path '*/node_modules/*' | wc -l)
hits=$(find . -name '*.md' -not -path './public/*' -not -path '*/node_modules/*' -print0 | xargs -0 grep -lE '\biSH\b' | sort | tr '\n' ' ')
echo "md files scanned: $n; files naming iSH: ${hits:-none}"
need=0; have=0
for f in ./index.md ./get-started/index.md ./general/cli.md ./install-security.md; do
  need=$((need+1)); if grep -qE '\biSH\b' "$f"; then have=$((have+1)); else echo "  no iSH in $f"; fi; done
grep -q 'latest-stable/community > /etc/apk/repositories' ./get-started/index.md && sw=1 || sw=0
# The index iOS tab must carry the switch itself: App Store iSH (Alpine 3.14) otherwise gets Python 3.9 / Ruby 2.7.
sed -n '/== iOS (iSH/,/^```$/p' ./index.md | grep -q 'latest-stable/community > /etc/apk/repositories' && tab=1 || tab=0
grep -qE 'PHP and Node.js (projects )?are not available' ./get-started/index.md && lang=1 || lang=0
cmp -s public/install.sh "$CLI/install.sh" && sh=equal || sh=DIFFERS
cmp -s public/install.ps1 "$CLI/install.ps1" && ps=equal || ps=DIFFERS
echo "VERDICT pages_with_iSH=$have/$need apk_switch=$sw tab_switch=$tab languages_stated=$lang install.sh=$sh install.ps1=$ps(out of scope)"
[ $have -eq $need ] && [ $sw -eq 1 ] && [ $tab -eq 1 ] && [ $lang -eq 1 ] && [ $sh = equal ]
