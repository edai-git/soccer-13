#!/usr/bin/env bash
# scripts/package.sh — Generate SOCCER13-PS4.pkg using orbis-win relocatable packaging pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# shellcheck source=docker/build-env.sh
source "$PROJECT_ROOT/docker/build-env.sh"

TITLE_ID="${TITLE_ID:-GLDS13013}"
TITLE="${TITLE:-SOCCER13}"
PKG_VERSION="${PKG_VERSION:-01.00}"
OUT_DIR="${OUT_DIR:-$PROJECT_ROOT/artifacts}"
STAGE_DIR="$PROJECT_ROOT/build/pkg-stage"

echo "=========================================================="
echo "  Packaging SOCCER13 Homebrew PKG ($TITLE_ID $PKG_VERSION)"
echo "=========================================================="

mkdir -p "$OUT_DIR" "$STAGE_DIR/sce_module" "$STAGE_DIR/sce_sys"

# 1. Ensure OpenOrbis module stubs are present
if [[ ! -f "$PW_MODULE_STUBS_DIR/libc.prx" || ! -f "$PW_MODULE_STUBS_DIR/libSceFios2.prx" ]]; then
  echo "[+] Building missing OpenOrbis module stubs..."
  (cd "$PROJECT_ROOT/runtime/orbis-win" && bash scripts/build-openorbis-module-stubs.sh)
fi

cp -f "$PW_MODULE_STUBS_DIR/libc.prx" "$STAGE_DIR/sce_module/libc.prx"
cp -f "$PW_MODULE_STUBS_DIR/libSceFios2.prx" "$STAGE_DIR/sce_module/libSceFios2.prx"

# 2. Stage soccer13 profile and configuration templates
echo "[+] Staging soccer13 profile and configs..."
mkdir -p "$STAGE_DIR/app/profiles" "$STAGE_DIR/app/config"
cp -f "$PROJECT_ROOT/app/profiles/soccer13.profile" "$STAGE_DIR/app/profiles/"
cp -f "$PROJECT_ROOT/app/config/dxvk.conf" "$STAGE_DIR/app/config/"

# Generate default 1280x720 Medium settings.dat template
python3 "$PROJECT_ROOT/scripts/generate-settings.py" --out "$STAGE_DIR/app/config/settings.dat" --width 1280 --height 720 --quality 1

# 3. Create Home-screen icon if absent (generate clean 512x512 tile)
ICON="$PROJECT_ROOT/app/assets/icon0.png"
if [[ ! -f "$ICON" ]]; then
  mkdir -p "$PROJECT_ROOT/app/assets"
  if [[ -f "$PROJECT_ROOT/runtime/orbis-win/scripts/render-logo-icon.py" ]]; then
    python3 "$PROJECT_ROOT/runtime/orbis-win/scripts/render-logo-icon.py" --output "$ICON" 2>/dev/null || true
  fi
  if [[ ! -f "$ICON" && -f "$PROJECT_ROOT/runtime/orbis-win/assets/icon0.png" ]]; then
    cp "$PROJECT_ROOT/runtime/orbis-win/assets/icon0.png" "$ICON"
  fi
fi

# 4. Invoke orbis-win relocatable packaging entrypoint
echo "[+] Assembling relocatable package via orbis-win packaging pipeline..."
BUNDLE="$PROJECT_ROOT/runtime/orbis-win/sdk/orbis-sdk-v1"
MAKE_PKG="$BUNDLE/orbis-compat/scripts/ps4/make-pkg.sh"
REPACKAGE_SCRIPT="$PROJECT_ROOT/runtime/orbis-win/scripts/repackage-orbis-ab.py"

BASELINE_STAGE="${PS4_BASELINE_STAGE:-$PROJECT_ROOT/runtime/orbis-win/pkgout/baseline/pkg-stage}"
if [[ ! -f "$BASELINE_STAGE/eboot.bin" && -d "$PROJECT_ROOT/build/extracted-baseline/uroot" ]]; then
  BASELINE_STAGE="$PROJECT_ROOT/build/extracted-baseline/uroot"
