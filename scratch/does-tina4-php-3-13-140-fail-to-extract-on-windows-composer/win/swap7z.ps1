param([string]$Installer)
if (Test-Path 'C:\Program Files\7-Zip\Uninstall.exe') { $u = Start-Process 'C:\Program Files\7-Zip\Uninstall.exe' -ArgumentList '/S' -Wait -PassThru; "uninstall exit: " + $u.ExitCode; Start-Sleep 3 }
if ($Installer) { $p = Start-Process $Installer -ArgumentList '/S' -Wait -PassThru; "install exit: " + $p.ExitCode }
"7z.exe now: " + $(if (Test-Path 'C:\Program Files\7-Zip\7z.exe') { (Get-Item 'C:\Program Files\7-Zip\7z.exe').VersionInfo.ProductVersion } else { 'absent' })
