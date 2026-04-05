#!/usr/bin/env bash
set -euo pipefail

echo "[AegisOS] Unix bootstrap"

missing=0
for tool in git python3 clang cmake ninja; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "[ok] $tool"
  else
    echo "[missing] $tool"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo
  echo "Some tools are missing."
  if command -v apt-get >/dev/null 2>&1; then
    echo "Install suggestions (apt):"
    echo "  sudo apt-get update && sudo apt-get install -y git python3 clang cmake ninja-build"
  elif command -v brew >/dev/null 2>&1; then
    echo "Install suggestions (brew):"
    echo "  brew install git python llvm cmake ninja"
  else
    echo "Install git/python3/clang/cmake/ninja using your platform package manager."
  fi
  exit 1
fi

echo
echo "Running first build validation..."
python3 scripts/onboarding_check.py
echo "Bootstrap completed successfully."
