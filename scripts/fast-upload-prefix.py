#!/usr/bin/env python3
"""High-performance bare prefix uploader for PS4 GoldHEN FTP."""
import ftplib
import os
import sys
import time
from pathlib import Path, PurePosixPath

HOST = "192.168.11.11"
PORT = 2121
LOCAL_PREFIX = Path(r"d:\dev\DEV\other\ps4\soccer13\build\bare-prefix").resolve()
REMOTE_PREFIX = "/data/prospero-win/prefixes/soccer13"


def safe_stor(ftp, target, local_path):
    with local_path.open("rb") as stream:
        try:
            ftp.storbinary(f"STOR {target}", stream, blocksize=65536)
        except ftplib.error_perm as e:
            if "550" in str(e):
                # GoldHEN FTP v2.2 rejects overwriting existing files: delete then retry
                try:
                    ftp.delete(target)
                except Exception:
                    pass
                stream.seek(0)
                ftp.storbinary(f"STOR {target}", stream, blocksize=65536)
            else:
                raise


def main():
    if not LOCAL_PREFIX.is_dir():
        print(f"Error: {LOCAL_PREFIX} not found", file=sys.stderr)
        return 1

    all_paths = sorted(LOCAL_PREFIX.rglob("*"))
    files = [p for p in all_paths if p.is_file()]
    dirs = [p for p in all_paths if p.is_dir()]

    print(f"Connecting to GoldHEN FTP {HOST}:{PORT}...", flush=True)
    ftp = ftplib.FTP(timeout=30)
    ftp.connect(HOST, PORT)
    ftp.login()
    print("Logged in successfully (anonymous).", flush=True)

    # 1. Create directories
    print(f"Ensuring {len(dirs)} directories exist...", flush=True)
    created = set()
    for d in sorted(dirs, key=lambda p: (len(p.parts), p)):
        rel = d.relative_to(LOCAL_PREFIX).as_posix()
        rem_dir = f"{REMOTE_PREFIX}/{rel}"
        parts = PurePosixPath(rem_dir).parts
        for i in range(2, len(parts) + 1):
            sub = str(PurePosixPath(*parts[:i]))
            if sub not in created:
                try:
                    ftp.mkd(sub)
                except ftplib.error_perm:
                    pass
                created.add(sub)

    # 2. Upload files
    total_files = len(files)
    total_bytes = sum(f.stat().st_size for f in files)
    print(f"Uploading {total_files} files ({total_bytes / (1024*1024):.1f} MB)...", flush=True)

    uploaded_bytes = 0
    start_time = time.time()

    for idx, path in enumerate(files, 1):
        rel = path.relative_to(LOCAL_PREFIX).as_posix()
        target = f"{REMOTE_PREFIX}/{rel}"
        sz = path.stat().st_size

        safe_stor(ftp, target, path)

        uploaded_bytes += sz
        elapsed = time.time() - start_time
        speed = (uploaded_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
        pct = (uploaded_bytes / total_bytes) * 100

        if idx % 50 == 0 or idx == total_files or sz > 2 * 1024 * 1024:
            print(
                f"[{idx:4d}/{total_files}] {pct:5.1f}% | "
                f"{uploaded_bytes / (1024*1024):.1f}/{total_bytes / (1024*1024):.1f} MB | "
                f"{speed:.2f} MB/s | {path.name}",
                flush=True,
            )

    print("\n--- Upload Complete! Verifying key files on PS4 ---", flush=True)
    checks = [
        "system.reg",
        "user.reg",
        "userdef.reg",
        ".update-timestamp",
        "dosdevices/.pw-symlinks",
        "drive_c/windows/syswow64/d3d9.dll",
        "drive_c/windows/syswow64/wow64native.dll",
        "drive_c/windows/system32/wowprospero.dll",
        "drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/settings.dat",
    ]
    for chk in checks:
        target = f"{REMOTE_PREFIX}/{chk}"
        try:
            sz = ftp.size(target)
            print(f"  OK: {chk} ({sz} bytes)", flush=True)
        except Exception as e:
            print(f"  FAIL: {chk} ({e})", flush=True)

    ftp.quit()
    print("Done!", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
