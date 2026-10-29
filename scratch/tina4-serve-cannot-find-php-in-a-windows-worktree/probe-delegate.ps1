# Delegated subcommand (`tina4 routes` hands off to the php CLI) with php reachable only via php.bat.
$T = 'C:\Users\mig\t120'; $PHPDIR = 'C:\Users\mig\cli27\php'
New-Item -ItemType Directory -Force "$T\shim" | Out-Null; Set-Content "$T\shim\php.bat" "@`"$PHPDIR\php.exe`" %*" -Encoding ASCII
$env:PATH = "$T\shim;$T\git\cmd;$T\tools;" + $env:PATH
Set-Location "$T\wt\public_html"
foreach ($exe in 'tina4-stock.exe','tina4-fixed.exe') {
  $out = & "$T\tools\$exe" routes 2>&1 | Out-String
  "=== $exe routes: exit $LASTEXITCODE"; ($out -split "`n" | Select-String 'not found|Failed|GET|route' | Select -First 2) | % { "  " + $_.Line.Trim() }
}
Remove-Item -Recurse -Force "$T\shim"
