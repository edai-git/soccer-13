#!/usr/bin/env python3
"""scripts/validate-game.py — Read-only validator for user game installation (SOCCER13).

Validates:
1. pes2013.exe exists and is a valid 32-bit Windows PE32 executable (i386).
2. img/ directory exists with core .img archives.
3. Repack support: code.txt is optional. If missing, uses standard fallback key.
4. Mod support: detects mod folders (kitserver13, pesjp2013, etc.) and mod DLLs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

DEFAULT_PRODUCT_CODE = "4X9X-J6W4-J2SN-VD5T-4CHW"

KNOWN_MOD_DIRECTORIES = (
    "kitserver13",
    "pesjp2013",
    "server",
    "gdb",
    "download",
)

KNOWN_MOD_DLLS = (
    "kload.dll",
    "dinput8.dll",
    "rld.dll",
)


def validate_pe32_header(exe_path: Path) -> tuple[bool, str, dict]:
    """Inspects PE headers without loading or executing the binary."""
    details = {
        "is_pe": False,
        "machine": "unknown",
        "format": "unknown",
        "image_base": 0,
        "relocatable": False,
        "sha256": "",
        "size_bytes": 0,
    }
    if not exe_path.is_file():
        return False, f"Executable not found: {exe_path}", details

    details["size_bytes"] = exe_path.stat().st_size
    h = hashlib.sha256()
    with exe_path.open("rb") as f:
        # Read header block
        d = f.read(0x600)
        h.update(d)
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    details["sha256"] = h.hexdigest()

    if len(d) < 0x40 or d[:2] != b"MZ":
        return False, "Not a valid Windows executable (missing MZ signature)", details

    pe_offset = struct.unpack_from("<I", d, 0x3C)[0]
    if pe_offset + 24 > len(d) or d[pe_offset:pe_offset + 4] != b"PE\0\0":
        return False, "Missing PE header signature", details

    details["is_pe"] = True
    machine = struct.unpack_from("<H", d, pe_offset + 4)[0]
    chars = struct.unpack_from("<H", d, pe_offset + 22)[0]
    magic = struct.unpack_from("<H", d, pe_offset + 24)[0]

    if machine == 0x014C:
        details["machine"] = "i386"
    elif machine == 0x8664:
        details["machine"] = "x86-64"
    else:
        details["machine"] = f"0x{machine:04x}"

    if magic == 0x10B:
        details["format"] = "PE32"
        details["image_base"] = struct.unpack_from("<I", d, pe_offset + 24 + 28)[0]
        dd = pe_offset + 24 + 96
    elif magic == 0x20B:
        details["format"] = "PE32+"
        details["image_base"] = struct.unpack_from("<Q", d, pe_offset + 24 + 24)[0]
        dd = pe_offset + 24 + 112
    else:
        return False, f"Unsupported PE optional header magic: 0x{magic:04x}", details

    if dd + 6 * 8 <= len(d):
        reloc_rva, reloc_size = struct.unpack_from("<II", d, dd + 5 * 8)
        stripped = bool(chars & 0x0001)
        details["relocatable"] = not stripped and reloc_size > 0

    if details["machine"] != "i386":
        return False, f"Game executable must be 32-bit i386, got {details['machine']}", details

    return True, "Valid PE32 i386 executable", details


def validate_game_installation(source_dir: Path) -> dict:
    """Validates game files, img assets, optional code.txt, and detected mods."""
    source_dir = source_dir.resolve()
    result = {
        "valid": False,
        "source_dir": str(source_dir),
        "executable": None,
        "executable_details": None,
        "img_dir": False,
        "img_count": 0,
        "product_code": DEFAULT_PRODUCT_CODE,
        "is_repack": True,
        "mods_detected": [],
        "save_seeds_detected": False,
        "errors": [],
    }

    if not source_dir.is_dir():
        result["errors"].append(f"Source directory does not exist: {source_dir}")
        return result

    exe_path = source_dir / "pes2013.exe"
    if not exe_path.is_file():
        # Case-insensitive fallback
        for candidate in source_dir.glob("*.exe"):
            if candidate.name.lower() == "pes2013.exe":
                exe_path = candidate
                break

    if not exe_path.is_file():
        result["errors"].append("Missing required game executable 'pes2013.exe'")
    else:
        ok, msg, details = validate_pe32_header(exe_path)
        result["executable"] = str(exe_path)
        result["executable_details"] = details
        if not ok:
            result["errors"].append(f"Executable validation failed: {msg}")

    # Check img/
    img_dir = source_dir / "img"
    if not img_dir.is_dir():
        for candidate in source_dir.iterdir():
            if candidate.is_dir() and candidate.name.lower() == "img":
                img_dir = candidate
                break

    if not img_dir.is_dir():
        result["errors"].append("Missing required 'img' directory")
    else:
        result["img_dir"] = True
        img_files = list(img_dir.glob("*.img"))
        result["img_count"] = len(img_files)
        if len(img_files) == 0:
            result["errors"].append("'img' directory exists but contains no .img archives")

    # Check code.txt (Repack support: optional)
    code_file = source_dir / "code.txt"
    if code_file.is_file():
        code = code_file.read_text(encoding="utf-8", errors="replace").strip()
        if code:
            result["product_code"] = code
            result["is_repack"] = False

    # Check mod folders and DLLs
    for item in source_dir.iterdir():
        name_lower = item.name.lower()
        if item.is_dir() and name_lower in KNOWN_MOD_DIRECTORIES:
            result["mods_detected"].append(f"dir:{item.name}")
        elif item.is_file() and name_lower in KNOWN_MOD_DLLS:
            result["mods_detected"].append(f"dll:{item.name}")

    # Check save seeds if user included a save folder
    save_dir = source_dir / "save"
    if save_dir.is_dir():
        result["save_seeds_detected"] = True

    result["valid"] = len(result["errors"]) == 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Directory containing user game files")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    report = validate_game_installation(args.source_dir)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "VALID" if report["valid"] else "INVALID"
        print(f"[{status}] SOCCER13 Installation Validator: {report['source_dir']}")
        if report["executable_details"]:
            ed = report["executable_details"]
            print(f"  Executable: {report['executable']} ({ed['machine']}, {ed['format']}, {ed['size_bytes']} B)")
            print(f"  SHA-256:    {ed['sha256']}")
        print(f"  Assets:     img/ present ({report['img_count']} .img files)")
        print(f"  Edition:    {'Repack / Pre-Cracked' if report['is_repack'] else 'Retail with code.txt'}")
        print(f"  Code:       {report['product_code']}")
        if report["mods_detected"]:
            print(f"  Mods found: {', '.join(report['mods_detected'])}")
        if report["save_seeds_detected"]:
            print("  Save seed:  save/ folder detected in source")
        if report["errors"]:
            print("  Errors:")
            for err in report["errors"]:
                print(f"    - {err}")

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

