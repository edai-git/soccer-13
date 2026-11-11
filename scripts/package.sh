#!/usr/bin/env bash
# scripts/package.sh
# Optimized SOCCER13 standalone PKG builder
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

source "$PROJECT_ROOT/docker/build-env.sh"

TITLE_ID="${TITLE_ID:-GLDS13013}"
TITLE="${TITLE:-SOCCER 13}"
PKG_VERSION="${PKG_VERSION:-01.00}"

OUT_DIR="${OUT_DIR:-$PROJECT_ROOT/artifacts}"

# External storage detection (build/external-storage)
EXTERNAL_STORAGE="${EXTERNAL_STORAGE:-$PROJECT_ROOT/build/external-storage}"
if [[ -d "$EXTERNAL_STORAGE" ]] && touch "$EXTERNAL_STORAGE/.write_test" 2>/dev/null; then
    rm -f "$EXTERNAL_STORAGE/.write_test"
    BUILD_BASE="$EXTERNAL_STORAGE"
    echo "[+] External storage detected and active: $EXTERNAL_STORAGE"
else
    BUILD_BASE="$PROJECT_ROOT/build"
fi

WORK_DIR="${WORK_DIR:-$BUILD_BASE/pkg-work}"
STAGE_DIR="$WORK_DIR/stage"
PKG_OUT="$WORK_DIR/output"

if [[ -n "${DUMP_DIR:-}" ]]; then
    echo "[+] Using game dump from DUMP_DIR override: $DUMP_DIR"
elif [[ -d "$EXTERNAL_STORAGE/ps4-dump/game/SOCCER13" ]]; then
    DUMP_DIR="$EXTERNAL_STORAGE/ps4-dump"
    echo "[+] Using game dump from external storage: $DUMP_DIR"
else
    DUMP_DIR="$PROJECT_ROOT/build/ps4-dump"
fi
DUMP_GAME="$DUMP_DIR/game/SOCCER13"
DUMP_SEED="$DUMP_DIR/seed"

ROOT="$PROJECT_ROOT/runtime/orbis-win"
OO="$ROOT/sdk/orbis-sdk-v1/sdk"
BIN="$ROOT/build/ps4-wine-sdk/bin"

BUILD_LAUNCHER="$PROJECT_ROOT/build/launcher"

REPACKAGE_SCRIPT="$ROOT/scripts/repackage-orbis-ab.py"

BASELINE_STAGE="${PS4_BASELINE_STAGE:-$ROOT/pkgout/baseline/pkg-stage}"

# HIGH 1080p settings.
# Verified against generate-settings.py (0=Low, 1=Medium, 2=High).
SETTINGS_WIDTH="${SETTINGS_WIDTH:-1920}"
SETTINGS_HEIGHT="${SETTINGS_HEIGHT:-1080}"
SETTINGS_QUALITY="${SETTINGS_QUALITY:-2}"

BUNDLE_GAME_DUMP="${BUNDLE_GAME_DUMP:-1}"

