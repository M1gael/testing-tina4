# Prove tina4 serve (no -p) hands the child a truncated TINA4_CSP.
# That is the path in tina4stack/tina4#27 — not env --sync.
#
# A stub .venv\Scripts\python.exe dumps the inherited environment and exits.
# tina4 serve always passes --managed and, on Windows, prefers that venv
# interpreter, so no real Python is needed.
#
# Exit 0 = default-port serve truncated the value (defect still present).
# Exit 1 = value survived (fix holds) or the server never spawned.
param(
    [Parameter(Mandatory = $true)]
    [string]$Bin,
    [Parameter(Mandatory = $true)]
    [string]$Stub
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $Bin)) { Write-Error "binary not found: $Bin"; exit 2 }
if (-not (Test-Path -LiteralPath $Stub)) { Write-Error "stub not found: $Stub"; exit 2 }

$work = Join-Path $env:TEMP ("tina4-cli27-serve-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work | Out-Null
$venvPy = Join-Path $work ".venv\Scripts\python.exe"
New-Item -ItemType Directory -Path (Split-Path $venvPy) | Out-Null
Copy-Item -LiteralPath $Stub -Destination $venvPy
Set-Content -LiteralPath (Join-Path $work "requirements.txt") -Value "tina4_python`n" -Encoding ascii
Set-Content -LiteralPath (Join-Path $work "app.py") -Value "" -Encoding ascii

$seed = @"
TINA4_CSP="default-src 'self'; form-action 'self'"
PLAIN_TRAILING_SQ=form-action 'self'
SQ_WRAPPED='hello world'
DQ_WRAPPED="hello world"
ENDS_DQ='say "hi"'
QUOTED_EMPTY="''"
PADDED=" spaced "
TINA4_PORT=8919

"@
[System.IO.File]::WriteAllText((Join-Path $work ".env"), $seed, (New-Object System.Text.UTF8Encoding $false))

$want = "default-src 'self'; form-action 'self'"

function Invoke-Serve([string[]]$extra) {
    $dump = Join-Path $work ("dump" + ($extra -join "") + ".txt")
    if (Test-Path $dump) { Remove-Item $dump }
    $log = Join-Path $work ("serve" + ($extra -join "") + ".log")

    $env:TINA4_NO_BROWSER = "true"
    $env:DUMP_TO = $dump
    foreach ($k in @("TINA4_CSP","PLAIN_TRAILING_SQ","SQ_WRAPPED","DQ_WRAPPED","ENDS_DQ","QUOTED_EMPTY","PADDED")) {
        Remove-Item "Env:$k" -ErrorAction SilentlyContinue
    }

    $p = Start-Process -FilePath $Bin -ArgumentList (@("serve") + $extra) `
        -WorkingDirectory $work -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $log -RedirectStandardError "$log.err"

    $deadline = (Get-Date).AddSeconds(20)
    while (-not (Test-Path $dump) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 150
    }
    if (-not $p.HasExited) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 200
    }

    $got = $null
    if (Test-Path $dump) {
        foreach ($line in Get-Content -LiteralPath $dump) {
            if ($line.StartsWith("TINA4_CSP=")) { $got = $line.Substring(10) }
        }
    }
    return @{ Dump = $dump; Got = $got; Log = $log }
}

Write-Host "BIN=$Bin"
Write-Host "HOST=$env:COMPUTERNAME"
& $Bin --version

$default = Invoke-Serve @()
$explicit = Invoke-Serve @("-p","8795")

Write-Host "----- serve (no -p) dump -----"
if (Test-Path $default.Dump) { Get-Content $default.Dump } else { Write-Host "(no dump)" }
Write-Host "----- serve -p 8795 dump -----"
if (Test-Path $explicit.Dump) { Get-Content $explicit.Dump } else { Write-Host "(no dump)" }

Write-Host "## verdict"
Write-Host "    .env holds:            $want"
Write-Host "    serve (default port):  $($default.Got)"
Write-Host "    serve -p 8795:         $($explicit.Got)"

Set-Location $env:TEMP
Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue

if (-not $default.Got) {
    Write-Host "    NOT MEASURED: default-port serve never spawned the child."
    exit 2
}
if ($default.Got -cne $want) {
    Write-Host "    DEFECT PRESENT: default-port serve handed the child a truncated value."
    exit 0
}
Write-Host "    VALUE SURVIVED: default-port serve handed the child the CSP intact."
exit 1
