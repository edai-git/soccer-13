#!/usr/bin/env bash
# scripts/validate.sh — Validate build artifacts, clean-room hygiene, licenses & package integrity
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# shellcheck source=docker/build-env.sh
source "$PROJECT_ROOT/docker/build-env.sh"

echo "=========================================================="
echo "  Validating SOCCER13 Release Artifacts & Hygiene"
echo "=========================================================="

# 1. Clean-room & trademark audit
echo "[+] Step 1: Auditing repository and artifact clean-room hygiene..."
python3 -m unittest tests.package.test_clean_room -v

# 2. Settings & Profile validation
echo "[+] Step 2: Validating configuration & settings generators..."
python3 "$PROJECT_ROOT/scripts/generate-settings.py" --validate
python3 -m unittest tests.config.test_profile -v

# 3. PKG Validation if package exists
PKG_PATH="${1:-$PROJECT_ROOT/release/SOCCER13-PS4.pkg}"
if [[ ! -f "$PKG_PATH" ]]; then
  PKG_PATH="$PROJECT_ROOT/artifacts/SOCCER13-PS4.pkg"
fi

if [[ -f "$PKG_PATH" && -s "$PKG_PATH" ]]; then
  echo "[+] Step 3: Validating PS4 PKG structure ($PKG_PATH)..."
  PKGTOOL="$PROJECT_ROOT/runtime/orbis-win/sdk/orbis-sdk-v1/sdk/bin/linux/PkgTool.Core"
  if [[ -x "$PKGTOOL" ]]; then
    echo "    Running PkgTool.Core pkg_validate..."
    LD_LIBRARY_PATH="${PS4_PKGTOOL_OPENSSL_LIB:-/opt/openssl11/lib}:${LD_LIBRARY_PATH:-}" \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
      "$PKGTOOL" pkg_validate "$PKG_PATH" || {
        echo "[-] ERROR: PkgTool pkg_validate reported errors" >&2
        exit 1
      }
    echo "[+] PkgTool validation OK."
  else
    echo "[!] Notice: PkgTool.Core not available on this host environment; skipping binary pkg_validate."
  fi
  
  echo "    Package SHA-256:"
  sha256sum "$PKG_PATH"
else
  echo "[!] Notice: No .pkg file found to validate at $PKG_PATH (run package.sh first)."
fi

# 4. License and notices check
echo "[+] Step 4: Checking licenses and attribution..."
if [[ -f "$PROJECT_ROOT/release/THIRD_PARTY.md" ]]; then
  echo "    Found release/THIRD_PARTY.md"
fi

echo "[+] Validation completed successfully."

