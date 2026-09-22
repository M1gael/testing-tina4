param(
    [Parameter(Mandatory = $true)][string]$Bin,
    [Parameter(Mandatory = $true)][string]$Stub,
    [Parameter(Mandatory = $true)][string]$Axis
)
$ErrorActionPreference = "Stop"
$port = 7145
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 300
$work = "C:\Users\mig\cli27\axis-$Axis"
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory "$work\.venv\Scripts" | Out-Null
Copy-Item $Stub "$work\.venv\Scripts\python.exe"
Set-Content "$work\requirements.txt" "tina4_python`n"
Set-Content "$work\app.py" ""
$short = "TINA4_CSP=`"default-src 'self'; form-action 'self'`"`nTINA4_PORT=$port`n"
$long = "TINA4_CSP=`"default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self'; worker-src 'self' blob:; form-action 'self'`"`nTINA4_PORT=$port`n"
switch ($Axis) {
    "lf" { [IO.File]::WriteAllBytes("$work\.env", [Text.Encoding]::UTF8.GetBytes($short.Replace("`r",""))) }
    "bom" {
        $b = New-Object Text.UTF8Encoding $true
        [IO.File]::WriteAllText("$work\.env", ($short -replace "`n","`r`n"), $b)
    }
    "long" { [IO.File]::WriteAllText("$work\.env", ($long -replace "`n","`r`n"), (New-Object Text.UTF8Encoding $false)) }
    "cmd" { [IO.File]::WriteAllText("$work\.env", ($short -replace "`n","`r`n"), (New-Object Text.UTF8Encoding $false)) }
    "preset" { [IO.File]::WriteAllText("$work\.env", ($short -replace "`n","`r`n"), (New-Object Text.UTF8Encoding $false)) }
    default { throw $Axis }
}
foreach ($k in @("TINA4_CSP","TINA4_PORT")) { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
$env:TINA4_NO_BROWSER = "true"
if ($Axis -eq "preset") { $env:TINA4_CSP = "preset-from-parent" }
if ($Axis -eq "cmd") {
    $p = Start-Process cmd.exe -ArgumentList @("/c", "`"$Bin`" serve") -WorkingDirectory $work -PassThru -WindowStyle Hidden -RedirectStandardOutput "$work\o.log" -RedirectStandardError "$work\e.log"
} else {
    $p = Start-Process $Bin -ArgumentList @("serve") -WorkingDirectory $work -PassThru -WindowStyle Hidden -RedirectStandardOutput "$work\o.log" -RedirectStandardError "$work\e.log"
}
$deadline = (Get-Date).AddSeconds(15)
while (-not (Test-Path "$work\dump.txt") -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 100 }
Start-Sleep -Milliseconds 300
Write-Host "AXIS=$Axis BIN=$Bin"
if (Test-Path "$work\dump.txt") { Write-Host (Get-Content "$work\dump.txt") } else { Write-Host "dump=<none>" }
try { $r = Invoke-WebRequest "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3; Write-Host ("WIRE=" + $r.Headers["Content-Security-Policy"]) } catch { Write-Host "WIRE=<none>" }
if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
if ($Axis -eq "preset") { Remove-Item Env:TINA4_CSP -ErrorAction SilentlyContinue }
