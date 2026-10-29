# Which environments produce "Could not spawn the php server: program not found"? Each case restored after.
param([string]$Where='wt', [string]$Exe='tina4.exe')
$T = 'C:\Users\mig\t120'; $W = "$T\$Where\public_html"; $PHPDIR = 'C:\Users\mig\cli27\php'
$base = "$T\git\cmd;$T\tools;" + $env:PATH
Copy-Item "$T\repo\public_html\.env" "$W\.env" -Force -ErrorAction SilentlyContinue
function Serve($label, $port) {
  Set-Location $W; $o = "$T\p-$port.log"
  $p = Start-Process -FilePath "$T\tools\$Exe" -ArgumentList "serve --port $port --no-browser" -RedirectStandardOutput $o -RedirectStandardError "$o.err" -PassThru -NoNewWindow
  Start-Sleep 12
  try { $c = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$port/" -TimeoutSec 5).StatusCode } catch { $c = 'no answer' }
  & taskkill /T /F /PID $p.Id 2>&1 | Out-Null
  $doc = (& "$T\tools\$Exe" doctor 2>&1 | Select-String 'PHP' | Select -First 1).Line
  "=== [$((Get-Location).Path)] $label  http=$c  doctor=[$($doc.Trim())]"
  Get-Content $o,"$o.err" | Select-String 'spawn|not found|Fail' | Select -First 2 | % { "  " + $_.Line.Trim() }
}
# A: baseline, php.exe dir on PATH
$env:PATH = "$PHPDIR;$base"; Serve 'A php.exe on PATH (worktree)' 7421
# B: php reachable only through a php.bat shim (Laravel Herd / some installers)
New-Item -ItemType Directory -Force "$T\shim" | Out-Null; Set-Content "$T\shim\php.bat" "@`"$PHPDIR\php.exe`" %*" -Encoding ASCII
$env:PATH = "$T\shim;$base"; Serve 'B only php.bat on PATH' 7422
# C: php.exe on PATH but vendor\bin\tina4php missing (only the .bat proxy)
$env:PATH = "$PHPDIR;$base"; Rename-Item "$W\vendor\bin\tina4php" 'tina4php.hidden'
Serve 'C vendor\bin\tina4php missing' 7423
Rename-Item "$W\vendor\bin\tina4php.hidden" 'tina4php'
Remove-Item -Recurse -Force "$T\shim"
# D: php.bat shim in a directory whose name has spaces
$sp = "$T\php shim dir"; New-Item -ItemType Directory -Force $sp | Out-Null; Set-Content "$sp\php.bat" "@`"$PHPDIR\php.exe`" %*" -Encoding ASCII
$env:PATH = "$sp;$base"; Serve 'D php.bat in a dir with spaces' 7424
Remove-Item -Recurse -Force $sp
# E: a php.cmd earlier on PATH than the real php.exe
New-Item -ItemType Directory -Force "$T\cmdfirst" | Out-Null; Set-Content "$T\cmdfirst\php.cmd" "@`"$PHPDIR\php.exe`" %*" -Encoding ASCII
$env:PATH = "$T\cmdfirst;$PHPDIR;$base"; Serve 'E php.cmd ahead of php.exe' 7425
Remove-Item -Recurse -Force "$T\cmdfirst"
