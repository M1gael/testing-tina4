#!/bin/sh
# build.sh: tina4press build of a docs tree, then check the iSH tab and sections render.
# Usage: DOCS=<docs tree root> build.sh   (tree is copied; node_modules from verify-1028/nm)
# Prints VERDICT; rc!=0 when the build fails or any of the 5 renders is missing.
set -u
NM=$HOME/.cache/tina4-worktrees/verify-1028/nm/node_modules
B=$HOME/.cache/tina4-worktrees/verify-1029/dsite03/build-$(basename "$DOCS")
rm -rf "$B"; cp -a "$DOCS" "$B"; ln -s "$NM" "$B/node_modules"
(cd "$B" && timeout 600 ./node_modules/.bin/tina4press build . > "$B.log" 2>&1); rc=$?
echo "build rc=$rc $(grep -o 'built [0-9]* page(s)' "$B.log")"
OUT=$B/docs/.vitepress/dist
miss=0
chk() { if grep -q "$2" "$OUT/$1" 2>/dev/null; then echo "  ok   $1: $2"; else echo "  MISS $1: $2"; miss=$((miss+1)); fi; }
chk index.html 'class="tp-tab">iOS (iSH, experimental)</button>'
chk get-started/index.html '<strong>iOS (iSH, experimental):</strong>'
chk get-started/index.html 'etc/apk/repositories'
chk index.html 'apk upgrade --available'
chk general/cli/index.html 'On iOS, inside'
chk install-security/index.html "iSH's root user is the app's sandbox"
echo "VERDICT build_rc=$rc missing=$miss/6"
[ -n "${KEEP:-}" ] || rm -rf "$B"; [ $rc -eq 0 ] && [ $miss -eq 0 ]
