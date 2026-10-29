# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File run-installer.ps1 <installer.ps1>
# Runs an installer the way `irm ... | iex` does (script text through iex), into a
# throwaway LOCALAPPDATA, and puts the user PATH back afterwards. iex runs the
# installer in THIS scope, so harness variables must not share its names ($tmp).
param([string]$Installer)
$core = (Invoke-RestMethod https://api.github.com/rate_limit).resources.core
Write-Output "api remaining: $($core.remaining)"
$savedPath = [Environment]::GetEnvironmentVariable("Path", "User")
$savedLad = $env:LOCALAPPDATA
$harnessDir = Join-Path $env:TEMP ("t4inst-" + [IO.Path]::GetRandomFileName())
New-Item -ItemType Directory $harnessDir | Out-Null
$env:LOCALAPPDATA = $harnessDir
$result = "FAIL"
try {
    $text = Get-Content -Raw $Installer
    Invoke-Expression $text
} catch {
    Write-Output "threw: $($_.Exception.Message)"
} finally {
    $env:LOCALAPPDATA = $savedLad
    [Environment]::SetEnvironmentVariable("Path", $savedPath, "User")
}
$exe = Join-Path $harnessDir "tina4\tina4.exe"
if (Test-Path $exe) { $result = "installed: " + (& $exe --version) }
Write-Output "RESULT $result"
Remove-Item -Recurse -Force $harnessDir
