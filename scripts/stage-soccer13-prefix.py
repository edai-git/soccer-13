#!/usr/bin/env python3
"""scripts/stage-soccer13-prefix.py — Stage and configure Wine prefix for SOCCER13.

Prepares:
- Prefixes tree: /data/prospero-win/prefixes/soccer13/
- User Documents: drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/
- Game directory: drive_c/Games/SOCCER13/ (including all user files and community mods)
- Registry injection: system.reg (Wow6432Node\\KONAMI\\PES2013 + CPU), user.reg (Wine\\Direct3D)
- settings.dat: 852-byte CRC16-XMODEM-NOT generated binary
- dxvk.conf: Direct3D 9 configuration
- Save data protection: Never overwrites existing save files during install or repair.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import shutil
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

# Load validator
val_spec = importlib.util.spec_from_file_location("validate_game", SCRIPT_DIR / "validate-game.py")
validate_game = importlib.util.module_from_spec(val_spec)
val_spec.loader.exec_module(validate_game)

# Load settings generator
set_spec = importlib.util.spec_from_file_location("generate_settings", SCRIPT_DIR / "generate-settings.py")
generate_settings = importlib.util.module_from_spec(set_spec)
set_spec.loader.exec_module(generate_settings)

DOCS_REL = "drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013"
PROGRAMDATA_DOWNLOAD_REL = "drive_c/ProgramData/KONAMI/Pro Evolution Soccer 2013/download"
GAMES_REL = "drive_c/Games/SOCCER13"

# Repack installer/uninstaller artifacts to skip when staging to PS4
SKIP_REPACK_DIRS = {"save", "original", "temp", "directx9c", "dvd"}
SKIP_REPACK_FILES = {"code.txt", "unins000.exe", "unins000.dat", "struktur.txt", "base-game-structure.txt"}


def inject_registry_block(reg_path: Path, section_header: str, key_values: dict[str, str | int]) -> None:
    """Injects or updates a registry section idempotently in a Wine .reg file."""
    if reg_path.is_file():
        content = reg_path.read_text(encoding="utf-8", errors="replace")
    else:
        content = "WINE REGISTRY Version 2\n;; All keys relative to registry root\n\n"

    section_pattern = rf"(?m)^\[{re.escape(section_header)}\][^\n]*\n"
    match = re.search(section_pattern, content)

    # Format new block
    lines = [f"[{section_header}] 1767225600", "#time=1dd56b8619811d4"]
    for k, v in key_values.items():
        if isinstance(v, int):
            lines.append(f'"{k}"=dword:{v:08x}')
        else:
            escaped_val = str(v).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'"{k}"="{escaped_val}"')
    new_block = "\n".join(lines) + "\n\n"

    if match:
        # Find next section or end of file
        start = match.start()
        end_match = re.search(r"(?m)^\[", content[match.end():])
        if end_match:
            end = match.end() + end_match.start()
        else:
            end = len(content)
        content = content[:start] + new_block + content[end:].lstrip()
    else:
        content = content.rstrip() + "\n\n" + new_block

    reg_path.write_text(content, encoding="utf-8")


def stage_soccer13_prefix(
    prefix_dir: Path,
    base_prefix: Path | None = None,
    game_source: Path | None = None,
    product_code: str | None = None,
    width: int = 1920,
    height: int = 1080,
    quality: int = 2,
    fullscreen: int = 1,
    repair: bool = False,
) -> dict:
    prefix_dir = prefix_dir.resolve()
    result = {
        "prefix_dir": str(prefix_dir),
        "game_copied": False,
        "files_copied": 0,
        "mods_copied": [],
        "saves_protected": 0,
        "settings_dat": None,
        "errors": [],
    }

    # 1. Base prefix copy if provided and target doesn't exist
    if base_prefix and base_prefix.is_dir() and not (prefix_dir / "system.reg").is_file():
        print(f"[+] Copying base Wine prefix from {base_prefix} -> {prefix_dir}...")
        prefix_dir.mkdir(parents=True, exist_ok=True)
        for item in base_prefix.iterdir():
            if item.name in ("drive_c", "dosdevices", "system.reg", "user.reg", "userdef.reg", ".update-timestamp"):
                dst = prefix_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dst)

    # 2. Ensure directory tree
    games_dir = prefix_dir / GAMES_REL
    docs_dir = prefix_dir / DOCS_REL
    save_dir = docs_dir / "save"
    games_dir.mkdir(parents=True, exist_ok=True)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 3. Handle Game Source & Mods
    if game_source and game_source.is_dir():
        validation = validate_game.validate_game_installation(game_source)
        if not validation["valid"]:
            result["errors"].extend(validation["errors"])
            return result

        code = product_code or validation["product_code"] or validate_game.DEFAULT_PRODUCT_CODE

        print(f"[+] Staging game files and mods from {game_source} -> {games_dir}...")
        copied_count = 0
        for item in game_source.iterdir():
            dst = games_dir / item.name
            name_lower = item.name.lower()
            if item.is_dir():
                if name_lower not in SKIP_REPACK_DIRS:
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                    copied_count += sum(1 for _ in dst.rglob("*") if _.is_file())
                    if name_lower in validate_game.KNOWN_MOD_DIRECTORIES:
                        result["mods_copied"].append(item.name)
            elif item.is_file():
                if name_lower not in SKIP_REPACK_FILES:
                    shutil.copy2(item, dst)
                    copied_count += 1
                    if name_lower in validate_game.KNOWN_MOD_DLLS:
                        result["mods_copied"].append(item.name)
        result["game_copied"] = True
        result["files_copied"] = copied_count

        # Stage CommonAppData/ProgramData download folder (e.g., defdat / DLC) from Repack Original/DVD or root
        prog_dl_dir = prefix_dir / PROGRAMDATA_DOWNLOAD_REL
        for candidate_dl in (
            game_source / "Original/DVD/CommonAppData/KONAMI/Pro Evolution Soccer 2013/download",
            game_source / "CommonAppData/KONAMI/Pro Evolution Soccer 2013/download",
            game_source / "download",
        ):
            if candidate_dl.is_dir():
                prog_dl_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(candidate_dl, prog_dl_dir, dirs_exist_ok=True)
                break

        # Check for save seed (EDIT.bin, etc.) from source
        src_save = game_source / "save"
        if src_save.is_dir():
            for save_file in src_save.glob("*"):
                if save_file.is_file():
                    target_save = save_dir / save_file.name
                    if target_save.exists():
                        result["saves_protected"] += 1
                    else:
                        shutil.copy2(save_file, target_save)
    else:
        code = product_code or validate_game.DEFAULT_PRODUCT_CODE

    # 4. Copy dxvk.conf
    dxvk_conf = ROOT / "app/config/dxvk.conf"
    if dxvk_conf.is_file():
        shutil.copy2(dxvk_conf, games_dir / "dxvk.conf")

    # 5. Generate settings.dat (852 bytes, CRC16-XMODEM-NOT)
    settings_file = docs_dir / "settings.dat"
    # Never overwrite if user has customized settings and running repair, unless forced
    if not repair or not settings_file.is_file():
        settings_payload = generate_settings.generate_settings(
            width=width,
            height=height,
            quality=quality,
            fullscreen=(fullscreen == 1),
            xinput=True,
        )
        settings_file.write_bytes(settings_payload)
        result["settings_dat"] = str(settings_file)

    # 6. Inject Registry
    system_reg = prefix_dir / "system.reg"
    user_reg = prefix_dir / "user.reg"

    # KONAMI PES2013 registration
    inject_registry_block(
        system_reg,
        "Software\\Wow6432Node\\KONAMI\\PES2013",
        {
            "installdir": "C:\\Games\\SOCCER13\\",
            "version": "1.00.0000",
            "code": code,
        },
    )

    # CPU spec check bypass
    inject_registry_block(
        system_reg,
        "Hardware\\Description\\System\\CentralProcessor\\0",
        {
            "~MHz": 3500,
            "Identifier": "AMD64 Family 22 Model 48 Stepping 1",
            "VendorIdentifier": "AuthenticAMD",
            "ProcessorNameString": "AMD Jaguar 8-Core Processor",
            "FeatureSet": 0x1FFF,
        },
    )

    # VRAM check bypass
    inject_registry_block(
        user_reg,
        "Software\\Wine\\Direct3D",
        {
            "VideoMemorySize": "2048",
            "renderer": "no3d",
        },
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prefix_dir", type=Path, help="Target Wine prefix directory (e.g. prefixes/soccer13)")
    parser.add_argument("--game-source", type=Path, help="Source directory containing user pes2013.exe & mods")
    parser.add_argument("--base-prefix", type=Path, help="Existing Wine base prefix to clone from")
    parser.add_argument("--product-code", help="Override product code")
    parser.add_argument("--width", type=int, default=1920, help="Horizontal resolution (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Vertical resolution (default: 1080)")
    parser.add_argument("--quality", type=int, default=1, choices=[0, 1, 2], help="Quality: 0=Low, 1=Med, 2=High")
    parser.add_argument("--fullscreen", type=int, default=1, choices=[0, 1], help="1=Fullscreen, 0=Windowed")
    parser.add_argument("--repair", action="store_true", help="Repair mode: protect existing saves and settings")
    args = parser.parse_args()

    res = stage_soccer13_prefix(
        prefix_dir=args.prefix_dir,
        base_prefix=args.base_prefix,
        game_source=args.game_source,
        product_code=args.product_code,
        width=args.width,
        height=args.height,
        quality=args.quality,
        fullscreen=args.fullscreen,
        repair=args.repair,
    )

    if res["errors"]:
        print(f"[-] Staging failed with {len(res['errors'])} error(s):")
        for err in res["errors"]:
            print(f"    - {err}")
        return 1

    print(f"[+] Successfully staged SOCCER13 prefix at: {res['prefix_dir']}")
    if res["game_copied"]:
        print(f"    Game files copied: {res['files_copied']}")
    if res["mods_copied"]:
        print(f"    Mods copied: {', '.join(res['mods_copied'])}")
    if res["saves_protected"]:
        print(f"    Protected existing save files: {res['saves_protected']}")
    if res["settings_dat"]:
        print(f"    Generated settings: {res['settings_dat']} ({args.width}x{args.height}, Quality={args.quality})")
    print("    Registry configured (PES2013 installdir + CPU clock + VRAM bypass).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
