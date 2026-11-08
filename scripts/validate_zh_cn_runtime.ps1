# Adapted from the v1.37.0 Windows CI runtime validation; validate before adding translated JSON.
param([Parameter(Mandatory=$true)][string]$RuntimeDirectory)

$ErrorActionPreference = 'Stop'
$requiredFiles = @(
  "$runtimeDirectory/Main.exe",
  "$runtimeDirectory/MUnique.Client.Library.dll"
)
foreach ($path in $requiredFiles) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw "Missing required runtime file: $path"
  }
}
if (-not (Test-Path -LiteralPath "$runtimeDirectory/shaders" -PathType Container)) {
  throw "Missing required runtime directory: $runtimeDirectory/shaders"
}
foreach ($path in @("$runtimeDirectory/Data", "$runtimeDirectory/fonts")) {
  if (Test-Path -LiteralPath $path) {
    throw "Unexpected bundled game data: $path"
  }
}

$dumpbin = (Get-Command dumpbin.exe -ErrorAction Stop).Source
$expectedMachinePattern = '^\s*8664 machine \(x64\)\s*$' # 8664 machine (x64)
if ([string]::IsNullOrWhiteSpace($env:WINDIR)) {
  throw "WINDIR is required for target Windows OS DLL validation."
}
if ([Environment]::Is64BitProcess) {
  $targetSystemDirectory = Join-Path $env:WINDIR "System32"
} else {
  $targetSystemDirectory = Join-Path $env:WINDIR "Sysnative"
}
$windowsOsDlls = @(
  "advapi32.dll"
  "avrt.dll"
  "bcrypt.dll"
  "cfgmgr32.dll"
  "combase.dll"
  "comctl32.dll"
  "comdlg32.dll"
  "crypt32.dll"
  "d3d12.dll"
  "dbghelp.dll"
  "dinput8.dll"
  "dnsapi.dll"
  "dwmapi.dll"
  "dxcore.dll"
  "dxgi.dll"
  "dxguid.dll"
  "gdi32.dll"
  "glu32.dll"
  "hid.dll"
  "imagehlp.dll"
  "imm32.dll"
  "iphlpapi.dll"
  "kernel32.dll"
  "mf.dll"
  "mfplat.dll"
  "mfreadwrite.dll"
  "mfsensorgroup.dll"
  "msvcrt.dll"
  "normaliz.dll"
  "ntdll.dll"
  "ole32.dll"
  "oleaut32.dll"
  "opengl32.dll"
  "powrprof.dll"
  "propsys.dll"
  "rpcrt4.dll"
  "sechost.dll"
  "secur32.dll"
  "setupapi.dll"
  "shell32.dll"
  "shcore.dll"
  "shlwapi.dll"
  "ucrtbase.dll"
  "uiautomationcore.dll"
  "urlmon.dll"
  "user32.dll"
  "usp10.dll"
  "uuid.dll"
  "version.dll"
  "vfw32.dll"
  "wininet.dll"
  "winmm.dll"
  "wintrust.dll"
  "wldap32.dll"
  "ws2_32.dll"
  "wtsapi32.dll"
)
$windowsOsDllAllowlist = @{}
foreach ($windowsOsDll in $windowsOsDlls) {
  $windowsOsDllAllowlist[$windowsOsDll] = $true
}

$rootRuntimeFiles = @{}
Get-ChildItem -LiteralPath $runtimeDirectory -Force -File |
  ForEach-Object { $rootRuntimeFiles[$_.Name] = $_.FullName }
$runtimeBinaries = @(
  Get-ChildItem -LiteralPath $runtimeDirectory -Force -File -Recurse |
    Where-Object { $_.Extension -in @(".exe", ".dll") } |
    Sort-Object FullName
)
if ($runtimeBinaries.Count -eq 0) {
  throw "Runtime directory contains no PE files: $runtimeDirectory"
}

