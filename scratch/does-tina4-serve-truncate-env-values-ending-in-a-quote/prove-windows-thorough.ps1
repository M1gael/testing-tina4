# Thorough Windows prove for tina4stack/tina4#27.
# Measures INHERIT (child getenv) and WIRE (HTTP CSP header), same port,
# with and without -p. Stock must still show the defect; fixed must not.
param(
    [Parameter(Mandatory = $true)][string]$Stock,
    [Parameter(Mandatory = $true)][string]$Fixed,
    [Parameter(Mandatory = $true)][string]$Stub
)

$ErrorActionPreference = "Stop"
$wantShort = "default-src 'self'; form-action 'self'"
$wantLong = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self'; worker-src 'self' blob:; form-action 'self'"
$port = 7145

function Sha256([string]$p) {
    (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
}

function Write-EnvFile([string]$dir, [string]$text, [string]$mode) {
    $path = Join-Path $dir ".env"
    switch ($mode) {
        "crlf" {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes(($text -replace "`n", "`r`n"))
            [System.IO.File]::WriteAllBytes($path, $bytes)
        }
        "lf" {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes(($text -replace "`r", ""))
            [System.IO.File]::WriteAllBytes($path, $bytes)
        }
        "bom" {
            $utf8bom = New-Object System.Text.UTF8Encoding $true
            [System.IO.File]::WriteAllText($path, ($text -replace "`n", "`r`n"), $utf8bom)
        }
        default { throw "unknown env mode $mode" }
    }
}

function Get-HeaderCsp([int]$p) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$p/" -UseBasicParsing -TimeoutSec 3
        return [string]$r.Headers["Content-Security-Policy"]
    } catch {
        return $null
    }
}

