# composer update of tina4stack/tina4php in a fresh project, run under the FILTERED desktop token.
param([string]$Version, [string]$Label, [switch]$NoZip)
$root = 'C:\Users\mig\php7z'
$php  = 'C:\Users\mig\cli27\php\php.exe'
$ini  = if ($NoZip) { "$root\php-nozip.ini" } else { 'C:\Users\mig\cli27\php\php.ini' }
$proj = "$root\proj-$Label"
foreach ($d in @($proj, "$root\home-$Label", "$root\cache-$Label")) { if (Test-Path $d) { cmd /c rmdir /s /q $d } }
New-Item -ItemType Directory $proj | Out-Null
[IO.File]::WriteAllText("$proj\composer.json", '{"require":{"tina4stack/tina4php":"' + $Version + '"}}')
$cmdline = "set `"COMPOSER_HOME=$root\home-$Label`" && set `"COMPOSER_CACHE_DIR=$root\cache-$Label`" && `"$php`" -c `"$ini`" `"$root\composer.phar`" update --no-interaction --no-ansi --working-dir `"$proj`""
& "$root\limited7z.ps1" -Label $Label -CmdLine $cmdline | Out-Null
$text = Get-Content "$root\$Label.log" -Raw
$rc = [regex]::Match($text, 'rc=(\d+)').Groups[1].Value
$pkg = "$proj\vendor\tina4stack\tina4php"
$confd = @(Get-ChildItem -Force "$pkg\.confd_*" -Recurse -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer })
$sevenz = (Get-Item 'C:\Program Files\7-Zip\7z.exe' -ErrorAction SilentlyContinue).VersionInfo.ProductVersion
"{0,-22} v{1} zipext={2} 7z={3} token={4} rc={5} dangerous={6} no_privilege={7} fallback={8} failed_to_extract={9} App.php={10} confd_entries={11}" -f `
  $Label, $Version, (-not $NoZip), $sevenz, ([regex]::Match($text, '(\w+) Mandatory Level').Groups[1].Value), $rc,
  ([regex]::Matches($text, 'Dangerous link path')).Count, ([regex]::Matches($text, 'required privilege is not held')).Count,
  $text.Contains('falling back to ZipArchive'), $text.Contains('Failed to extract tina4stack/tina4php'),
  (Test-Path "$pkg\Tina4\App.php"), $confd.Count
