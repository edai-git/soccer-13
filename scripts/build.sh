#!/usr/bin/env bash
# scripts/build.sh — Main build entrypoint for soccer13
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# shellcheck source=docker/build-env.sh
source "$PROJECT_ROOT/docker/build-env.sh"

CLEAN=0
if [[ "${1:-}" == "--clean" ]]; then
  CLEAN=1
  shift || true
fi

if (( CLEAN )); then
  echo "[+] Cleaning soccer13 build artifacts..."
  rm -rf "$PROJECT_ROOT/artifacts"/* "$PROJECT_ROOT/release"/* "$PROJECT_ROOT/build"/*
  echo "[+] Clean finished."
  exit 0
fi

echo "=========================================================="
echo "  Building SOCCER13 (PS4 HEN) — Docker Build Pipeline"
echo "=========================================================="

# 1. Verify submodule
if [[ ! -f "$PROJECT_ROOT/runtime/orbis-win/README.md" ]]; then
  echo "[-] ERROR: runtime/orbis-win submodule is not initialized." >&2
  echo "    Run: git submodule update --init --recursive" >&2
  exit 1
fi

mkdir -p "$PROJECT_ROOT/artifacts" "$PROJECT_ROOT/release" "$PROJECT_ROOT/build"

# 2. Fetch & verify SDK bundle if needed
echo "[+] Step 1: Checking OpenOrbis SDK bundle..."
if [[ ! -f "$PROJECT_ROOT/runtime/orbis-win/sdk/orbis-sdk-v1/BUNDLE.txt" ]]; then
  echo "    Fetching SDK bundle via upstream fetch-sdk.sh..."
  (cd "$PROJECT_ROOT/runtime/orbis-win" && bash scripts/fetch-sdk.sh)
else
  echo "    OpenOrbis SDK bundle already verified."
fi

# 3. Synchronize toolchain shim
echo "[+] Step 2: Synchronizing toolchain shims..."
(cd "$PROJECT_ROOT/runtime/orbis-win" && bash scripts/sync-toolchain.sh)

# 4. Build OpenOrbis module stubs (clean-room GPL-3.0, no proprietary blobs)
echo "[+] Step 3: Building OpenOrbis module stubs (libc.prx & libSceFios2.prx)..."
export PW_MODULE_STUBS_DIR="$PROJECT_ROOT/build/openorbis-module-stubs"
(cd "$PROJECT_ROOT/runtime/orbis-win" && bash scripts/build-openorbis-module-stubs.sh)

# 5. Build and validate soccer13 configuration templates
echo "[+] Step 4: Validating soccer13 game profiles & configurations..."
if [[ -f "$PROJECT_ROOT/scripts/generate-settings.py" ]]; then
  python3 "$PROJECT_ROOT/scripts/generate-settings.py" --validate
fi

# 6. Execute Baseline Runtime Build (Phase 2)
echo "[+] Step 5: Executing Baseline Runtime build (Phase 2)..."
if [[ -f "$PROJECT_ROOT/scripts/build-baseline.sh" ]]; then
  bash "$PROJECT_ROOT/scripts/build-baseline.sh"
fi

echo "[+] Build completed successfully."
echo "    Staged components in build/ and artifacts/."

