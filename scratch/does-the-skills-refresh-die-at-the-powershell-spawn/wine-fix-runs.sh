#!/usr/bin/env bash
# Run 5: does the FIX change what Windows prints, in the two cells that matter?
#
#   A  powershell.exe absent          stock prints no cause; fixed must print one.
#   B  powershell.exe present, but the v1.0 directory removed from the registry
#      PATH so a bare name cannot resolve    stock must skip; fixed must run it.
#
# Everything is done inside a throwaway copy of the prefix state: system32 gets a
# curl.exe stand-in (so the download succeeds and the run reaches the spawn), and
# every file and registry edit is put back before the script exits.
set -u
W=/var/home/work/.cache/tina4-wine
PFX=$W/pfx
SYS=$PFX/drive_c/windows/system32
PS=$SYS/WindowsPowerShell/v1.0/powershell.exe
STUB=${STUB:?path to the built curl.exe stand-in}
STOCK=$W/tina4-windows-amd64.exe
FIXED=$W/tina4-fixed.exe
OUT=$W/out; mkdir -p "$OUT"

wine () { # $1 = exe, rest = args
  timeout 180 flatpak run --filesystem=$W --env=WINEPREFIX=$PFX \
    --command=wine com.usebottles.bottles "$@"
}

restore () {
  [ -f "$PS.away" ] && mv -f "$PS.away" "$PS"
  rm -f "$SYS/curl.exe"
  [ -f "$PFX/system.reg.away" ] && mv -f "$PFX/system.reg.away" "$PFX/system.reg"
  return 0
}
trap restore EXIT

arm () { # $1 = label, $2 = exe
  rm -rf "$PFX/drive_c/users/$USER/Temp" 2>/dev/null
  wine "$2" skills all >"$OUT/$1.out" 2>"$OUT/$1.err"
  echo "$?" >"$OUT/$1.code"
  printf '%-12s exit %-3s %4s bytes\n' "$1" "$(cat "$OUT/$1.code")" "$(wc -c <"$OUT/$1.out")"
}

cp "$STUB" "$SYS/curl.exe"

echo "== A: powershell.exe absent =="
mv -f "$PS" "$PS.away"
arm A-stock "$STOCK"
arm A-fixed "$FIXED"
mv -f "$PS.away" "$PS"

echo "== B: powershell.exe present, its directory off the registry PATH =="
cp "$PFX/system.reg" "$PFX/system.reg.away"
sed -i 's|;%SystemRoot%\\\\system32\\\\WindowsPowershell\\\\v1.0||' "$PFX/system.reg"
grep -c 'WindowsPowershell' "$PFX/system.reg" | sed 's/^/  PATH still names the directory: /'
arm B-stock "$STOCK"
arm B-fixed "$FIXED"
mv -f "$PFX/system.reg.away" "$PFX/system.reg"

rm -f "$SYS/curl.exe"
