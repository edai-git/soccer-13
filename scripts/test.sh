#!/usr/bin/env bash
# scripts/test.sh — Execute host tests inside Docker
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# shellcheck source=docker/build-env.sh
source "$PROJECT_ROOT/docker/build-env.sh"

echo "=========================================================="
echo "  Running SOCCER13 Host Verification & Test Suite"
echo "=========================================================="

echo "[+] Step 1: Verifying dependencies lock & toolchain..."
bash "$PROJECT_ROOT/docker/build-env.sh" --verify

echo "[+] Step 2: Testing binary settings generator & CRC16..."
python3 "$PROJECT_ROOT/scripts/generate-settings.py" --validate

echo "[+] Step 3: Running Python test discovery across tests/..."
python3 -m unittest discover -s "$PROJECT_ROOT/tests" -v

echo "[+] Step 4: Verifying clean-room repository state..."
if command -v git >/dev/null && git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "    Checking for forbidden binary files in git..."
  python3 -m unittest tests.package.test_clean_room -v
fi

echo "=========================================================="
echo "  ALL HOST TESTS PASSED (100% OK)"
echo "=========================================================="