function Invoke-Case {
    param(
        [string]$Bin,
        [string]$Name,
        [string]$EnvText,
        [string]$EnvMode,
        [string[]]$ServeArgs,
        [hashtable]$ParentEnv,
        [string]$Launch
    )
    $work = Join-Path $env:TEMP ("t4-27-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $work | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $work ".venv\Scripts") | Out-Null
    Copy-Item $Stub (Join-Path $work ".venv\Scripts\python.exe")
    Set-Content (Join-Path $work "requirements.txt") "tina4_python`n" -Encoding ascii
    Set-Content (Join-Path $work "app.py") "" -Encoding ascii
    Write-EnvFile $work $EnvText $EnvMode

    $dump = Join-Path $work "dump.txt"
    $log = Join-Path $work "serve.log"
    $err = Join-Path $work "serve.err"

    $old = @{}
    foreach ($k in @("TINA4_CSP","TINA4_PORT","TINA4_NO_BROWSER","DUMP_TO","PLAIN_TRAILING_SQ")) {
        $old[$k] = [Environment]::GetEnvironmentVariable($k, "Process")
        [Environment]::SetEnvironmentVariable($k, $null, "Process")
    }
    [Environment]::SetEnvironmentVariable("TINA4_NO_BROWSER", "true", "Process")
    if ($ParentEnv) {
        foreach ($k in $ParentEnv.Keys) {
            [Environment]::SetEnvironmentVariable($k, $ParentEnv[$k], "Process")
        }
    }

    $argLine = (@("serve") + $ServeArgs) -join " "
    if ($Launch -eq "cmd") {
        $p = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "`"$Bin`" $argLine") `
            -WorkingDirectory $work -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput $log -RedirectStandardError $err
    } else {
        $p = Start-Process -FilePath $Bin -ArgumentList (@("serve") + $ServeArgs) `
            -WorkingDirectory $work -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput $log -RedirectStandardError $err
    }

    $deadline = (Get-Date).AddSeconds(20)
    $wire = $null
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $dump) {
            Start-Sleep -Milliseconds 200
            $wire = Get-HeaderCsp $port
            if ($wire) { break }
        }
        Start-Sleep -Milliseconds 150
    }
    if ($p -and -not $p.HasExited) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
    Get-Process -Name "python","tina4-stock","tina4-fixed","tina4" -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "$work*" } |
        Stop-Process -Force -ErrorAction SilentlyContinue

    $inherit = $null
    if (Test-Path $dump) {
        foreach ($line in Get-Content $dump) {
            if ($line.StartsWith("TINA4_CSP=")) { $inherit = $line.Substring(10) }
        }
    }

    foreach ($k in $old.Keys) {
        [Environment]::SetEnvironmentVariable($k, $old[$k], "Process")
    }
    $logTail = ""
    if (Test-Path $err) { $logTail = (Get-Content $err -Raw) }
    Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
    return [pscustomobject]@{
        Name = $Name
        Inherit = $inherit
        Wire = $wire
        Log = $logTail
    }
}

Write-Host "HOST=$env:COMPUTERNAME"
Write-Host (cmd /c ver)
Write-Host ("STOCK sha256 " + (Sha256 $Stock))
Write-Host ("FIXED sha256 " + (Sha256 $Fixed))
Write-Host ("STUB  sha256 " + (Sha256 $Stub))
& $Stock --version
& $Fixed --version
Write-Host ""

$shortEnv = @"
TINA4_CSP="default-src 'self'; form-action 'self'"
TINA4_PORT=$port
"@
$longEnv = @"
TINA4_CSP="$wantLong"
TINA4_PORT=$port
"@
$spacedEnv = @"
TINA4_CSP = "default-src 'self'; form-action 'self'"
TINA4_PORT = $port
"@
$exportEnv = @"
export TINA4_CSP="default-src 'self'; form-action 'self'"
TINA4_PORT=$port
"@

$rows = @()

function Add-Pair($name, $envText, $mode, $args, $parent, $launch) {
    $s = Invoke-Case -Bin $Stock -Name "stock/$name" -EnvText $envText -EnvMode $mode -ServeArgs $args -ParentEnv $parent -Launch $launch
    $f = Invoke-Case -Bin $Fixed -Name "fixed/$name" -EnvText $envText -EnvMode $mode -ServeArgs $args -ParentEnv $parent -Launch $launch
    $script:rows += $s
    $script:rows += $f
}

Add-Pair "default-crlf"          $shortEnv "crlf" @()              $null "ps"
Add-Pair "flag-p-same-port"      $shortEnv "crlf" @("-p","$port")  $null "ps"
Add-Pair "flag-port-long"        $shortEnv "crlf" @("--port","$port") $null "ps"
Add-Pair "default-lf"            $shortEnv "lf"   @()              $null "ps"
Add-Pair "default-bom"           $shortEnv "bom"  @()              $null "ps"
Add-Pair "default-cmd"           $shortEnv "crlf" @()              $null "cmd"
Add-Pair "default-spaces"        $spacedEnv "crlf" @()             $null "ps"
Add-Pair "default-export"        $exportEnv "crlf" @()             $null "ps"
Add-Pair "long-csp-default"      $longEnv "crlf" @()               $null "ps"
Add-Pair "long-csp-flag-p"       $longEnv "crlf" @("-p","$port")   $null "ps"
Add-Pair "parent-preset-default" $shortEnv "crlf" @() (@{ TINA4_CSP = "preset-from-parent" }) "ps"

Write-Host ("{0,-32} {1,-42} {2}" -f "CASE", "INHERIT", "WIRE")
Write-Host ("-" * 110)
foreach ($r in $rows) {
    $inh = if ($null -eq $r.Inherit) { "<none>" } else { $r.Inherit }
    $w = if ($null -eq $r.Wire) { "<none>" } else { $r.Wire }
    if ($inh.Length -gt 40) { $inh = $inh.Substring($inh.Length - 40) }
    if ($w.Length -gt 40) { $w = $w.Substring($w.Length - 40) }
    Write-Host ("{0,-32} {1,-42} {2}" -f $r.Name, $inh, $w)
}

$fail = 0
function Expect($name, $field, $want) {
    $r = $script:rows | Where-Object { $_.Name -eq $name } | Select-Object -First 1
    $got = $r.$field
    if ($got -cne $want) {
        Write-Host "FAIL $name.$field"
        Write-Host "  want [$want]"
        Write-Host "  got  [$got]"
        $script:fail++
    } else {
        Write-Host "ok   $name.$field"
    }
}

Write-Host ""
Write-Host "## expectations (Chanelle's table + Windows axes)"
Expect "stock/default-crlf" "Wire" ($wantShort.TrimEnd("'"))
Expect "stock/default-crlf" "Inherit" ($wantShort.TrimEnd("'"))
Expect "fixed/default-crlf" "Wire" $wantShort
Expect "fixed/default-crlf" "Inherit" $wantShort
Expect "stock/flag-p-same-port" "Inherit" "<unset>"
Expect "stock/flag-p-same-port" "Wire" $wantShort
Expect "fixed/flag-p-same-port" "Inherit" "<unset>"
Expect "fixed/flag-p-same-port" "Wire" $wantShort
Expect "stock/flag-port-long" "Wire" $wantShort
Expect "fixed/flag-port-long" "Wire" $wantShort
Expect "stock/default-lf" "Wire" ($wantShort.TrimEnd("'"))
Expect "fixed/default-lf" "Wire" $wantShort
Expect "stock/default-cmd" "Wire" ($wantShort.TrimEnd("'"))
Expect "fixed/default-cmd" "Wire" $wantShort
Expect "stock/long-csp-default" "Wire" ($wantLong.TrimEnd("'"))
Expect "fixed/long-csp-default" "Wire" $wantLong
Expect "stock/long-csp-flag-p" "Wire" $wantLong
Expect "fixed/long-csp-flag-p" "Wire" $wantLong
Expect "stock/parent-preset-default" "Wire" "preset-from-parent"
Expect "fixed/parent-preset-default" "Wire" "preset-from-parent"

Write-Host ""
if ($fail -gt 0) {
    Write-Host "OVERALL: $fail expectation(s) failed"
    exit 1
}
Write-Host "OVERALL: every written expectation held"
exit 0
