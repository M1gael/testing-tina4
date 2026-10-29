#!/usr/bin/env bash
# The hosted installer (tina4-documentation docs/public/install.sh, synced from
# tina4 main) run on a FRESH Termux against a local copy of a release that
# publishes tina4-android-amd64. Only the two GitHub URLs are rewritten
# (install-local-release.sh); detection, checksum and install are the real script.
# Pass: exit 0, binary at $PREFIX/bin/tina4, it runs, no sudo attempted.
# usage: installer-run.sh <tina4 android binary>
set -uo pipefail
BIN=$1
HERE=$(cd "$(dirname "$0")" && pwd)
R=$HERE/fake-release; OUT=$HERE/installer-out; mkdir -p "$OUT"
cp "$BIN" "$R/download/v9.9.9/tina4-android-amd64"
(cd "$R/download/v9.9.9" && sha256sum tina4-android-amd64 >SHA256SUMS)
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$R" >"$OUT/http.log" 2>&1 & srv=$!
sleep 1
/var/home/work/vm/termux-reset.sh >"$OUT/reset.txt" 2>&1 || /var/home/work/vm/termux-reset.sh >>"$OUT/reset.txt" 2>&1 || { echo "installer: RESET FAILED"; kill $srv; exit 2; }
scp -q -P 8022 "$HERE/install-local-release.sh" 127.0.0.1:install.sh
ssh -o BatchMode=yes -p 8022 127.0.0.1 'sh install.sh </dev/null; echo INSTALL_RC=$?; ls -l $PREFIX/bin/tina4; tina4 --version; echo WHICH=$(command -v tina4)' >"$OUT/install.txt" 2>&1
kill $srv
rc=$(grep -a -o 'INSTALL_RC=[0-9]*' "$OUT/install.txt" | cut -d= -f2)
which=$(grep -a -o 'WHICH=.*' "$OUT/install.txt" | cut -d= -f2)
ver=$(grep -a -c '^tina4 ' "$OUT/install.txt")
sudo=$(grep -a -c -i 'sudo' "$OUT/install.txt")
plat=$(grep -a 'Platform:' "$OUT/install.txt" | sed 's/^ *//')
ok=yes
[ "${rc:-x}" = 0 ] || ok=no; [ "$which" = /data/data/com.termux/files/usr/bin/tina4 ] || ok=no; [ "$ver" -ge 1 ] || ok=no; [ "$sudo" = 0 ] || ok=no
echo "installer: $( [ $ok = yes ] && echo PASS || echo FAIL )  rc=${rc:-none} installed_at=${which:-none} runs=$ver sudo_mentions=$sudo  [$plat]"
[ $ok = yes ]
