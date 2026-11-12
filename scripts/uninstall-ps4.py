#!/usr/bin/env python3
"""scripts/uninstall-ps4.py — Remove SOCCER13 runtime data from a PS4 via FTP.

PS4 (Orbis OS) provides NO uninstall hook for homebrew packages: deleting the
SOCCER13 app from the XMB only removes /user/app/GLDS13013. Data created at
runtime under /data/prospero-win/ stays behind. Run this script (PS4 online,
GoldHEN FTP enabled) after/before uninstalling the app to remove:

  /data/prospero-win/prefixes/soccer13        (Wine prefix incl. saves/EDIT.bin)
  /data/prospero-win/profiles/soccer13*        (runtime profiles)
  /data/prospero-win/prefixes/soccer13*.log    (and logs/soccer13*)

Usage:
  python3 scripts/uninstall-ps4.py            # asks for confirmation
  python3 scripts/uninstall-ps4.py --yes      # no prompt
  python3 scripts/uninstall-ps4.py --backup-saves   # download save/ first

PS4_IP / PS4_FTP_PORT are read from environment or the gitignored .env file.
"""

import argparse
import ftplib
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.strip().split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

PS4_IP = os.environ.get("PS4_IP", "10.0.0.1")
PS4_FTP_PORT = int(os.environ.get("PS4_FTP_PORT", "2121"))

BASE = "/data/prospero-win"
PREFIX = f"{BASE}/prefixes/soccer13"
SAVE_DIRS = [
    f"{PREFIX}/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/save",
    f"{PREFIX}/drive_c/users/root/Documents/KONAMI/Pro Evolution Soccer 2013/save",
]


def list_entries(ftp, path):
    """Return [(name, is_dir)] using MLSD when available, LIST otherwise."""
    entries = []
    try:
        for name, facts in ftp.mlsd(path):
            if name in (".", ".."):
                continue
            entries.append((name, facts.get("type") == "dir"))
        return entries
    except ftplib.error_perm:
        pass
    lines = []
    ftp.retrlines(f"LIST {path}", lines.append)
    for line in lines:
        parts = line.split(None, 8)
        if len(parts) < 9 or parts[8] in (".", ".."):
            continue
        entries.append((parts[8], line.startswith("d")))
    return entries


def rm_tree(ftp, path):
    try:
        entries = list_entries(ftp, path)
    except ftplib.all_errors:
        return
    for name, is_dir in entries:
        child = f"{path}/{name}"
        if is_dir:
            rm_tree(ftp, child)
        else:
            try:
                ftp.delete(child)
            except ftplib.all_errors as e:
                print(f"[!] delete failed {child}: {e}")
    try:
        ftp.rmd(path)
        print(f"[-] removed {path}")
    except ftplib.all_errors as e:
        print(f"[!] rmd failed {path}: {e}")


def backup_saves(ftp):
    out = PROJECT_ROOT / "build" / "save-backup"
    for remote in SAVE_DIRS:
        try:
            entries = list_entries(ftp, remote)
        except ftplib.all_errors:
            continue
        dest = out / remote.split("/users/")[1].split("/")[0]
        dest.mkdir(parents=True, exist_ok=True)
        for name, is_dir in entries:
            if is_dir:
                continue
            with open(dest / name, "wb") as f:
                ftp.retrbinary(f"RETR {remote}/{name}", f.write)
            print(f"[+] backed up {name} -> {dest}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--yes", action="store_true", help="skip confirmation")
    ap.add_argument("--backup-saves", action="store_true", help="download save/ to build/save-backup first")
    args = ap.parse_args()

    if not args.yes:
        ans = input(f"Delete SOCCER13 data (prefix + profiles + saves) on {PS4_IP}? [y/N] ")
        if ans.strip().lower() != "y":
            print("Aborted.")
            return 1

    ftp = ftplib.FTP()
    ftp.connect(PS4_IP, PS4_FTP_PORT, timeout=30)
    ftp.login()

    if args.backup_saves:
        backup_saves(ftp)

    rm_tree(ftp, PREFIX)
    for sub in ("profiles", "logs", "prefixes"):
        try:
            for name, is_dir in list_entries(ftp, f"{BASE}/{sub}"):
                if name.lower().startswith("soccer13"):
                    p = f"{BASE}/{sub}/{name}"
                    if is_dir:
                        rm_tree(ftp, p)
                    else:
                        ftp.delete(p)
                        print(f"[-] removed {p}")
        except ftplib.all_errors:
            pass
    ftp.quit()
    print("[+] SOCCER13 data removed. Uninstall the app from the PS4 Home Screen if not done yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