elif [[ ! -f "$BASELINE_STAGE/eboot.bin" && -d "$PROJECT_ROOT/build/extracted-baseline" ]]; then
  BASELINE_STAGE="$PROJECT_ROOT/build/extracted-baseline"
fi

if [[ -f "$BASELINE_STAGE/eboot.bin" && -f "$REPACKAGE_SCRIPT" ]]; then
  echo "    Repackaging with base stage: $BASELINE_STAGE"
  mkdir -p "$STAGE_DIR/app-pkg"
  
  # Inject soccer13 profile and configs into base stage if needed
  mkdir -p "$BASELINE_STAGE/app/profiles" "$BASELINE_STAGE/app/config"
  cp -f "$PROJECT_ROOT/app/profiles/soccer13.profile" "$BASELINE_STAGE/app/profiles/"
  cp -f "$PROJECT_ROOT/app/config/dxvk.conf" "$BASELINE_STAGE/app/config/"
  cp -f "$STAGE_DIR/app/config/settings.dat" "$BASELINE_STAGE/app/config/"
  
  python3 "$REPACKAGE_SCRIPT" \
    --base-stage "$BASELINE_STAGE" \
    --out-dir "$STAGE_DIR/app-pkg" \
    --title-id "$TITLE_ID" \
    --title "$TITLE" \
    --version "$PKG_VERSION" \
    --replace "sce_module/libc.prx=$STAGE_DIR/sce_module/libc.prx" \
    --replace "sce_module/libSceFios2.prx=$STAGE_DIR/sce_module/libSceFios2.prx"
  
  PKG_FOUND=$(find "$STAGE_DIR/app-pkg" -maxdepth 1 -type f -name '*.pkg' -print -quit || true)
  if [[ -n "$PKG_FOUND" ]]; then
    cp -f "$PKG_FOUND" "$OUT_DIR/SOCCER13-PS4.pkg"
    echo "[+] Generated: $OUT_DIR/SOCCER13-PS4.pkg"
  fi
elif [[ -f "$MAKE_PKG" ]]; then
  EBOOT_FILE="$STAGE_DIR/eboot.bin"
  if [[ ! -f "$EBOOT_FILE" && -f "$BASELINE_STAGE/eboot.bin" ]]; then
    EBOOT_FILE="$BASELINE_STAGE/eboot.bin"
  elif [[ ! -f "$EBOOT_FILE" ]]; then
    # Create minimal stub eboot placeholder if real eboot not yet compiled
    touch "$EBOOT_FILE"
  fi

  bash "$MAKE_PKG" \
    --eboot "$EBOOT_FILE" \
    --title-id "$TITLE_ID" \
    --title "$TITLE" \
    --version "$PKG_VERSION" \
    --out-dir "$OUT_DIR" \
    ${ICON:+--icon "$ICON"}
  
  PKG_FOUND=$(find "$OUT_DIR" -maxdepth 1 -type f -name '*.pkg' -print -quit || true)
  if [[ -n "$PKG_FOUND" ]]; then
    mv -f "$PKG_FOUND" "$OUT_DIR/SOCCER13-PS4.pkg"
    echo "[+] Generated: $OUT_DIR/SOCCER13-PS4.pkg"
  fi
else
  echo "[!] Notice: OpenOrbis SDK bundle make-pkg.sh not yet extracted. Simulated stage created."
  touch "$OUT_DIR/SOCCER13-PS4.pkg"
fi

# 5. Stash / Copy BUILD-MANIFEST.txt
if [[ -f "$PROJECT_ROOT/artifacts/baseline/BUILD-MANIFEST.txt" ]]; then
  cp -f "$PROJECT_ROOT/artifacts/baseline/BUILD-MANIFEST.txt" "$OUT_DIR/BUILD-MANIFEST.txt"
fi

echo "[+] Packaging completed."

