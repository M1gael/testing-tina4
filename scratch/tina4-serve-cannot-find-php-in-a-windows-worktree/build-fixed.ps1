# Builds the fixed tina4.exe on the guest with rustup's windows-gnu toolchain (self-contained linker).
$T = 'C:\Users\mig\t120'; Set-Location $T
if (!(Test-Path "$env:USERPROFILE\.cargo\bin\cargo.exe")) {
  Invoke-WebRequest -UseBasicParsing 'https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-gnu/rustup-init.exe' -OutFile rustup-init.exe
  & .\rustup-init.exe -y --default-host x86_64-pc-windows-gnu --default-toolchain stable --profile minimal 2>&1 | Select -Last 2
}
$env:PATH = "$env:USERPROFILE\.cargo\bin;$T\git\cmd;" + $env:PATH
& rustup default stable-x86_64-pc-windows-gnu 2>&1 | Select -Last 1
Remove-Item -Recurse -Force "$T\src" -ErrorAction SilentlyContinue; New-Item -ItemType Directory "$T\src" | Out-Null
& tar -xzf "$T\src120.tgz" -C "$T\src"; Set-Location "$T\src"
$env:CARGO_TARGET_DIR = "$T\target"
& cargo build --release 2>&1 | Select -Last 3
Copy-Item "$T\target\release\tina4.exe" "$T\tools\tina4-fixed.exe" -Force
& "$T\tools\tina4-fixed.exe" --version
