param(
    [Parameter(Mandatory = $true)][string]$Bin,
    [Parameter(Mandatory = $true)][string]$Stub,
    [Parameter(Mandatory = $true)][string]$Mode
)
$ErrorActionPreference = "Stop"
$port = 7145
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400

$work = "C:\Users\mig\cli27\iso-$Mode"
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Path "$work\.venv\Scripts" | Out-Null
Copy-Item $Stub "$work\.venv\Scripts\python.exe"
Set-Content "$work\requirements.txt" "tina4_python`n" -Encoding ascii
Set-Content "$work\app.py" "" -Encoding ascii
$envText = "TINA4_CSP=`"default-src 'self'; form-action 'self'`"`r`nTINA4_PORT=$port`r`n"
[System.IO.File]::WriteAllText("$work\.env", $envText, (New-Object System.Text.UTF8Encoding $false))

foreach ($k in @("TINA4_CSP","TINA4_PORT","PLAIN_TRAILING_SQ")) {
    Remove-Item "Env:$k" -ErrorAction SilentlyContinue
}
$env:TINA4_NO_BROWSER = "true"

if ($Mode -eq "flag") {
    $args = @("serve", "-p", "$port")
} else {
    $args = @("serve")
}
Write-Host "CMD=$Bin $($args -join ' ')"
Write-Host "CWD=$work"
$p = Start-Process -FilePath $Bin -ArgumentList $args -WorkingDirectory $work -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "$work\out.log" -RedirectStandardError "$work\err.log"

$deadline = (Get-Date).AddSeconds(15)
while (-not (Test-Path "$work\dump.txt") -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 100 }
Start-Sleep -Milliseconds 400
Write-Host "----- dump -----"
if (Test-Path "$work\dump.txt") { Get-Content "$work\dump.txt" } else { Write-Host "(no dump)" }
Write-Host "----- curl header -----"
try {
    $r = Invoke-WebRequest "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3
    Write-Host ("CSP=" + $r.Headers["Content-Security-Policy"])
} catch {
    Write-Host "curl-fail: $_"
}
Write-Host "----- err.log -----"
if (Test-Path "$work\err.log") { Get-Content "$work\err.log" }
Write-Host "----- out.log -----"
if (Test-Path "$work\out.log") { Get-Content "$work\out.log" }
if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
