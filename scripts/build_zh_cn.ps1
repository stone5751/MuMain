param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$repository = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $repository
$missing = @()
foreach ($command in @('cmake', 'ninja', 'dotnet', 'cl', 'link')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { $missing += $command }
}
if (-not $env:VCPKG_ROOT -or -not (Test-Path -LiteralPath "$env:VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake")) {
    $missing += 'VCPKG_ROOT with vcpkg.cmake'
}
if ($missing.Count) {
    throw "Missing build dependencies: $($missing -join ', '). Use a Visual Studio x64 Developer PowerShell; see docs/build/windows/console.md."
}
$compiler = (& cl.exe /? 2>&1 | Out-String)
if ($compiler -notmatch 'for x64') { throw 'The active MSVC compiler does not target x64.' }
if ((& dotnet --list-sdks | Out-String) -notmatch '(?m)^10\.') { throw '.NET 10 SDK is required.' }
if ($CheckOnly) { Write-Host 'Windows x64 build prerequisites found.'; exit 0 }

& cmake --preset windows-x64 -DBUILD_TESTING=ON
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed.' }
& cmake --build --preset windows-x64-release
if ($LASTEXITCODE -ne 0) { throw 'Windows x64 compilation failed.' }
& ctest --test-dir out/build/windows-x64 --build-config Release --output-on-failure --no-tests=error
if ($LASTEXITCODE -ne 0) { throw 'CTest failed; do not distribute this build as verified.' }
Write-Host 'Compiled and passed CTest. In-game font, layout and OpenMU connection checks are still required.'
