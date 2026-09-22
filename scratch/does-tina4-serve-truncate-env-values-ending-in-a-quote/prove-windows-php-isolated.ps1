param(
    [Parameter(Mandatory = $true)][string]$Bin,
    [Parameter(Mandatory = $true)][string]$PhpHome,
    [Parameter(Mandatory = $true)][string]$Mode
)
$ErrorActionPreference = "Stop"
$port = 7145
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 400

$work = "C:\Users\mig\cli27\phpiso-$Mode"
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Path "$work\vendor","$work\bin","$work\Tina4" | Out-Null
Copy-Item "C:\Users\mig\cli27\php-wire\bin\tina4php" "$work\bin\tina4php"
Copy-Item "C:\Users\mig\cli27\php-wire\Tina4\DotEnv.php" "$work\Tina4\DotEnv.php"
Copy-Item "C:\Users\mig\cli27\php-wire\composer.json" "$work\composer.json"
$envText = "TINA4_CSP=`"default-src 'self'; form-action 'self'`"`r`nTINA4_PORT=$port`r`nTINA4_DEBUG=true`r`n"
[System.IO.File]::WriteAllText("$work\.env", $envText, (New-Object System.Text.UTF8Encoding $false))

$env:PATH = "$PhpHome;" + $env:PATH
foreach ($k in @("TINA4_CSP","TINA4_PORT")) { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
$env:TINA4_NO_BROWSER = "true"

$args = if ($Mode -eq "flag") { @("serve","-p","$port") } else { @("serve") }
Write-Host "CMD=$Bin $($args -join ' ')"
Write-Host "PHP=$(php -v | Select-Object -First 1)"
$p = Start-Process -FilePath $Bin -ArgumentList $args -WorkingDirectory $work -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "$work\out.log" -RedirectStandardError "$work\err.log"
$deadline = (Get-Date).AddSeconds(20)
while (-not (Test-Path "$work\dump.txt") -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 100 }
Start-Sleep -Milliseconds 500
Write-Host "----- dump -----"
if (Test-Path "$work\dump.txt") { Get-Content "$work\dump.txt" } else { Write-Host "(no dump)" }
Write-Host "----- curl -----"
try {
    $r = Invoke-WebRequest "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3
    Write-Host ("CSP=" + $r.Headers["Content-Security-Policy"])
} catch { Write-Host "curl-fail: $_" }
Write-Host "----- logs -----"
Get-Content "$work\out.log","$work\err.log" -ErrorAction SilentlyContinue
if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
