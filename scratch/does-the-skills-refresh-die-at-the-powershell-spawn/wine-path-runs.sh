#!/usr/bin/env bash
# Run 5B, done properly: a live wineserver holds the registry in memory, so editing
# system.reg underneath one changes nothing.  Kill it first, then edit, then PROVE
# the running process's PATH really lost the directory before believing any result.
set -u
W=/var/home/work/.cache/tina4-wine
PFX=$W/pfx
SYS=$PFX/drive_c/windows/system32
STUB=${STUB:?path to the built curl.exe stand-in}
STOCK=$W/tina4-windows-amd64.exe
FIXED=$W/tina4-fixed.exe
OUT=$W/out; mkdir -p "$OUT"

run () { timeout 180 flatpak run --filesystem=$W --env=WINEPREFIX=$PFX \
           --command=wine com.usebottles.bottles "$@"; }
kill_server () { timeout 60 flatpak run --filesystem=$W --env=WINEPREFIX=$PFX \
           --command=wineserver com.usebottles.bottles -k >/dev/null 2>&1; sleep 2; }

restore () {
  # wineserver -k returns before the server has finished writing its in-memory
  # registry back out, and that write lands ON TOP of a restore done too early.
  # Wait for it, put the file back, then read the key to confirm it took.
  kill_server; sleep 5
  [ -f "$PFX/system.reg.away" ] && mv -f "$PFX/system.reg.away" "$PFX/system.reg"
  rm -f "$SYS/curl.exe"
  echo "  restored, PATH key names the directory: $(grep -c 'WindowsPowershell' "$PFX/system.reg")"
  return 0
}
trap restore EXIT

arm () { # $1 = label, $2 = exe
  run "$2" skills all >"$OUT/$1.out" 2>"$OUT/$1.err"
  echo "$?" >"$OUT/$1.code"
  printf '%-12s exit %-3s %4s bytes\n' "$1" "$(cat "$OUT/$1.code")" "$(wc -c <"$OUT/$1.out")"
}

cp "$STUB" "$SYS/curl.exe"
kill_server
cp "$PFX/system.reg" "$PFX/system.reg.away"
sed -i 's|;%SystemRoot%\\\\system32\\\\WindowsPowershell\\\\v1.0||' "$PFX/system.reg"
echo "  system.reg still names the directory: $(grep -c 'WindowsPowershell' "$PFX/system.reg")"

# The instrument check: what PATH does a process in this prefix actually get?
run "$PFX/drive_c/windows/system32/cmd.exe" /c "echo %PATH%" >"$OUT/PATH.out" 2>"$OUT/PATH.err"
echo "  PATH seen by a child:  $(tr -d '\r' <"$OUT/PATH.out" | tail -1)"
echo "  powershell.exe on disk: $([ -f "$SYS/WindowsPowerShell/v1.0/powershell.exe" ] && echo yes || echo NO)"

arm B2-stock "$STOCK"
arm B2-fixed "$FIXED"
