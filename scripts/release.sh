#!/usr/bin/env bash
# scripts/release.sh — Build, package, validate, and emit final release deliverables
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# shellcheck source=docker/build-env.sh
source "$PROJECT_ROOT/docker/build-env.sh"

echo "=========================================================="
echo "  Building SOCCER13 Official Release Package"
echo "=========================================================="

# 1. Run build
bash "$PROJECT_ROOT/scripts/build.sh"

# 2. Run all host tests
bash "$PROJECT_ROOT/scripts/test.sh"

# 3. Create package
OUT_DIR="$PROJECT_ROOT/release" bash "$PROJECT_ROOT/scripts/package.sh"

# 4. Copy THIRD_PARTY.md & generate release README.md
echo "[+] Step 3: Staging release documentation & licenses..."
if [[ -f "$PROJECT_ROOT/THIRD_PARTY.md" ]]; then
  cp -f "$PROJECT_ROOT/THIRD_PARTY.md" "$PROJECT_ROOT/release/THIRD_PARTY.md"
fi

cat <<'EOF' > "$PROJECT_ROOT/release/README.md"
# SOCCER13 (PlayStation 4 HEN Release)

**Title ID:** `GLDS13013`  
**Base Runtime:** `plastikman/orbis-win` (ABI-v4)  
**Package:** `SOCCER13-PS4.pkg`

---

## Quick Start Installation Guide

1. **Install Package on PS4:**
   - Copy `SOCCER13-PS4.pkg` to a FAT32/exFAT USB root.
   - On PS4 running GoldHEN, open **Package Installer** and install `SOCCER13-PS4.pkg`.

2. **Deploy Your Game Files & Mods:**
   - **Via USB:** Copy your PC game files (containing `pes2013.exe`, `img/`, and optional mods like `kitserver13/`) to `/SOCCER13/` on your USB stick. Insert into PS4 and open the launcher.
   - **Via Network / FTP:** From your PC, run:
     ```bash
     ./scripts/deploy-ps4.sh install-soccer13 /path/to/pc_game_folder
     ```
   - *Note for Repack editions:* `code.txt` is completely optional. Repacks and community patches run out of the box.

3. **Play:**
   - Launch `SOCCER13` from the PS4 Home Screen.
   - Select **PLAY SOCCER13** or configure graphics in **SETTINGS**.
   - All navigation uses your DualShock 4 controller.
EOF

# 5. Generate BUILD-MANIFEST.txt and SHA256SUMS
echo "[+] Step 4: Emitting release provenance & SHA256SUMS..."
cd "$PROJECT_ROOT/release"

ROOT_COMMIT=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "uncommitted")
ORBIS_WIN_COMMIT=$(git -C "$PROJECT_ROOT/runtime/orbis-win" rev-parse HEAD 2>/dev/null || echo "unknown")

{
  echo "package=SOCCER13-PS4.pkg"
  if [[ -f "SOCCER13-PS4.pkg" && -s "SOCCER13-PS4.pkg" ]]; then
    echo "package_sha256=$(sha256sum "SOCCER13-PS4.pkg" | cut -d' ' -f1)"
  else
    echo "package_sha256=none"
  fi
  echo "title_id=GLDS13013 app_ver=01.00 title=SOCCER13"
  echo "build_timestamp_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "source_date_epoch=${SOURCE_DATE_EPOCH:-1767225600}"
  echo "root_commit=$ROOT_COMMIT"
  echo "orbis_win_commit=$ORBIS_WIN_COMMIT"
  echo "wine_commit=$WINE_COMMIT"
  echo "dxvk_version=$DXVK_VERSION"
  echo "module_stub_source=OpenOrbis-PS4-Toolchain@0a1aaf9dd4a92695538bdeb09fb056d06dd11725 (GPL-3.0)"
} > BUILD-MANIFEST.txt

# Generate SHA256SUMS for all release artifacts
find . -maxdepth 1 -type f ! -name "SHA256SUMS" -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
cat BUILD-MANIFEST.txt
cat SHA256SUMS

# 6. Final validation
echo "[+] Step 5: Running final release validation..."
bash "$PROJECT_ROOT/scripts/validate.sh" "$PROJECT_ROOT/release/SOCCER13-PS4.pkg"

echo "=========================================================="
echo "  SOCCER13 Release build completed successfully!"
echo "  Artifacts available in release/"
echo "=========================================================="

