#!/usr/bin/env python3
"""Upload the full booted bare prefix to PS4 GoldHEN FTP at /data/prospero-win/prefixes/soccer13.

Preserves drive_c/Games/SOCCER13 entirely!
Skips files that already exist on PS4 with matching size.
"""
import ftplib
import os
import sys
import time
from pathlib import Path, PurePosixPath

HOST = "192.168.11.11"
PORT = 2121
LOCAL_PREFIX = Path(r"d:\dev\DEV\other\ps4\soccer13\build\bare-prefix").resolve()
REMOTE_PREFIX = "/data/prospero-win/prefixes/soccer13"


def main():
    if not LOCAL_PREFIX.is_dir():
        print(f"Error: {LOCAL_PREFIX} does not exist", file=sys.stderr)
        return 1

    all_paths = sorted(LOCAL_PREFIX.rglob("*"))
    files = [p for p in all_paths if p.is_file()]
    dirs = [p for p in all_paths if p.is_dir()]

    print(f"Connecting to GoldHEN FTP at {HOST}:{PORT}...")
    ftp = ftplib.FTP(timeout=30)
    ftp.connect(HOST, PORT)
    ftp.login()
    print("Connected successfully!")

    # Step 1: Ensure all directories exist
    print(f"Ensuring {len(dirs)} directories exist on PS4...")
    created_dirs = set()
    for d in sorted(dirs, key=lambda p: (len(p.parts), p)):
        rel = d.relative_to(LOCAL_PREFIX).as_posix()
        rem_dir = f"{REMOTE_PREFIX}/{rel}"
        # Build path recursively
        parts = PurePosixPath(rem_dir).parts
        for i in range(2, len(parts) + 1):
            sub = str(PurePosixPath(*parts[:i]))
            if sub not in created_dirs:
                try:
                    ftp.mkd(sub)
                except ftplib.error_perm as e:
                    if not str(e).startswith("550"):
                        pass
                created_dirs.add(sub)

    # Step 2: Query remote file sizes where possible to skip unchanged files
    print(f"Checking {len(files)} files to upload...")
    to_upload = []
    skipped = 0
    for f in files:
        rel = f.relative_to(LOCAL_PREFIX).as_posix()
        rem_file = f"{REMOTE_PREFIX}/{rel}"
        local_size = f.stat().st_size
        try:
            rem_size = ftp.size(rem_file)
            if rem_size == local_size:
                skipped += 1
                continue
        except Exception:
            pass
        to_upload.append((f, rem_file, local_size))

    print(f"Already up-to-date: {skipped} files. To upload: {len(to_upload)} files.")

    total_bytes = sum(s for _, _, s in to_upload)
    uploaded_bytes = 0
    start_time = time.time()

    for idx, (local_path, remote_path, file_size) in enumerate(to_upload, 1):
        with open(local_path, "rb") as fp:
            ftp.storbinary(f"STOR {remote_path}", fp, blocksize=65536)
        uploaded_bytes += file_size
        elapsed = time.time() - start_time
        speed = (uploaded_bytes / 1024 / 1024) / elapsed if elapsed > 0 else 0
        percent = (uploaded_bytes / total_bytes * 100) if total_bytes > 0 else 100
        if idx % 25 == 0 or idx == len(to_upload) or file_size > 1024 * 1024:
            print(
                f"[{idx}/{len(to_upload)}] {percent:5.1f}% | "
                f"{uploaded_bytes / 1024 / 1024:.1f}/{total_bytes / 1024 / 1024:.1f} MB | "
                f"{speed:.2f} MB/s | {local_path.name}"
            )

    print("\nVerifying uploaded files on PS4...")
    for check_file in ["system.reg", "user.reg", "userdef.reg", ".update-timestamp"]:
        try:
            sz = ftp.size(f"{REMOTE_PREFIX}/{check_file}")
            print(f"  {check_file}: {sz} bytes (OK)")
        except Exception as e:
            print(f"  {check_file}: ERROR ({e})")

    try:
        sz = ftp.size(f"{REMOTE_PREFIX}/drive_c/windows/syswow64/d3d9.dll")
        print(f"  syswow64/d3d9.dll: {sz} bytes (OK)")
    except Exception as e:
        print(f"  syswow64/d3d9.dll: ERROR ({e})")

    ftp.quit()
    print("\nBare prefix upload complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

