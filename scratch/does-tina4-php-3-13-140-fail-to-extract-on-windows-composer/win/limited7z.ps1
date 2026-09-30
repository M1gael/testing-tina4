# Run a cmd line in mig's desktop session with the UAC-FILTERED (medium) token, the one an
# ordinary terminal such as PhpStorm's gets. Waits for the rc= line, prints the log.
param([string]$Label, [string]$CmdLine)
$root = 'C:\Users\mig\php7z'
$log = "$root\$Label.log"; Remove-Item $log -ErrorAction SilentlyContinue
$bat = "$root\$Label.cmd"
Set-Content $bat -Encoding ascii -Value ("@echo off`r`nsetlocal enabledelayedexpansion`r`n" +
  "(whoami /groups | findstr /c:`"Mandatory Level`") > `"$log`" 2>&1`r`n" +
  "(whoami /priv | findstr SeCreateSymbolicLink) >> `"$log`" 2>&1`r`n" +
  "echo privilege-line-count follows >> `"$log`"`r`n" +
  "$CmdLine >> `"$log`" 2>&1`r`n" +
  "echo rc=!errorlevel! >> `"$log`"`r`n")
$name = "limited-$Label"
Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"$bat`""
$p = New-ScheduledTaskPrincipal -UserId 'mig' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $a -Principal $p | Out-Null
Start-ScheduledTask -TaskName $name
$deadline = (Get-Date).AddMinutes(9)
do { Start-Sleep -Seconds 3 } until (((Test-Path $log) -and ((Get-Content $log -Raw) -match 'rc=\d+')) -or (Get-Date) -gt $deadline)
Unregister-ScheduledTask -TaskName $name -Confirm:$false
if (Test-Path $log) { Get-Content $log } else { "NO LOG" }
