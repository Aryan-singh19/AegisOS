$ErrorActionPreference = "Stop"

Write-Host "[AegisOS] PowerShell bootstrap"
$tools = @("git", "python", "clang", "cmake", "ninja")
$missing = @()

foreach ($tool in $tools) {
  if (Get-Command $tool -ErrorAction SilentlyContinue) {
    Write-Host "[ok] $tool"
  } else {
    Write-Host "[missing] $tool"
    $missing += $tool
  }
}

if ($missing.Count -gt 0) {
  Write-Host ""
  Write-Host "Some tools are missing."
  Write-Host "Install suggestions (winget):"
  Write-Host "  winget install --id Git.Git -e"
  Write-Host "  winget install --id Python.Python.3.11 -e"
  Write-Host "  winget install --id LLVM.LLVM -e"
  Write-Host "  winget install --id Kitware.CMake -e"
  Write-Host "  winget install --id Ninja-build.Ninja -e"
  exit 1
}

Write-Host ""
Write-Host "Running first build validation..."
python scripts/onboarding_check.py
if ($LASTEXITCODE -ne 0) {
  Write-Host "Bootstrap validation failed."
  exit $LASTEXITCODE
}
Write-Host "Bootstrap completed successfully."
