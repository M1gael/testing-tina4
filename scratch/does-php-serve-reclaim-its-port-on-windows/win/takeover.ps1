# On the Windows guest: does `tina4php serve` really reclaim its port from a stale Tina4 dev
# server? PortTakeover::killPid() falls back to exec("kill -15 <pid>") without posix_kill,
# and Windows has no `kill`.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File takeover.ps1
param(
  [string]$Root = 'C:\Users\mig\fix-serve-native-session',
  [string]$Php = 'C:\Users\mig\cli27\php\php.exe',
  [int]$Port = 17990
)
$ErrorActionPreference = 'Continue'
$tree = Join-Path $Root 'tree'
$app = Join-Path $Root 'takeover-app'
Remove-Item -Recurse -Force $app -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$app\src\routes" | Out-Null
$autoload = (Join-Path $tree 'vendor\autoload.php') -replace '\\', '/'
Set-Content -Path "$app\index.php" -Encoding Ascii -Value @"
<?php
require_once '$autoload';
`$app = new \Tina4\App(basePath: __DIR__);
`$app->handle();
"@
Set-Content -Path "$app\src\routes\pid.php" -Encoding Ascii -Value @'
<?php
\Tina4\Router::get('/pid', fn ($request, $response) => $response(['pid' => getmypid()]));
'@
$env:PATH = (Split-Path $Php) + ';' + $env:PATH
$env:TINA4_DEBUG = 'true'
$env:TINA4_NO_BROWSER = 'true'
$env:TINA4_OVERRIDE_CLIENT = 'true'
$env:TINA4_AUTO_MIGRATE = 'false'
$env:TINA4_SECRET = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
"PHP $(& $Php -r 'echo PHP_VERSION;') / $([Environment]::OSVersion.VersionString) / posix_kill: $(& $Php -r 'var_export(function_exists(''posix_kill''));')"
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { "SKIP: port $Port is busy"; exit 2 }

function Start-Serve([string]$name) {
  Start-Process -FilePath $Php -ArgumentList @("$tree\bin\tina4php", 'serve', '--managed', '--host', '127.0.0.1', '--port', "$Port", '--no-browser') `
    -WorkingDirectory $app -NoNewWindow -PassThru -RedirectStandardOutput "$app\$name.out" -RedirectStandardError "$app\$name.err"
}
function Pid-Answering { try { ((& curl.exe -s --max-time 2 "http://127.0.0.1:$Port/pid") | ConvertFrom-Json).pid } catch { $null } }

$stale = Start-Serve 'stale'
foreach ($i in 1..40) { if (Pid-Answering) { break }; Start-Sleep -Milliseconds 250 }
"stale server: process $($stale.Id), answering as pid $(Pid-Answering)"
$pidfiles = Get-ChildItem -Recurse -Force $app, $env:TEMP -Filter "*$Port*" -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -ExpandProperty FullName
"pid files naming the port: $($pidfiles -join ', ')"

$second = Start-Serve 'second'
Start-Sleep -Seconds 8
"after 8 s: stale running=$(-not $stale.HasExited)  second running=$(-not $second.HasExited)  answering pid=$(Pid-Answering)"
"-- second server's console:"
Get-Content "$app\second.out", "$app\second.err" -ErrorAction SilentlyContinue | Select-Object -First 30
"-- listeners on ${Port}:"
Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | ForEach-Object { "  $($_.LocalAddress):$($_.LocalPort) pid $($_.OwningProcess)" }

foreach ($p in @($stale, $second)) { & taskkill.exe /T /F /PID $p.Id 2>&1 | Out-Null }
Start-Sleep -Seconds 1
"left listening on $Port afterwards: $(@(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue).Count)"
