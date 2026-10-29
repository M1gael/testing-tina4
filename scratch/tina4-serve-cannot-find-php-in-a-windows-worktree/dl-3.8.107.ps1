# Fetch the published v3.8.107 Windows binary and check it against the release SHA256SUMS.
$T = 'C:\Users\mig\t120'; $u = 'https://github.com/tina4stack/tina4/releases/download/v3.8.107'
Invoke-WebRequest -UseBasicParsing "$u/tina4-windows-amd64.exe" -OutFile "$T\tools\tina4-3.8.107.exe"
$sums = Invoke-WebRequest -UseBasicParsing "$u/SHA256SUMS"; $sums = if ($sums.Content -is [byte[]]) { [Text.Encoding]::ASCII.GetString($sums.Content) } else { $sums.Content }
$want = ($sums -split "`n" | Select-String 'tina4-windows-amd64.exe').Line.Split(' ')[0]
$got = (Get-FileHash "$T\tools\tina4-3.8.107.exe" -Algorithm SHA256).Hash.ToLower()
"sha256 $got  match=$($got -eq $want)"; & "$T\tools\tina4-3.8.107.exe" --version
