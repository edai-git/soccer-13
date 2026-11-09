#!/usr/bin/env python3
"""scripts/dump-from-ps4.py — Dump PES 2013 game files & Wine registry seed from live PS4 via FTP.

Saves game files to build/ps4-dump/game/SOCCER13/
Saves prefix seed to build/ps4-dump/seed/
Files in build/ are strictly gitignored to preserve clean-room hygiene.
"""

import ftplib
import os
import sys
import time
from pathlib import Path

# Load .env if present
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

PS4_IP = os.environ.get("PS4_IP", "10.0.0.1")
PS4_FTP_PORT = int(os.environ.get("PS4_FTP_PORT", "2121"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DUMP_DIR = PROJECT_ROOT / "build" / "ps4-dump"
GAME_DIR = DUMP_DIR / "game" / "SOCCER13"
SEED_DIR = DUMP_DIR / "seed"


def get_ftp_connection():
    print(f"[+] Connecting to PS4 FTP at {PS4_IP}:{PS4_FTP_PORT}...")
    ftp = ftplib.FTP()
    ftp.connect(PS4_IP, PS4_FTP_PORT, timeout=30)
    ftp.login()
    print("[+] Connected to PS4 FTP.")
    return ftp


def download_file(ftp, remote_path, local_path, expected_size=None):
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if expected_size is None:
        try:
            expected_size = ftp.size(remote_path)
        except Exception:
            expected_size = None

    if local_path.is_file() and expected_size is not None and local_path.stat().st_size == expected_size:
        print(f"  [OK] {local_path.name} already downloaded ({expected_size / (1024*1024):.2f} MB), skipping.")
        return

    print(f"  [>] Downloading {remote_path} -> {local_path.name} ({expected_size / (1024*1024):.2f} MB)..." if expected_size else f"  [>] Downloading {remote_path}...")

    downloaded = 0
    t0 = time.time()
    last_print = t0

    with local_path.open("wb") as f:
        def callback(chunk):
            nonlocal downloaded, last_print
            f.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_print >= 2.0:
                elapsed = now - t0
                speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                pct = (downloaded / expected_size * 100) if expected_size else 0
                print(f"      {downloaded / (1024*1024):.1f}/{expected_size/(1024*1024):.1f} MB ({pct:.1f}%) - {speed:.2f} MB/s", flush=True)
                last_print = now

        ftp.retrbinary(f"RETR {remote_path}", callback, blocksize=1024 * 1024)

    elapsed = time.time() - t0
    speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
    print(f"  [✓] Downloaded {local_path.name} in {elapsed:.1f}s ({speed:.2f} MB/s).")


def dump_directory(ftp, remote_dir, local_base):
    dirs = [remote_dir]
    while dirs:
        cur = dirs.pop(0)
        lines = []
        try:
            ftp.retrlines(f"LIST {cur}", lines.append)
        except Exception as e:
            print(f"  [!] Failed to list {cur}: {e}")
            continue

        for line in lines:
            parts = line.split(None, 8)
            if len(parts) < 9:
                continue
            perms, _, _, _, size_str, _, _, _, name = parts
            if name in (".", ".."):
                continue

            full_remote = cur.rstrip("/") + "/" + name
            rel_path = full_remote[len(remote_dir):].lstrip("/")
            full_local = local_base / rel_path

            if perms.startswith("d"):
                dirs.append(full_remote)
            elif not perms.startswith("l"):
                download_file(ftp, full_remote, full_local, int(size_str))


def main():
    print("=" * 60)
    print("  PS4 SOCCER 13 Game & Seed Dumper")
    print("=" * 60)

    ftp = get_ftp_connection()

    # 1. Dump Seed Prefix files
    print("\n[+] Dumping Prefix Seed Files...")
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    seed_files = [
        "/data/prospero-win/prefixes/soccer13/system.reg",
        "/data/prospero-win/prefixes/soccer13/user.reg",
        "/data/prospero-win/prefixes/soccer13/userdef.reg",
        "/data/prospero-win/prefixes/soccer13/.update-timestamp",
        "/data/prospero-win/prefixes/soccer13/dosdevices/.pw-symlinks",
    ]
    for sf in seed_files:
        try:
            download_file(ftp, sf, SEED_DIR / Path(sf).name)
        except Exception as e:
            print(f"  [!] Could not download {sf}: {e}")

    # 2. Dump Game Files
    print("\n[+] Dumping Game Files from /data/prospero-win/prefixes/soccer13/drive_c/Games/SOCCER13...")
    dump_directory(ftp, "/data/prospero-win/prefixes/soccer13/drive_c/Games/SOCCER13", GAME_DIR)

    ftp.quit()
    print("\n[+] Game & Seed Dump completed successfully!")
    print(f"    Seed: {SEED_DIR}")
    print(f"    Game: {GAME_DIR}")


if __name__ == "__main__":
    main()