log() {
    echo "[+] $*"
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

cleanup() {
    local status=$?

    if [[ "$status" -eq 0 ]]; then
        rm -rf "$WORK_DIR"
        log "Temporary build directory cleaned."
    else
        echo "[!] Build failed. Temporary files preserved at: $WORK_DIR" >&2
    fi
}

trap cleanup EXIT

# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

copy_replace() {
    local src="$1"
    local dst="$2"

    [[ -f "$src" ]] || die "Source file missing: $src"

    mkdir -p "$(dirname "$dst")"

    local tmp="${dst}.tmp.$$"

    rm -f "$tmp"
    cp -p "$src" "$tmp"
    mv -f "$tmp" "$dst"
}

clone_tree() {
    local src="$1"
    local dst="$2"

    [[ -d "$src" ]] || die "Directory not found: $src"

    mkdir -p "$dst"

    # Hardlink clone avoids duplicating large baseline files.
    # Fall back to physical copy when hardlinks are unavailable.
    if cp -al "$src/." "$dst/" 2>/dev/null; then
        log "Hardlink clone: $src"
    else
        rm -rf "$dst"
        mkdir -p "$dst"
        cp -a "$src/." "$dst/"
        log "Physical copy fallback: $src"
    fi
}

copy_directory() {
    local src="$1"
    local dst="$2"

    [[ -d "$src" ]] || die "Directory not found: $src"

    mkdir -p "$dst"
    cp -a "$src/." "$dst/"
}

link_or_copy_tree() {
    local src="$1"
    local dst="$2"

    [[ -d "$src" ]] || die "Directory not found: $src"

    mkdir -p "$(dirname "$dst")"

    [[ ! -e "$dst" ]] || die "Destination already exists: $dst"

    if cp -al "$src" "$dst" 2>/dev/null; then
        log "Game assets linked without physical duplication."
    else
        rm -rf "$dst"
        cp -a "$src" "$dst"
        log "Game assets copied (hardlink unavailable)."
    fi
}

# ----------------------------------------------------------
# 1. Preflight
# ----------------------------------------------------------

echo "=========================================================="
echo "  SOCCER13 Standalone PKG Builder"
echo "  TITLE ID : $TITLE_ID"
echo "  VERSION  : $PKG_VERSION"
echo "=========================================================="

mkdir -p "$OUT_DIR" "$PROJECT_ROOT/build"

[[ -d "$ROOT" ]] || die "orbis-win runtime not found."
[[ -f "$OO/include/orbis/libkernel.h" ]] || die "OpenOrbis SDK not found."

if [[ "$BUNDLE_GAME_DUMP" == "1" ]]; then
    [[ -d "$DUMP_GAME" ]] || die "Game dump missing: $DUMP_GAME"
    [[ -d "$DUMP_SEED" ]] || die "Prefix seed missing: $DUMP_SEED"
fi

# Never modify the original baseline.
patch_pkgtool() {
    local pkgtool="$OO/bin/linux/PkgTool.Core"
    if [[ -f "$pkgtool" ]]; then
        python3 -c "
import sys
p = sys.argv[1]
try:
    with open(p, 'r+b') as f:
        f.seek(77934451)
        b = f.read(1)
        if b == b'\x1a':
            f.seek(77934451)
            f.write(b'\x1e')
            print('[+] Applied PlayGo ChunkSha buffer sizing patch (0x1a -> 0x1e) to PkgTool.Core')
except Exception as e:
    print(f'[!] Warning: Could not patch PkgTool.Core: {e}')
" "$pkgtool"
    fi
}
patch_pkgtool

if [[ ! -f "$BASELINE_STAGE/eboot.bin" ]]; then
    if [[ -f "$PROJECT_ROOT/build/extracted-baseline/uroot/eboot.bin" ]]; then
        BASELINE_STAGE="$PROJECT_ROOT/build/extracted-baseline/uroot"
    elif [[ -f "$PROJECT_ROOT/build/extracted-baseline/eboot.bin" ]]; then
        BASELINE_STAGE="$PROJECT_ROOT/build/extracted-baseline"
    elif [[ -f "$PROJECT_ROOT/artifacts/baseline/ORBIS-WIN-BASELINE.pkg" ]]; then
        log "Extracting baseline stage from artifacts/baseline/ORBIS-WIN-BASELINE.pkg..."
        PKGTOOL="$OO/bin/linux/PkgTool.Core"
        mkdir -p "$PROJECT_ROOT/build/extracted-baseline"
        LD_LIBRARY_PATH="${PS4_PKGTOOL_OPENSSL_LIB:-/opt/openssl11/lib}:${LD_LIBRARY_PATH:-}" \
        DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
            "$PKGTOOL" pkg_extract --passcode 00000000000000000000000000000000 \
                "$PROJECT_ROOT/artifacts/baseline/ORBIS-WIN-BASELINE.pkg" "$PROJECT_ROOT/build/extracted-baseline"
        if [[ -f "$PROJECT_ROOT/build/extracted-baseline/uroot/eboot.bin" ]]; then
            BASELINE_STAGE="$PROJECT_ROOT/build/extracted-baseline/uroot"
        else
            BASELINE_STAGE="$PROJECT_ROOT/build/extracted-baseline"
        fi
    else
        die "Valid baseline stage with eboot.bin not found."
    fi
fi

[[ -f "$REPACKAGE_SCRIPT" ]] || die "Repackage script not found."

# Remove only our dedicated temporary workspace.
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR" "$PKG_OUT"

# ----------------------------------------------------------
# 2. OpenOrbis module stubs
# ----------------------------------------------------------

if [[ ! -f "$PW_MODULE_STUBS_DIR/libc.prx" ||
      ! -f "$PW_MODULE_STUBS_DIR/libSceFios2.prx" ]]; then

    log "Building missing OpenOrbis module stubs..."

    (
        cd "$ROOT"
        bash scripts/build-openorbis-module-stubs.sh
    )
fi

[[ -f "$PW_MODULE_STUBS_DIR/libc.prx" ]] ||
    die "libc.prx missing."

[[ -f "$PW_MODULE_STUBS_DIR/libSceFios2.prx" ]] ||
    die "libSceFios2.prx missing."

# ----------------------------------------------------------
# 3. Compile direct boot EBOOT
# ----------------------------------------------------------

log "Compiling direct boot launcher..."

mkdir -p "$BIN" "$BUILD_LAUNCHER"

ln -sf /usr/local/bin/ld.lld "$BIN/orbis-ld" 2>/dev/null || true

CC="$BIN/prospero-clang"

export OO_PS4_TOOLCHAIN="$OO"

python3 "$ROOT/scripts/gen-libkernel-symbol-list.py" \
    "$OO/include/orbis/libkernel.h" \
    "$BUILD_LAUNCHER/libkernel-symbols.inc"

PW_EXECUTABLE_LD_SCRIPT="$ROOT/src/reloc-wine-app/stub-no-relro.ld" \
PW_EXECUTABLE_NO_RELRO=1 \
PW_EXECUTABLE_NO_ORBIS_COMPAT=1 \
"$CC" \
    -std=gnu11 \
    -O2 \
    -Wall \
    -Wextra \
    -Werror \
    -fPIC \
    -I"$BUILD_LAUNCHER" \
    "$PROJECT_ROOT/app/launcher/src/handoff_stub.c" \
    -o "$BUILD_LAUNCHER/handoff-linked.elf" \
    -lSceNet \
    -lSceAudioOut \
    -lSceSystemService \
    -lSceSysmodule \
    -lSceGnmDriver \
    -lSceVideoOut \
    -lScePad \
    -lSceUserService

python3 "$ROOT/scripts/prepare-orbis-stub-no-relro.py" \
    --layout 0x55c000 0x7fff0000 0x80000000 \
    "$BUILD_LAUNCHER/handoff-linked.elf" \
    "$BUILD_LAUNCHER/handoff.elf"

"$ROOT/scripts/create-fself-repro.sh" \
    "$OO/bin/linux/create-fself" \
    -in "$BUILD_LAUNCHER/handoff.elf" \
    -out "$BUILD_LAUNCHER/handoff.oelf" \
    -eboot "$BUILD_LAUNCHER/eboot.bin"

python3 "$ROOT/scripts/prepare-orbis-stub-no-relro.py" \
    --check-oelf \
    --layout 0x55c000 0x7fff0000 0x80000000 \
    "$BUILD_LAUNCHER/handoff.oelf"

[[ -s "$BUILD_LAUNCHER/eboot.bin" ]] ||
    die "Generated eboot.bin is empty or missing."

# ----------------------------------------------------------
# 4. Create one isolated staging directory
# ----------------------------------------------------------

log "Creating isolated package staging..."

# Clone baseline using hardlinks where possible.
# Original baseline remains untouched.
clone_tree "$BASELINE_STAGE" "$STAGE_DIR"

# Replace EBOOT without modifying any baseline hardlink.
copy_replace \
    "$BUILD_LAUNCHER/eboot.bin" \
    "$STAGE_DIR/eboot.bin"

# ----------------------------------------------------------
# 5. Inject profiles and configurations
# ----------------------------------------------------------

log "Injecting profiles and configurations..."

mkdir -p \
    "$STAGE_DIR/app/profiles" \
    "$STAGE_DIR/app/config" \
    "$STAGE_DIR/app/launcher" \
    "$STAGE_DIR/sce_module" \
    "$STAGE_DIR/sce_sys"

shopt -s nullglob

PROFILE_FILES=("$PROJECT_ROOT"/app/profiles/*.profile)

(( ${#PROFILE_FILES[@]} > 0 )) ||
    die "No profile files found."

for file in "${PROFILE_FILES[@]}"; do
    copy_replace "$file" "$STAGE_DIR/app/profiles/$(basename "$file")"
done

shopt -u nullglob

copy_replace \
    "$PROJECT_ROOT/app/config/dxvk.conf" \
    "$STAGE_DIR/app/config/dxvk.conf"

copy_replace \
    "$PW_MODULE_STUBS_DIR/libc.prx" \
    "$STAGE_DIR/sce_module/libc.prx"

copy_replace \
    "$PW_MODULE_STUBS_DIR/libSceFios2.prx" \
    "$STAGE_DIR/sce_module/libSceFios2.prx"

# Optional launcher binary.
if [[ -f "$PROJECT_ROOT/build/launcher/soccer13_launcher" ]]; then
    copy_replace \
        "$PROJECT_ROOT/build/launcher/soccer13_launcher" \
        "$STAGE_DIR/app/launcher/soccer13_launcher"
fi

# ----------------------------------------------------------
# 6. Generate settings
# ----------------------------------------------------------

log "Generating settings.dat..."

python3 "$PROJECT_ROOT/scripts/generate-settings.py" \
    --out "$STAGE_DIR/app/config/settings.dat" \
    --width "$SETTINGS_WIDTH" \
    --height "$SETTINGS_HEIGHT" \
    --quality "$SETTINGS_QUALITY"

[[ -s "$STAGE_DIR/app/config/settings.dat" ]] ||
    die "settings.dat generation failed."

# ----------------------------------------------------------
# 7. Inject game and registry seed
# ----------------------------------------------------------

if [[ "$BUNDLE_GAME_DUMP" == "1" ]]; then

    log "Injecting game dump..."

    mkdir -p "$STAGE_DIR/game"

    link_or_copy_tree \
        "$DUMP_GAME" \
        "$STAGE_DIR/game/SOCCER13"

    log "Injecting Wine registry seed..."

    copy_directory \
        "$DUMP_SEED" \
        "$STAGE_DIR/seed"

else
    die "Standalone package requires BUNDLE_GAME_DUMP=1."
fi

# ----------------------------------------------------------
# 8. Inject RADV configuration
# ----------------------------------------------------------

if [[ -f "$PROJECT_ROOT/build/ps4-dump/radv.env" ]]; then
    copy_replace \
        "$PROJECT_ROOT/build/ps4-dump/radv.env" \
        "$STAGE_DIR/app/radv.env"
    copy_replace \
        "$PROJECT_ROOT/build/ps4-dump/radv.env" \
        "$STAGE_DIR/radv.env"
elif [[ -f "$PROJECT_ROOT/runtime/orbis-win/radv.env" ]]; then
    copy_replace \
        "$PROJECT_ROOT/runtime/orbis-win/radv.env" \
        "$STAGE_DIR/app/radv.env"
    copy_replace \
        "$PROJECT_ROOT/runtime/orbis-win/radv.env" \
        "$STAGE_DIR/radv.env"
fi

# ----------------------------------------------------------
# 9. Inject application icons
# ----------------------------------------------------------

ICON="$PROJECT_ROOT/app/assets/icon0.png"

if [[ ! -f "$ICON" ]]; then
    mkdir -p "$PROJECT_ROOT/app/assets"

    if [[ -f "$ROOT/scripts/render-logo-icon.py" ]]; then
        python3 "$ROOT/scripts/render-logo-icon.py" \
            --output "$ICON" 2>/dev/null || true
    fi

    if [[ ! -f "$ICON" && -f "$ROOT/assets/icon0.png" ]]; then
        cp "$ROOT/assets/icon0.png" "$ICON"
    fi
fi

for name in icon0.png pic0.png pic1.png bg.raw; do

    SRC="$PROJECT_ROOT/app/assets/$name"

    if [[ -f "$SRC" ]]; then

        if [[ "$name" == "bg.raw" ]]; then
            copy_replace "$SRC" "$STAGE_DIR/app/assets/bg.raw"
        else
            copy_replace "$SRC" "$STAGE_DIR/sce_sys/$name"
        fi

    fi
done

# ----------------------------------------------------------
# 10. Validate staging
# ----------------------------------------------------------

log "Validating package staging..."

[[ -s "$STAGE_DIR/eboot.bin" ]] ||
    die "Missing EBOOT in staging."

[[ -d "$STAGE_DIR/game/SOCCER13/img" ]] ||
    die "Missing game img directory."

[[ -d "$STAGE_DIR/seed" ]] ||
    die "Missing prefix seed."

[[ -f "$STAGE_DIR/app/config/settings.dat" ]] ||
    die "Missing settings.dat."

for name in system.reg user.reg userdef.reg; do
    [[ -s "$STAGE_DIR/seed/$name" ]] ||
        die "Missing registry seed: $name"
done

# ----------------------------------------------------------
# 11. Generate standalone PKG
# ----------------------------------------------------------

log "Building standalone PKG..."

python3 "$REPACKAGE_SCRIPT" \
    --base-stage "$STAGE_DIR" \
    --out-dir "$PKG_OUT" \
    --title-id "$TITLE_ID" \
    --title "$TITLE" \
    --version "$PKG_VERSION" \
    --eboot-source "$BUILD_LAUNCHER/eboot.bin" \
    --replace "sce_module/libc.prx=$PW_MODULE_STUBS_DIR/libc.prx" \
    --replace "sce_module/libSceFios2.prx=$PW_MODULE_STUBS_DIR/libSceFios2.prx"

PKG_FOUND=""

while IFS= read -r -d '' file; do
    PKG_FOUND="$file"
    break
done < <(find "$PKG_OUT" -maxdepth 1 -type f -name '*.pkg' -print0)

[[ -n "$PKG_FOUND" ]] ||
    die "Repackage pipeline did not generate a PKG."

[[ -s "$PKG_FOUND" ]] ||
    die "Generated PKG is empty."

# Move instead of creating another full-size copy whenever possible.
FINAL_PKG="$OUT_DIR/SOCCER13-FULL-PS4.pkg"

mkdir -p "$OUT_DIR"

mv -f "$PKG_FOUND" "$FINAL_PKG"

# ----------------------------------------------------------
# 12. Generate SHA-256
# ----------------------------------------------------------

log "Generating SHA-256..."

(
    cd "$OUT_DIR"
    sha256sum "$(basename "$FINAL_PKG")" \
        > "$(basename "$FINAL_PKG").sha256"
)

# ----------------------------------------------------------
# 13. Final report
# ----------------------------------------------------------

PKG_SIZE="$(du -h "$FINAL_PKG" | awk '{print $1}')"
PKG_HASH="$(awk '{print $1}' "$FINAL_PKG.sha256")"

echo
echo "=========================================================="
echo "  SOCCER13 BUILD SUCCESS"
echo "=========================================================="
echo "PKG      : $FINAL_PKG"
echo "SIZE     : $PKG_SIZE"
echo "SHA-256  : $PKG_HASH"
echo "=========================================================="