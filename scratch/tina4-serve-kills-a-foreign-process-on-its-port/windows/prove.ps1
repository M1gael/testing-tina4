# CLI-FW-02 on Windows. Stock tina4.exe. A TcpListener is the holder; a TcpClient
# is only connected. Prints whether each is still alive after `tina4 serve`.
$ErrorActionPreference = 'Continue'
$bin = $args[0]
Write-Output ("HOST " + $env:COMPUTERNAME)
Write-Output (& $bin --version)

function Invoke-Case {
  param($Label, $Port, $PidMode, $How)
  $dir = Join-Path $env:TEMP "clifw02-$Port"
  if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
  New-Item -ItemType Directory -Path (Join-Path $dir 'data') | Out-Null
  Set-Content -Path (Join-Path $dir 'requirements.txt') -Value 'tina4_python' -Encoding ascii
  Set-Content -Path (Join-Path $dir 'app.py') -Value "import time`ntime.sleep(30)`n" -Encoding ascii
  if ($How -eq 'default') { Set-Content (Join-Path $dir '.env') "TINA4_PORT=$Port" -Encoding ascii }

  $listenCmd = "`$l = New-Object System.Net.Sockets.TcpListener ([Net.IPAddress]::Loopback, $Port); `$l.Start(); while (`$true) { Start-Sleep -Seconds 1 }"
  $lp = Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command',$listenCmd -PassThru -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds(10)
  do { Start-Sleep -Milliseconds 200; $up = netstat -ano | Select-String (":$Port .*LISTENING") } while (-not $up -and (Get-Date) -lt $deadline)
  if (-not $up) { Write-Output "$Label SKIP listener never bound"; Stop-Process -Id $lp.Id -Force -ErrorAction SilentlyContinue; return }

  if ($PidMode -eq 'holder') { Set-Content (Join-Path $dir "data\.tina4-serve-$Port.pid") "$($lp.Id)" -Encoding ascii }
  if ($PidMode -eq 'other') { Set-Content (Join-Path $dir "data\.tina4-serve-$Port.pid") '999999' -Encoding ascii }

  $clientCmd = "`$c = New-Object System.Net.Sockets.TcpClient; `$c.Connect('127.0.0.1', $Port); while (`$true) { Start-Sleep -Seconds 1 }"
  $cp = Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command',$clientCmd -PassThru -WindowStyle Hidden
  Start-Sleep -Seconds 1
  $states = (netstat -ano | Select-String ":$Port ") | ForEach-Object { $_.Line.Trim() }

  $serveArgs = @('serve')
  if ($How -eq 'explicit') { $serveArgs += @('-p', "$Port") }
  $env:TINA4_NO_BROWSER = 'true'
  $out = Join-Path $dir 'out.txt'
  $err = Join-Path $dir 'err.txt'
  $sp = Start-Process -FilePath $bin -ArgumentList $serveArgs -WorkingDirectory $dir -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
  if (-not $sp.WaitForExit(8000)) { Stop-Process -Id $sp.Id -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Milliseconds 600
  $lAlive = $null -ne (Get-Process -Id $lp.Id -ErrorAction SilentlyContinue)
  $cAlive = $null -ne (Get-Process -Id $cp.Id -ErrorAction SilentlyContinue)
  $line = @(Get-Content $out,$err -ErrorAction SilentlyContinue | Select-String 'Port |kill|freed|Could not|Detected') | Select-Object -First 1
  Write-Output ("{0,-18} listener={1} client={2} | {3}" -f $Label, ($(if ($lAlive) {'alive'} else {'DEAD'})), ($(if ($cAlive) {'alive'} else {'DEAD'})), $line)
  Write-Output ("  netstat-before: " + (($states | Select-Object -First 4) -join ' || '))
  Stop-Process -Id $lp.Id,$cp.Id,$sp.Id -Force -ErrorAction SilentlyContinue
}

Invoke-Case 'foreign-explicit' 18941 'none' 'explicit'
Invoke-Case 'foreign-default'  18942 'none' 'default'
Invoke-Case 'stale-pidfile'    18943 'other' 'explicit'
Invoke-Case 'own-pidfile'      18944 'holder' 'explicit'
