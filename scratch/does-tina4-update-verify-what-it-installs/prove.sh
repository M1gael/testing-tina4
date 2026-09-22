#!/usr/bin/env bash
# f-cli-06 — `tina4 update` installs whatever the downloader wrote, with no
# integrity check, although every release publishes SHA256SUMS and the project's
# own install.sh verifies against it.
#
# Green (exit 0) = the defect is present. Red (exit 1) = a check appeared; re-read the row.
#
# Method: put a stand-in `curl` first on PATH. The version check (no -o) is passed
# through to the real curl, so only the asset download is under our control. If the
# CLI verified anything, B2 would refuse the bytes we substitute.
set -u
SB="${SB:-$HOME/.cache/tina4-update-probe/prove06}"
OLD="${OLD:-v3.8.85}"   # any released tag older than latest, so the download path runs
rm -rf "$SB"; mkdir -p "$SB"/{bin,home,cwd,fakebin,empty}
curl -fsSL "https://github.com/tina4stack/tina4/releases/download/$OLD/tina4-linux-amd64" -o "$SB/old" || exit 2
chmod +x "$SB/old"
fail=0

echo "--- the release publishes a checksum for exactly this asset"
curl -fsSL "https://github.com/tina4stack/tina4/releases/download/$OLD/SHA256SUMS" -o "$SB/sums" || exit 2
grep -q 'tina4-linux-amd64' "$SB/sums" && echo "  ok   SHA256SUMS lists tina4-linux-amd64" || { echo "  FAIL no SHA256SUMS entry"; fail=1; }

echo "--- B1 control: real curl, the happy path must work and land the published bytes"
cp "$SB/old" "$SB/bin/tina4"; chmod +x "$SB/bin/tina4"
( cd "$SB/cwd" && env -i HOME="$SB/home" PATH="$SB/empty:/usr/bin:/bin" TERM=dumb "$SB/bin/tina4" update < /dev/null ) > "$SB/b1.log" 2>&1
NEWVER=$("$SB/bin/tina4" --version 2>/dev/null)
echo "  after B1: $NEWVER"
grep -q 'Updated tina4 CLI' "$SB/b1.log" && echo "  ok   update completed" || { echo "  FAIL update did not complete"; fail=1; }

echo "--- B2 attack: the downloader exits 0 having written bytes the server never sent"
cat > "$SB/fakebin/curl" <<'EOF'
#!/bin/sh
dest=""
for a in "$@"; do if [ "${prev:-}" = "-o" ]; then dest="$a"; fi; prev="$a"; done
[ -z "$dest" ] && exec /usr/bin/curl "$@"
echo "TOTALLY-NOT-A-TINA4-BINARY" > "$dest"
exit 0
EOF
chmod +x "$SB/fakebin/curl"
cp "$SB/old" "$SB/bin/tina4"; chmod +x "$SB/bin/tina4"
( cd "$SB/cwd" && env -i HOME="$SB/home" PATH="$SB/fakebin:/usr/bin:/bin" TERM=dumb "$SB/bin/tina4" update < /dev/null ) > "$SB/b2.log" 2>&1
RC=$?
SIZE=$(stat -c %s "$SB/bin/tina4")
echo "  exit=$RC  installed size=${SIZE}B  says: $(grep -o 'Updated tina4 CLI.*' "$SB/b2.log" || echo '(no success line)')"
if [ "$SIZE" -lt 1000 ] && grep -q 'Updated tina4 CLI' "$SB/b2.log" && [ "$RC" -eq 0 ]; then
  echo "  ok   27 bytes of text installed as the CLI, reported as success, exit 0"
else
  echo "  FAIL something rejected the substituted bytes"; fail=1
fi
[ -e "$SB/bin/tina4.old" ] && { echo "  note backup kept"; } || echo "  ok   the working binary's backup was deleted too — nothing to roll back to"

echo "--- B3: the downloader exits 0 having written nothing at all"
cat > "$SB/fakebin/curl" <<'EOF'
#!/bin/sh
dest=""
for a in "$@"; do if [ "${prev:-}" = "-o" ]; then dest="$a"; fi; prev="$a"; done
[ -z "$dest" ] && exec /usr/bin/curl "$@"
exit 0
EOF
chmod +x "$SB/fakebin/curl"
cp "$SB/old" "$SB/bin/tina4"; chmod +x "$SB/bin/tina4"
( cd "$SB/cwd" && env -i HOME="$SB/home" PATH="$SB/fakebin:/usr/bin:/bin" TERM=dumb "$SB/bin/tina4" update < /dev/null ) > "$SB/b3.log" 2>&1
RC=$?
echo "  exit=$RC  binary still: $("$SB/bin/tina4" --version 2>&1 | head -1)"
[ "$RC" -eq 0 ] && echo "  ok   a failed update exits 0 (separate defect, f-cli-23 shape, on Linux)" || echo "  note exits non-zero here"

[ $fail -eq 0 ] && { echo "VERDICT: defect present — nothing verifies what gets installed"; exit 0; } || { echo "VERDICT: behaviour differs — re-read the row"; exit 1; }