$missingImports = @()
foreach ($binary in $runtimeBinaries) {
  $headers = @(& $dumpbin /headers $binary.FullName 2>&1)
  if ($LASTEXITCODE -ne 0) {
    throw "dumpbin /headers failed for $($binary.FullName) with exit code $LASTEXITCODE."
  }
  $machineMatches = @($headers | Select-String -Pattern $expectedMachinePattern)
  if ($machineMatches.Count -ne 1) {
    throw "Unexpected PE architecture for $($binary.FullName); expected x64."
  }

  $dependents = @(& $dumpbin /DEPENDENTS $binary.FullName 2>&1)
  if ($LASTEXITCODE -ne 0) {
    throw "dumpbin /DEPENDENTS failed for $($binary.FullName) with exit code $LASTEXITCODE."
  }
  $dependencySection = [regex]::Match(
    ($dependents -join "`n"),
    '(?ms)^[ \t]*Image has the following dependencies:[ \t]*\r?\n(?<body>.*?)(?=^[ \t]*Summary[ \t]*$)'
  )
  if (-not $dependencySection.Success) {
    throw "Could not parse dumpbin dependency heading for $($binary.FullName)."
  }
  $imports = @(
    [regex]::Matches(
      $dependencySection.Groups["body"].Value,
      '(?im)^[ \t]*(?<name>[^ \t\r\n]+\.dll)[ \t]*$'
    ) |
      ForEach-Object { $_.Groups["name"].Value } |
      Sort-Object -Unique
  )
  foreach ($importName in $imports) {
    $importFileName = [IO.Path]::GetFileName($importName)
    if (
      [IO.Path]::IsPathRooted($importName) -or
      $importName.Contains('/') -or
      $importName.Contains('\') -or
      -not [StringComparer]::Ordinal.Equals($importFileName, $importName)
    ) {
      $missingImports += "$($binary.FullName): invalid import name: $importName"
      continue
    }
    if ($importName -match '^(?:ucrtbased|(?:vcruntime|msvcp|concrt|vcomp)[0-9]+(?:_[a-z0-9_]+)?d)\.dll$') {
      $missingImports += "$($binary.FullName): debug CRT import in Release runtime: $importName"
      continue
    }
    if ($rootRuntimeFiles.ContainsKey($importName)) {
      continue
    }
    if ($importName -match '^(?:vcruntime|msvcp|concrt|vcomp)[0-9]+(?:_[a-z0-9_]+)?\.dll$') {
      $missingImports += "$($binary.FullName): VC runtime import must be staged root-local: $importName"
      continue
    }
    if ($importName -like "api-ms-win-*" -or $importName -like "ext-ms-win-*") {
      continue
    }
    if ($windowsOsDllAllowlist.ContainsKey($importName)) {
      $systemDllPath = Join-Path $targetSystemDirectory $importName
      if (Test-Path -LiteralPath $systemDllPath -PathType Leaf) {
        continue
      }
      $missingImports += "$($binary.FullName): allowlisted Windows OS DLL missing from target system directory: $importName"
      continue
    }
    $missingImports += "$($binary.FullName): $importName"
  }
}
$missingImports = @($missingImports | Sort-Object -Unique)
if ($missingImports.Count -ne 0) {
  throw "Missing runtime imports:`n$($missingImports -join "`n")"
}

# The shader list lives in cmake/ValidateShaderBlobs.cmake, which the
# build already runs on its own shader output. Running it on the
# runtime copy checks that every listed .spv, .msl and .dxil blob is
# there and valid and that no unlisted one is.
$shaderDirectory = (Resolve-Path -LiteralPath "$runtimeDirectory/shaders").Path.Replace('\', '/')
cmake "-DMU_SHADER_BLOB_DIR=$shaderDirectory" -P cmake/ValidateShaderBlobs.cmake
if ($LASTEXITCODE -ne 0) {
  throw "Runtime shaders do not match cmake/ValidateShaderBlobs.cmake (exit code $LASTEXITCODE)."
}
$otherShaderEntries = @(
  Get-ChildItem -LiteralPath $shaderDirectory -Force -Recurse |
    Where-Object { $_.PSIsContainer -or $_.Extension -notin @(".spv", ".msl", ".dxil") } |
    ForEach-Object { $_.FullName }
)
if ($otherShaderEntries.Count -ne 0) {
  throw "Unexpected entries in the runtime shader directory:`n$($otherShaderEntries -join "`n")"
}

Write-Host "Validated native x64 runtime directory: $runtimeDirectory"
