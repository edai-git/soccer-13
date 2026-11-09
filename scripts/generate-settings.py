#!/usr/bin/env python3
"""scripts/generate-settings.py — Generator and validator for SOCCER13 settings.dat binary.

Re-implements the verified 852-byte 'WECF' configuration structure and CRC-16/XMODEM bitwise NOT checksum.
"""

import argparse
import struct
import sys
from pathlib import Path

SIZE = 852
WIDTH_AT = 0x10
HEIGHT_AT = 0x14
CHECKSUM_AT = 0x0C
FLAGS_AT = 0x0E
QUALITY_AT = 0x1C
FULLSCREEN_AT = 0x20

# Canonical 852-byte template (1920x1080, Fullscreen, High, XInput)
TEMPLATE_HEX = (
    "5745434602000000540300003c3bcb008007000038040000010000000200000001000000000000006b16000000000000"
    "000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "00000000612b1d6fa0d5cf11bfc74445535400000011000000200001002d0002001e0003002c0004002e000500100006"
    "00120007002f000800300009ff00000aff00000b0048000c004d000d0050000e004b000f00c8030100d0020100cb0300"
    "00cd0200ff000303ff000203ff000302ff00020200000000000000000000000000000000000000000001000100020002"
    "00030003000400040005000500060006000700070008000800090009000a000a000b000b0800000c0b00000d0900000e"
    "0a00000f0301030102010201030003000200020003030303020302030302030202020202000000000000000000000000"
    "0000000000000000000100010002000200030003000400040005000500060006000700070008000800090009000a000a"
    "000b000b0800000c0b00000d0900000e0a00000f03010301020102010300030002000200030303030203020303020302"
    "020202020000000000000000000000000000000000000000000100010002000200030003000400040005000500060006"
    "000700070008000800090009000a000a000b000b0800000c0b00000d0900000e0a00000f030103010201020103000300"
    "020002000303030302030203030203020202020200000000000000000000000000000000000000000001000100020002"
    "00030003000400040005000500060006000700070008000800090009000a000a000b000b0800000c0b00000d0900000e"
    "0a00000f0301030102010201030003000200020003030303020302030302030202020202"
)


def crc16_not(data: bytes) -> int:
    """Calculate bitwise NOT of CRC-16/XMODEM (poly=0x1021, init=0) with checksum bytes zeroed."""
    c = 0
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if (c & 0x8000) else (c << 1) & 0xFFFF
    return (~c) & 0xFFFF


def generate_settings(
    width: int = 1280,
    height: int = 720,
    quality: int = 1,
    fullscreen: bool = True,
    xinput: bool = True,
) -> bytes:
    """Generate 852-byte settings.dat binary."""
    out = bytearray(bytes.fromhex(TEMPLATE_HEX))
    struct.pack_into("<I", out, WIDTH_AT, width)
    struct.pack_into("<I", out, HEIGHT_AT, height)
    struct.pack_into("<I", out, QUALITY_AT, quality)
    struct.pack_into("<I", out, FULLSCREEN_AT, 1 if fullscreen else 0)

    # Flags: 0xCB for XInput + VSync + frame skipping; 0xC3 for DirectInput
    flags = 0xCB if xinput else 0xC3
    struct.pack_into("<H", out, FLAGS_AT, flags)

    # Zero checksum bytes before calculation
    struct.pack_into("<H", out, CHECKSUM_AT, 0)
    calculated_crc = crc16_not(out)
    struct.pack_into("<H", out, CHECKSUM_AT, calculated_crc)

    return bytes(out)


def validate_settings(data: bytes) -> bool:
    """Validate header, length, and checksum of a settings.dat binary."""
    if len(data) != SIZE:
        return False
    if data[0:4] != b"WECF":
        return False
    stored_crc = struct.unpack_from("<H", data, CHECKSUM_AT)[0]
    temp = bytearray(data)
    struct.pack_into("<H", temp, CHECKSUM_AT, 0)
    expected_crc = crc16_not(temp)
    return stored_crc == expected_crc


def run_self_test() -> bool:
    """Verify known test vectors from reference settings.exe."""
    # Test vector 1: 1920x1080 High XInput
    res_1080 = generate_settings(width=1920, height=1080, quality=2, fullscreen=True, xinput=True)
    if not validate_settings(res_1080):
        print("[-] Test Vector 1 Failed: Validation failed")
        return False
    crc_1080 = struct.unpack_from("<H", res_1080, CHECKSUM_AT)[0]
    if crc_1080 != 0x3B3C:
        print(f"[-] Test Vector 1 Failed: Expected checksum 0x3B3C, got {hex(crc_1080)}")
        return False

    # Test vector 2: 1280x720 Medium XInput (PS4 baseline default)
    res_720 = generate_settings(width=1280, height=720, quality=1, fullscreen=True, xinput=True)
    if not validate_settings(res_720):
        print("[-] Test Vector 2 Failed: Validation failed")
        return False

    print("[+] All settings.dat self-tests passed (CRC-16/XMODEM-NOT verified).")
    return True


def main():
    parser = argparse.ArgumentParser(description="SOCCER13 settings.dat generator & validator")
    parser.add_argument("--validate", action="store_true", help="Run internal self-tests")
    parser.add_argument("--check-file", type=Path, help="Check an existing settings.dat file")
    parser.add_argument("--out", type=Path, help="Output path to write settings.dat")
    parser.add_argument("--width", type=int, default=1280, help="Screen width (default: 1280)")
    parser.add_argument("--height", type=int, default=720, help="Screen height (default: 720)")
    parser.add_argument("--quality", type=int, default=1, choices=[0, 1, 2], help="Quality: 0=Low, 1=Med, 2=High")

    args = parser.parse_args()

    if args.validate:
        if not run_self_test():
            sys.exit(1)
        sys.exit(0)

    if args.check_file:
        content = args.check_file.read_bytes()
        if validate_settings(content):
            print(f"[+] {args.check_file} is VALID.")
            sys.exit(0)
        else:
            print(f"[-] {args.check_file} is INVALID.")
            sys.exit(1)

    if args.out:
        data = generate_settings(width=args.width, height=args.height, quality=args.quality)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
        print(f"[+] Written valid {len(data)}-byte settings.dat to {args.out}")


if __name__ == "__main__":
    main()

