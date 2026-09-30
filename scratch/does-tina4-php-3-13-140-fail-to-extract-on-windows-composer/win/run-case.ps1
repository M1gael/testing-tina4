# One composer install of tina4stack/tina4php, fresh project, fresh COMPOSER_HOME and cache.
param([string]$Version, [string]$Label, [switch]$NoZip)
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\mig\php7z'
$php  = 'C:\Users\mig\cli27\php\php.exe'
$ini  = if ($NoZip) { "$root\php-nozip.ini" } else { 'C:\Users\mig\cli27\php\php.ini' }
$proj = "$root\proj-$Label"
foreach ($d in @($proj, "$root\home-$Label", "$root\cache-$Label")) { if (Test-Path $d) { cmd /c rmdir /s /q $d } }
New-Item -ItemType Directory $proj | Out-Null
[IO.File]::WriteAllText("$proj\composer.json", '{"require":{"tina4stack/tina4php":"' + $Version + '"}}')
$env:COMPOSER_HOME = "$root\home-$Label"
$env:COMPOSER_CACHE_DIR = "$root\cache-$Label"
$log = "$root\$Label.log"
& $php -c $ini "$root\composer.phar" update --no-interaction --no-ansi --working-dir $proj *> $log
$rc = $LASTEXITCODE
$text = Get-Content $log -Raw
$pkg = "$proj\vendor\tina4stack\tina4php"
$confd = @(Get-ChildItem -Force "$pkg\.confd_*" -Recurse -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer })
$first = $confd | Select-Object -First 1
"{0} v{1} zipext={2} 7z={3} rc={4} dangerous={5} fallback={6} failed_to_extract={7} App.php={8} confd_entries={9} first={10} attrs={11} content={12}" -f `
  $Label, $Version, (-not $NoZip), (Test-Path 'C:\Program Files\7-Zip\7z.exe'), $rc,
  ([regex]::Matches($text, 'Dangerous link path')).Count,
  $text.Contains('falling back to ZipArchive'), $text.Contains('Failed to extract tina4stack/tina4php'),
  (Test-Path "$pkg\Tina4\App.php"), $confd.Count,
  $(if ($first) { $first.Name } else { '-' }), $(if ($first) { $first.Attributes } else { '-' }),
  $(if ($first -and -not ($first.Attributes -band [IO.FileAttributes]::ReparsePoint)) { (Get-Content $first.FullName -Raw) } else { '-' })
