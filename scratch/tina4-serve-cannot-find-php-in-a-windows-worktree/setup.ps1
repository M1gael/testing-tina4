# Sets up C:\Users\mig\t120: MinGit, composer, tina4 3.8.106, PHP from cli27 on PATH.
$ErrorActionPreference = 'Stop'; $T = 'C:\Users\mig\t120'; New-Item -ItemType Directory -Force $T,"$T\tools" | Out-Null
Set-Location $T
if (!(Test-Path "$T\git\cmd\git.exe")) { Invoke-WebRequest -UseBasicParsing 'https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.4/MinGit-2.56.0.4-64-bit.zip' -OutFile mingit.zip; Expand-Archive mingit.zip -DestinationPath "$T\git" -Force }
if (!(Test-Path "$T\tools\tina4.exe")) { Invoke-WebRequest -UseBasicParsing 'https://github.com/tina4stack/tina4/releases/download/v3.8.106/tina4-windows-amd64.exe' -OutFile "$T\tools\tina4.exe" }
if (!(Test-Path "$T\tools\composer.phar")) { Invoke-WebRequest -UseBasicParsing 'https://getcomposer.org/download/latest-stable/composer.phar' -OutFile "$T\tools\composer.phar" }
Set-Content "$T\tools\composer.bat" '@php "%~dp0composer.phar" %*' -Encoding ASCII
$env:PATH = "C:\Users\mig\cli27\php;$T\git\cmd;$T\tools;" + $env:PATH
& tina4 --version; & git --version; & php -v | Select -First 1; & composer --version
