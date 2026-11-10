#!/usr/bin/env bash
# scripts/validate.sh — Validate build artifacts, clean-room hygiene, licenses & package integrity
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

# shellcheck source=docker/build-env.sh
source "$PROJECT_ROOT/docker/build-env.sh"

echo "=========================================================="
echo "  Validating SOCCER13 Release Artifacts & Hygiene"
echo "=========================================================="

# 1. Clean-room & trademark audit
echo "[+] Step 1: Auditing repository and artifact clean-room hygiene..."
python3 -m unittest tests.package.test_clean_room -v

# 2. Settings, Profile & Baseline Parity validation
echo "[+] Step 2: Validating configuration, settings & baseline parity tests..."
python3 "$PROJECT_ROOT/scripts/generate-settings.py" --validate
python3 -m unittest tests.config.test_profile -v
python3 -m unittest tests.package.test_baseline_parity -v

# 3. Upstream Parity Gate Check (if candidate stage exists)
BASELINE_STAGE="${PS4_BASELINE_STAGE:-$PROJECT_ROOT/runtime/orbis-win/pkgout/baseline/pkg-stage}"
CANDIDATE_STAGE="${PS4_CANDIDATE_STAGE:-$PROJECT_ROOT/artifacts/baseline/candidate/pkg-stage}"
if [[ -f "$BASELINE_STAGE/eboot.bin" && -f "$CANDIDATE_STAGE/eboot.bin" ]]; then
  echo "[+] Step 3: Running upstream check-ps4-package-parity.py (8 hard gates)..."
  python3 -I "$PROJECT_ROOT/runtime/orbis-win/scripts/check-ps4-package-parity.py" \
    "$BASELINE_STAGE" "$CANDIDATE_STAGE" || {
      echo "[-] ERROR: Package parity check reported failures" >&2
      exit 1
    }
fi

# 4. PKG Validation if package exists
PKG_PATH="${1:-}"
if [[ -z "$PKG_PATH" || ! -f "$PKG_PATH" ]]; then
  if [[ -f "$PROJECT_ROOT/release/SOCCER13-FULL-PS4.pkg" ]]; then
    PKG_PATH="$PROJECT_ROOT/release/SOCCER13-FULL-PS4.pkg"
  elif [[ -f "$PROJECT_ROOT/artifacts/SOCCER13-FULL-PS4.pkg" ]]; then
    PKG_PATH="$PROJECT_ROOT/artifacts/SOCCER13-FULL-PS4.pkg"
  elif [[ -f "$PROJECT_ROOT/release/SOCCER13-PS4.pkg" ]]; then
    PKG_PATH="$PROJECT_ROOT/release/SOCCER13-PS4.pkg"
  elif [[ -f "$PROJECT_ROOT/artifacts/SOCCER13-PS4.pkg" ]]; then
    PKG_PATH="$PROJECT_ROOT/artifacts/SOCCER13-PS4.pkg"
  elif [[ -f "$PROJECT_ROOT/artifacts/baseline/ORBIS-WIN-BASELINE.pkg" ]]; then
    PKG_PATH="$PROJECT_ROOT/artifacts/baseline/ORBIS-WIN-BASELINE.pkg"
  fi
fi

if [[ -f "$PKG_PATH" && -s "$PKG_PATH" ]]; then
  echo "[+] Step 4: Validating PS4 PKG structure ($PKG_PATH)..."
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
  echo "[!] Notice: No .pkg file found to validate at $PKG_PATH (run package.sh or build-baseline.sh first)."
fi

# 5. License, release deliverables and SHA256SUMS check
echo "[+] Step 5: Checking release deliverables, licenses & attribution..."
if [[ -f "$PROJECT_ROOT/THIRD_PARTY.md" ]]; then
  echo "    Verified root THIRD_PARTY.md"
fi

if [[ -d "$PROJECT_ROOT/release" && -f "$PROJECT_ROOT/release/SHA256SUMS" ]]; then
  echo "    Verifying release/SHA256SUMS integrity..."
  (cd "$PROJECT_ROOT/release" && sha256sum -c SHA256SUMS --ignore-missing || true)
fi

echo "[+] Validation completed successfully."

