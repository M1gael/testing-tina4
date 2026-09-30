# Windows twin of ../prove.sh: does tina4-php lose the native session under `tina4 serve`?
#
# Expects, under $Root (default C:\Users\mig\php253):
#   tina4.exe       the tina4 CLI (Windows build)
#   composer.phar   Composer
#   app\            the proof app (index.php, src\routes\session.php)
# and PHP at $Php. Each version is installed from Packagist into $Root\v\<version>.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File prove.ps1
#   powershell ... -File prove.ps1 -Versions 3.13.141 -Modes cli,phps -Prestart
#   -ObApp makes app\index.php call ob_start() and leave the buffer open.
#
# Modes: cli      `tina4 serve`
#        direct   `php vendor\bin\tina4php serve` (TINA4_OVERRIDE_CLIENT=true)
#        buffered direct with `php -d output_buffering=4096` (an instrument)
#        phps     `php -S`
# Windows has no pcntl_fork, so the socket server is always serial here; each cell
# prints the pid of two /probe calls to show it.
#
# Exit 0: every stock socket-server cell (cli, direct) kept the native session per
# client through /set and /regen. Exit 1: at least one did not. Exit 2: nothing measured.
param(
  [string[]]$Versions = @('3.13.138', '3.13.139', '3.13.141'),
  [string[]]$Modes = @('cli', 'direct', 'buffered', 'phps'),
  [string]$Root = 'C:\Users\mig\php253',
  [string]$Php = 'C:\Users\mig\cli27\php\php.exe',
  [switch]$Prestart,
  [switch]$ObApp,
  [string]$DebugMode = 'true'
)
$ErrorActionPreference = 'Continue'
# `powershell -File` hands `-Modes cli,phps` over as ONE string; split it here.
$Versions = @($Versions | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Modes = @($Modes | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$tmp = Join-Path $Root 'tmp'; New-Item -ItemType Directory -Force $tmp | Out-Null
$logs = Join-Path $Root 'logs'; New-Item -ItemType Directory -Force $logs | Out-Null
$env:PATH = (Split-Path $Php) + ';' + $env:PATH
$env:TINA4_SECRET = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
$env:TINA4_DEBUG = $DebugMode
$env:TINA4_NO_BROWSER = 'true'
if ($Prestart) { $env:PRESTART = '1' } else { Remove-Item Env:PRESTART -ErrorAction SilentlyContinue }
if ($ObApp) { $env:OB_APP = '1' } else { Remove-Item Env:OB_APP -ErrorAction SilentlyContinue }
$port = 17870; $status = 0; $cells = 0; $bad = 0

function Field([string]$body, [string]$name) {
  try { $d = $body | ConvertFrom-Json } catch { return '?' }
  if ($null -eq $d) { return '?' }
  $v = $d.$name
  if ($null -eq $v) { return 'null' }
  $s = [string]$v
  if ($name -eq 'id' -and $s.Length -gt 6) { return $s.Substring(0, 6) }
  return $s
}
function Sid([string]$hfile, [string]$ck) {
  $m = Select-String -Path $hfile -Pattern "^set-cookie: $ck=([^;]*)"
  if (-not $m) { return '-' }
  ($m | ForEach-Object { $x = $_.Matches[0].Groups[1].Value; $x.Substring(0, [Math]::Min(6, $x.Length)) }) -join ','
}
function Flow([int]$p, [string]$route, [string]$first = 'GET:/whoami', [string]$who = '/whoami', [string]$ck = 'PHPSESSID') {
  $u = "http://127.0.0.1:$p"; $jar = Join-Path $tmp 'jar'
  Remove-Item $jar -ErrorAction SilentlyContinue
  $fm, $fp = $first.Split(':', 2)
  $b1 = (& curl.exe -s -c $jar -D "$tmp\h1" -X $fm "$u$fp") -join "`n"
  $b2 = (& curl.exe -s -b $jar -c $jar -D "$tmp\h2" -X POST "$u$route") -join "`n"
  $b3 = (& curl.exe -s -b $jar -c $jar -D "$tmp\h3" "$u$who") -join "`n"
  $verdict = 'lost'; $shared = ''
  if ((Field $b3 'hit') -eq (Field $b2 'hit') -and (Field $b3 'id') -eq (Field $b2 'id')) { $verdict = 'kept' }
  $h1 = Field $b1 'hit'
  if ($fm -eq 'GET' -and $h1 -ne 'null' -and $h1 -ne '?') { $shared = "  SHARED: fresh client saw hit=$h1" }
  # Write-Host, not Write-Output: anything written to the pipeline would become part of
  # this function's return value and hide the line from the log.
  Write-Host ('{0,-11} 1 {1}/{2} set:{3} | 2 {4}/{5} set:{6} | 3 {7}/{8} set:{9}  {10}{11}' -f $route,
    (Field $b1 'id'), $h1, (Sid "$tmp\h1" $ck),
    (Field $b2 'id'), (Field $b2 'hit'), (Sid "$tmp\h2" $ck),
    (Field $b3 'id'), (Field $b3 'hit'), (Sid "$tmp\h3" $ck), $verdict, $shared)
  return ($verdict -eq 'kept' -and $shared -eq '')
}
function Stop-Cell($proc, [int]$p) {
  & taskkill.exe /T /F /PID $proc.Id 2>&1 | Out-Null
  foreach ($i in 1..40) {
    $l = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $p -or $_.LocalPort -eq ($p + 1000) }
    if (-not $l) { return }
    Start-Sleep -Milliseconds 250
  }
  "WARN: port $p still bound after stop" | Write-Output
}

"CLI: $(& (Join-Path $Root 'tina4.exe') --version) / PHP $(& $Php -r 'echo PHP_VERSION;') / $([Environment]::OSVersion.VersionString) / debug=$DebugMode / prestart=$([int][bool]$Prestart) / ob_app=$([int][bool]$ObApp)" | Write-Output
foreach ($v in $Versions) {
  $proj = Join-Path $Root "v\$v"
  $have = ''
  if (Test-Path "$proj\vendor\composer\installed.json") { $have = (& $Php "$Root\composer.phar" show tina4stack/tina4php --working-dir $proj 2>$null | Select-String '^versions' | ForEach-Object { ($_ -split '\s+')[-1] }) }
  if ($have -ne $v) {
    Remove-Item -Recurse -Force $proj -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $proj | Out-Null
    Set-Content -Path "$proj\composer.json" -Value ('{"require": {"tina4stack/tina4php": "' + $v + '"}, "config": {"preferred-install": "dist"}}') -Encoding Ascii
    & $Php "$Root\composer.phar" install --no-interaction --no-progress -q --working-dir $proj
    if ($LASTEXITCODE -ne 0) { "SKIP: composer install $v failed" | Write-Output; exit 2 }
  }
  Copy-Item -Recurse -Force "$Root\app\*" $proj
  foreach ($m in $Modes) {
    Remove-Item -Recurse -Force "$proj\data\sessions-php", "$proj\data\sessions", "$proj\data\sessions-app" -ErrorAction SilentlyContinue
    $port++
    $log = Join-Path $logs "$v-$m"
    $srv = @('serve', '--host', '127.0.0.1', '--port', "$port", '--no-browser', '--no-reload')
    Remove-Item Env:TINA4_OVERRIDE_CLIENT -ErrorAction SilentlyContinue
    switch ($m) {
      'cli'      { $exe = Join-Path $Root 'tina4.exe'; $argv = $srv }
      'direct'   { $env:TINA4_OVERRIDE_CLIENT = 'true'; $exe = $Php; $argv = @('vendor\bin\tina4php') + $srv }
      'buffered' { $env:TINA4_OVERRIDE_CLIENT = 'true'; $exe = $Php; $argv = @('-d', 'output_buffering=4096', 'vendor\bin\tina4php') + $srv }
      'phps'     { $exe = $Php; $argv = @('-S', "127.0.0.1:$port", '-t', '.', 'index.php') }
    }
    $proc = Start-Process -FilePath $exe -ArgumentList $argv -WorkingDirectory $proj -NoNewWindow -PassThru `
      -RedirectStandardOutput "$log.out" -RedirectStandardError "$log.err"
    $up = $false
    foreach ($i in 1..80) { if ((& curl.exe -s -o NUL -w '%{http_code}' "http://127.0.0.1:$port/probe") -eq '200') { $up = $true; break }; Start-Sleep -Milliseconds 500 }
    if (-not $up) { "SKIP: $v $m never answered on $port"; Get-Content "$log.out", "$log.err" -Tail 5 -ErrorAction SilentlyContinue; Stop-Cell $proc $port; exit 2 }
    $probe = (& curl.exe -s "http://127.0.0.1:$port/probe") -join ''
    $pid2 = Field ((& curl.exe -s "http://127.0.0.1:$port/probe") -join '') 'pid'
    "== $v $m  probe: $probe  second-probe-pid: $pid2" | Write-Output
    $ok = $true
    if (-not (Flow $port '/set')) { $ok = $false }
    if (-not (Flow $port '/regen')) { $ok = $false }
    Flow $port '/regen-keep' | Out-Null
    Flow $port '/t-set' 'GET:/t-who' '/t-who' 'tina4_session' | Out-Null
    Flow $port '/t-regen' 'POST:/t-set' '/t-who' 'tina4_session' | Out-Null
    $n1 = @(Get-ChildItem "$proj\data\sessions-php" -ErrorAction SilentlyContinue).Count
    $n2 = @(Get-ChildItem "$proj\data\sessions-app" -ErrorAction SilentlyContinue).Count
    "   session files: native $n1, app-started $n2" | Write-Output
    if ($m -eq 'cli' -or $m -eq 'direct') { $cells++; if (-not $ok) { $bad++; $status = 1 } }
    Stop-Cell $proc $port
  }
}
"native `$_SESSION not kept per client (/set or /regen) in $bad of $cells stock socket-server cells" | Write-Output
exit $status
