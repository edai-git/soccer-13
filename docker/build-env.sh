#!/usr/bin/env bash
# docker/build-env.sh — Environment setup and checksum verification for soccer13
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
LOCK_FILE="$SCRIPT_DIR/dependencies.lock"

if [[ ! -f "$LOCK_FILE" ]]; then
  echo "[-] ERROR: dependencies.lock not found at $LOCK_FILE" >&2
  exit 1
fi

# Load locked versions and checksums
# shellcheck source=/dev/null
source "$LOCK_FILE"

export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1767225600}"
export LC_ALL=C
export TZ=UTC

# PS4 OpenOrbis & orbis-win compatibility paths
export PW_PS4_ROOT="${PROJECT_ROOT}/runtime/orbis-win"
export OO_PS4_TOOLCHAIN="${OO_PS4_TOOLCHAIN:-${PROJECT_ROOT}/runtime/orbis-win/sdk/orbis-sdk-v1/sdk}"
export PW_MODULE_STUBS_DIR="${PW_MODULE_STUBS_DIR:-${PROJECT_ROOT}/build/openorbis-module-stubs}"

# OpenSSL 1.1 isolated path for PkgTool.Core
if [[ -d "/opt/openssl11/lib" ]]; then
  export LD_LIBRARY_PATH="/opt/openssl11/lib:${LD_LIBRARY_PATH:-}"
  export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
  export PS4_PKGTOOL_OPENSSL_LIB="/opt/openssl11/lib"
fi

verify_toolchain() {
  echo "[+] Verifying build toolchain..."
  command -v clang >/dev/null || { echo "[-] clang is required" >&2; return 1; }
  command -v ld.lld >/dev/null || { echo "[-] ld.lld is required" >&2; return 1; }
  command -v llvm-ar >/dev/null || { echo "[-] llvm-ar is required" >&2; return 1; }

  local clang_ver
  clang_ver=$(clang --version | head -n1)
  echo "    Detected Clang: $clang_ver"
  if [[ "$clang_ver" != *"$LLVM_VERSION"* ]]; then
    echo "[!] WARNING: Clang is not exactly $LLVM_VERSION (detected: $clang_ver)" >&2
  fi
  echo "[+] Toolchain verification OK."
}

ensure_orbis_sdk() {
  local sdk_dest="${PROJECT_ROOT}/runtime/orbis-win/sdk"
  local bundle_txt="${sdk_dest}/orbis-sdk-v1/BUNDLE.txt"
  local tag="orbis-sdk-v1"

  if [[ -f "$bundle_txt" ]]; then
    echo "    OpenOrbis SDK bundle already verified."
    return 0
  fi

  echo "    Ensuring OpenOrbis SDK bundle ($tag)..."
  mkdir -p "$sdk_dest"

  # If tarball is not yet downloaded, fetch using API endpoint (with direct fallback)
  if [[ ! -f "$sdk_dest/$tag.tar.gz" ]]; then
    echo "    Downloading $tag.tar.gz via GitHub API endpoint..."
    curl -fL# -H "Accept: application/octet-stream" \
      -o "$sdk_dest/$tag.tar.gz" \
      "https://api.github.com/repos/orbis-ports/orbis-porting-kit/releases/assets/572744939" || {
        echo "    API endpoint failed; trying direct release download..."
        curl -fL# -o "$sdk_dest/$tag.tar.gz" \
          "https://github.com/orbis-ports/orbis-porting-kit/releases/download/$tag/$tag.tar.gz"
      }
  fi

  if [[ ! -f "$sdk_dest/$tag.tar.gz.sha256" ]]; then
    curl -fLs -H "Accept: application/octet-stream" \
      -o "$sdk_dest/$tag.tar.gz.sha256" \
      "https://api.github.com/repos/orbis-ports/orbis-porting-kit/releases/assets/572744940" || {
        curl -fLs -o "$sdk_dest/$tag.tar.gz.sha256" \
          "https://github.com/orbis-ports/orbis-porting-kit/releases/download/$tag/$tag.tar.gz.sha256"
      }
  fi

  # Delegate unpacking, pairing check, and gate verification to upstream fetch-sdk.sh
  (cd "${PROJECT_ROOT}/runtime/orbis-win" && bash scripts/fetch-sdk.sh)
}

verify_dependencies() {
  echo "[+] Verifying pinned source revisions & bundles..."
  
  # Verify orbis-win submodule commit if in a git tree
  if [[ -d "${PROJECT_ROOT}/runtime/orbis-win/.git" || -f "${PROJECT_ROOT}/runtime/orbis-win/.git" ]]; then
    local current_orbis_win
    current_orbis_win=$(git -C "${PROJECT_ROOT}/runtime/orbis-win" rev-parse HEAD 2>/dev/null || true)
    if [[ -n "$current_orbis_win" ]]; then
      echo "    runtime/orbis-win commit: $current_orbis_win"
      if [[ "$current_orbis_win" != "$ORBIS_WIN_COMMIT" ]]; then
        echo "[!] WARNING: runtime/orbis-win commit ($current_orbis_win) differs from lock ($ORBIS_WIN_COMMIT)"
      fi
    fi
  fi

  # Verify SDK bundle if unpacked
  local bundle_txt="${PROJECT_ROOT}/runtime/orbis-win/sdk/orbis-sdk-v1/BUNDLE.txt"
  if [[ -f "$bundle_txt" ]]; then
    echo "[+] Found OpenOrbis SDK bundle: $(grep -E '^gate=' "$bundle_txt" 2>/dev/null || echo "orbis-sdk-v1")"
  fi
  echo "[+] Dependencies check completed."
}

if [[ "${1:-}" == "--verify" ]]; then
  verify_toolchain
  verify_dependencies
elif [[ "${1:-}" == "--env" ]]; then
  env | grep -E '^(UBUNTU|LLVM|ORBIS|PW_|OO_|SOURCE_DATE_EPOCH|DOTNET_)'
fi

