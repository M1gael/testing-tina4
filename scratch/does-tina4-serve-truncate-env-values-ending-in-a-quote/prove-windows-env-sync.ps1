# Prove tina4 env --sync keeps or eats trailing quotes. Windows.
# Exit 0 = every value survived two --sync runs (fix holds).
# Exit 1 = a value changed (defect still present, or a new break).
param(
    [Parameter(Mandatory = $true)]
    [string]$Bin
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $Bin)) {
    Write-Error "binary not found: $Bin"
    exit 2
}

$work = Join-Path $env:TEMP ("tina4-cli27-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work | Out-Null
Set-Location $work

# Same shapes as the Linux prove / the integration test. CRLF on purpose.
# .NET write so Windows PowerShell 5.1 does not prepend a UTF-8 BOM.
$seed = @"
TINA4_CSP="default-src 'self'; form-action 'self'"
PLAIN_TRAILING_SQ=form-action 'self'
SQ_WRAPPED='hello world'
DQ_WRAPPED="hello world"
ENDS_DQ='say "hi"'
QUOTED_EMPTY="''"
PADDED=" spaced "

"@
[System.IO.File]::WriteAllText((Join-Path $work ".env"), $seed, (New-Object System.Text.UTF8Encoding $false))

$expected = [ordered]@{
    TINA4_CSP          = "default-src 'self'; form-action 'self'"
    PLAIN_TRAILING_SQ  = "form-action 'self'"
    SQ_WRAPPED         = "hello world"
    DQ_WRAPPED         = "hello world"
    ENDS_DQ            = 'say "hi"'
    QUOTED_EMPTY       = "''"
    PADDED             = " spaced "
}

function Read-DotEnv([string]$path) {
    $map = @{}
    foreach ($raw in Get-Content -LiteralPath $path) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith("#")) { continue }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { continue }
        $key = $line.Substring(0, $eq).Trim()
        $value = $line.Substring($eq + 1).Trim()
        if ($value.Length -ge 2) {
            $first = $value[0]
            $last = $value[$value.Length - 1]
            if (($first -eq [char]34 -or $first -eq [char]39) -and $last -eq $first) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }
        $map[$key] = $value
    }
    return $map
}

Write-Host "BIN=$Bin"
Write-Host "CWD=$work"
& $Bin --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "binary would not print a version"
    exit 2
}

$failed = $false
foreach ($run in 1..2) {
    $out = & $Bin env --sync 2>&1
    Write-Host "--- --sync run $run exit=$LASTEXITCODE ---"
    Write-Host $out
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL: env --sync exited $LASTEXITCODE"
        $failed = $true
        break
    }
    $got = Read-DotEnv ".env"
    Write-Host "----- .env after run $run -----"
    Get-Content -LiteralPath ".env" | ForEach-Object { Write-Host $_ }
    foreach ($key in $expected.Keys) {
        $want = $expected[$key]
        $have = $got[$key]
        if ($have -cne $want) {
            Write-Host "FAIL run $run : $key"
            Write-Host "  want: [$want]"
            Write-Host "  got : [$have]"
            $failed = $true
        } else {
            Write-Host "ok   run $run : $key = [$have]"
        }
    }
}

Set-Location $env:TEMP
Remove-Item -LiteralPath $work -Recurse -Force
if ($failed) { exit 1 } else { Write-Host "PASS: two --sync runs left every value intact"; exit 0 }
