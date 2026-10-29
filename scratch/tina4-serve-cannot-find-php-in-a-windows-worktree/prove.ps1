# Reproduces tina4#120: tina4 serve (php) in a normal checkout vs a linked git worktree.
param([string]$Tina4 = 'tina4')
$T = 'C:\Users\mig\t120'
$env:PATH = "C:\Users\mig\cli27\php;$T\git\cmd;$T\tools;" + $env:PATH
$R = "$T\repo"; $W = "$T\wt"
if (!(Test-Path "$R\public_html\vendor")) {
  Remove-Item -Recurse -Force $R,$W -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force $R | Out-Null; Set-Location $R
  & git init -q; & git config user.email t@t; & git config user.name t
  'n' | & $Tina4 init php public_html *> "$T\init.log"
  Set-Location "$R\public_html"; if (!(Test-Path vendor)) { & composer install -q 2>&1 | Out-Null }
  Set-Location $R; & git add -A 2>$null; & git commit -qm base
  & git worktree add -q $W -b wt 2>&1
  Set-Location "$W\public_html"; & composer install -q 2>&1 | Out-Null
}
function Serve($dir, $port) {
  Set-Location $dir
  $o = "$T\serve-$port.log"
  $p = Start-Process -FilePath (Get-Command $Tina4).Source -ArgumentList "serve --port $port --no-browser" -RedirectStandardOutput $o -RedirectStandardError "$o.err" -PassThru -NoNewWindow
  Start-Sleep 15
  try { $code = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$port/" -TimeoutSec 5).StatusCode } catch { $code = "ERR " + $_.Exception.Message }
  & taskkill /T /F /PID $p.Id 2>&1 | Out-Null
  "=== $dir  (http: $code)"; Get-Content $o,"$o.err" | Select-String -Pattern 'php|spawn|Fail|not found|Starting|error' | Select -First 8 | % { "  " + $_.Line }
}
Serve "$R\public_html" 7411
Serve "$W\public_html" 7412
"vendor bin (wt): " + ((Get-ChildItem "$W\public_html\vendor\bin" -Name) -join ' ')
