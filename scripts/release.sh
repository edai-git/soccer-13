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

# 4. Generate THIRD_PARTY.md if missing
if [[ ! -f "$PROJECT_ROOT/release/THIRD_PARTY.md" ]]; then
  cat <<'EOF' > "$PROJECT_ROOT/release/THIRD_PARTY.md"
# THIRD_PARTY.md — Third-Party Licenses and Attributions for SOCCER13

SOCCER13 is an independent open-source clean-room homebrew project. It incorporates and links against the following open-source projects:

- **orbis-win & prospero-win:** LGPL-2.1-or-later (https://github.com/plastikman/orbis-win)
- **Wine:** LGPL-2.1-or-later (https://www.winehq.org)
- **Mesa / RADV:** MIT License (https://mesa3d.org)
- **DXVK:** zlib/libpng License (https://github.com/doitsujin/dxvk)
- **OpenOrbis Toolchain & Module Stubs:** GPL-3.0 (https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)
- **FreeType:** FreeType License / GPL-2.0 (https://www.freetype.org)

No game code, executables, graphics, audio, or trademarks belonging to Konami or Sony Interactive Entertainment are distributed with this software.
EOF
fi

# 5. Generate BUILD-MANIFEST.txt and SHA256SUMS
echo "[+] Emitting release provenance & SHA256SUMS..."
cd "$PROJECT_ROOT/release"
{
  echo "SOCCER13 PS4 HEN Release"
  echo "build_timestamp=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "source_date_epoch=${SOURCE_DATE_EPOCH:-1767225600}"
  echo "root_commit=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "uncommitted")"
  echo "orbis_win_commit=$(git -C "$PROJECT_ROOT/runtime/orbis-win" rev-parse HEAD 2>/dev/null || echo "unknown")"
} > BUILD-MANIFEST.txt

find . -maxdepth 1 -type f ! -name "SHA256SUMS" -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
cat BUILD-MANIFEST.txt
cat SHA256SUMS

# 6. Final validation
bash "$PROJECT_ROOT/scripts/validate.sh" "$PROJECT_ROOT/release/SOCCER13-PS4.pkg"

echo "=========================================================="
echo "  SOCCER13 Release build completed successfully!"
echo "  Artifacts available in release/"
echo "=========================================================="

