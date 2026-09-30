# Each 7-Zip build x {elevated ssh token, filtered desktop token} on one dist zip.
param([string]$Zip = 'C:\Users\mig\php7z\140.zip', [string]$Tag = '140')
$root = 'C:\Users\mig\php7z'
$exes = [ordered]@{ '7z-2603-installed' = 'C:\Program Files\7-Zip\7z.exe'; '7za-2603' = "$root\7za-2603.exe"; '7za-2501' = "$root\7za-2501.exe"; '7za-2409' = "$root\7za-2409.exe" }
function Summ([string]$label, [string]$log, [string]$out) {
  $t = if (Test-Path $log) { Get-Content $log -Raw } else { '' }
  $rc = [regex]::Match($t, 'rc=(\d+)').Groups[1].Value
  $links = @(Get-ChildItem -Force -Recurse $out -ErrorAction SilentlyContinue | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
  $confd = @(Get-ChildItem -Force -Recurse "$out\*\.confd_*" -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer }).Count
  $app = @(Get-ChildItem -Recurse "$out\*\Tina4\App.php" -ErrorAction SilentlyContinue).Count
  "{0,-34} rc={1} dangerous={2} no_privilege={3} symlinks={4} confd_entries={5} App.php={6}" -f $label, $rc,
    ([regex]::Matches($t, 'Dangerous link path')).Count, ([regex]::Matches($t, 'required privilege is not held')).Count, $links, $confd, $app
}
foreach ($k in $exes.Keys) {
  $exe = $exes[$k]
  foreach ($mode in 'elevated', 'filtered') {
    $label = "$Tag-$k-$mode"; $out = "$root\m-$label"; $log = "$root\$label.log"
    if (Test-Path $out) { cmd /c rmdir /s /q $out }
    $cmdline = "`"$exe`" x -bb0 -y `"$Zip`" `"-o$out`""
    if ($mode -eq 'elevated') { cmd /v:on /c "$cmdline > `"$log`" 2>&1 & echo rc=!errorlevel! >> `"$log`"" }
    else { & "$root\limited7z.ps1" -Label $label -CmdLine $cmdline | Out-Null }
    Summ $label $log $out
  }
}
