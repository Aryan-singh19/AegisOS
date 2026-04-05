@echo off
setlocal EnableDelayedExpansion

echo [AegisOS] Windows bootstrap
set REQUIRED_MISSING=0
for %%T in (git python clang) do (
  %%T --version >nul 2>nul
  if errorlevel 1 (
    echo [missing] %%T
    set REQUIRED_MISSING=1
  ) else (
    echo [ok] %%T
  )
)
for %%T in (cmake ninja) do (
  %%T --version >nul 2>nul
  if errorlevel 1 (
    echo [warn] optional missing %%T
  ) else (
    echo [ok] optional %%T
  )
)

if "!REQUIRED_MISSING!"=="1" (
  echo.
  echo Some required tools are missing.
  echo Install suggestions ^(winget^):
  echo   winget install --id Git.Git -e
  echo   winget install --id Python.Python.3.11 -e
  echo   winget install --id LLVM.LLVM -e
  echo   winget install --id Kitware.CMake -e
  echo   winget install --id Ninja-build.Ninja -e
  exit /b 1
)

echo.
echo Running first build validation...
python scripts\onboarding_check.py
if errorlevel 1 (
  echo Bootstrap validation failed.
  exit /b 1
)
echo Bootstrap completed successfully.

endlocal
