# AgentBetta Windows release build script.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$pyinstaller = Join-Path $root ".venv\Scripts\pyinstaller.exe"
$version = "0.2.0-alpha.1"
$releaseDir = Join-Path $root "release\windows\$version"

# Locate the Inno Setup compiler in common install locations or on PATH.
$iscc = $null
$candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    "C:\ProgramData\chocolatey\bin\ISCC.exe"
)
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) { $iscc = $candidate; break }
}
if (-not $iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}

Write-Host "== Tests =="
Push-Location $root
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Tests failed; aborting build." }

Write-Host "== Generate icon =="
& $python (Join-Path $root "packaging\make_icon.py")

Write-Host "== PyInstaller =="
& $pyinstaller --clean --noconfirm agentbetta.spec
Pop-Location

Write-Host "== Release directory =="
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

Write-Host "== Portable ZIP =="
$portable = Join-Path $releaseDir "AgentBetta-$version-Windows-x64-Portable.zip"
if (Test-Path $portable) { Remove-Item -LiteralPath $portable -Force }
Compress-Archive -Path (Join-Path $root "dist\AgentBetta") -DestinationPath $portable -CompressionLevel Optimal

Write-Host "== Inno Setup installer =="
if ($iscc) {
    & $iscc (Join-Path $root "packaging\agentbetta.iss")
} else {
    Write-Warning "Inno Setup compiler not found; skipping installer. Install Inno Setup 6 to build the Setup EXE."
}

Write-Host "== SHA-256 hashes =="
$sums = Join-Path $releaseDir "SHA256SUMS.txt"
Get-ChildItem -File $releaseDir | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | ForEach-Object {
    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
    "$hash  $($_.Name)"
} | Set-Content -LiteralPath $sums -Encoding ascii

Write-Host "Release artifacts:"
Get-ChildItem -File $releaseDir | Select-Object Name, @{N="MB";E={"{0:N1}" -f ($_.Length/1MB)}}
