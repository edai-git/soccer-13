#!/usr/bin/env python3
"""scripts/install-soccer13.py — Deploy staged SOCCER13 profile and prefix to PS4 HEN or USB.

Uploads to:
- /data/prospero-win/profiles/soccer13.profile
- /data/prospero-win/prefixes/soccer13/

Features:
- Minimal GoldHEN FTP (TYPE I / PASV / STOR, zero lftp, no MLSD)
- Resumable upload: saves progress in state JSON
- Offline USB export mode (--usb-out)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import socket
import sys
import time

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_STATE = PROJECT_ROOT / "build/soccer13-upload-state.json"


def load_env_defaults() -> tuple[str | None, int]:
    """Reads PS4_IP / PS4_HOST and PS4_FTP_PORT from .env, .ENV, or config.env."""
    host = None
    port = 2121
    for name in (".env", ".ENV", "config.env"):
        env_path = PROJECT_ROOT / name
        if env_path.is_file():
            for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in ("PS4_HOST", "PS4_IP") and v:
                    host = v
                elif k == "PS4_FTP_PORT" and v.isdigit():
                    port = int(v)
            break
    return host, port


class GoldHENClient:
    def __init__(self, host: str, port: int = 2121, timeout: int = 20):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.ctl = socket.create_connection((host, port), timeout=timeout)
        self.reader = self.ctl.makefile("rb")
        self.read_reply()
        self.command("TYPE I")

    def read_reply(self) -> str:
        line = self.reader.readline()
        if not line:
            raise ConnectionError("PS4 closed control connection")
        text = line.decode("utf-8", "replace").rstrip()
        return text

    def command(self, cmd: str) -> str:
        self.ctl.sendall((cmd + "\r\n").encode("utf-8"))
        reply = self.read_reply()
        return reply

    def ensure_remote_dir(self, remote_dir: str) -> None:
        parts = [p for p in remote_dir.split("/") if p]
        curr = ""
        for p in parts:
            curr += "/" + p
            self.command(f"MKD {curr}")

    def put_file(self, local_path: Path, remote_path: str, progress_cb=None) -> None:
        size = local_path.stat().st_size
        parent_dir = remote_path.rsplit("/", 1)[0]
        self.ensure_remote_dir(parent_dir)

        reply = self.command("PASV")
        if not reply.startswith("227"):
            raise RuntimeError(f"PASV error: {reply}")
        # parse 227 Entering Passive Mode (h1,h2,h3,h4,p1,p2)
        start = reply.index("(") + 1
        end = reply.index(")")
        parts = reply[start:end].split(",")
        d_host = ".".join(parts[:4])
        d_port = int(parts[4]) * 256 + int(parts[5])

        data_conn = socket.create_connection((d_host, d_port), timeout=self.timeout)
        sent = 0
        try:
            stor_reply = self.command(f"STOR {remote_path}")
            if not stor_reply.startswith(("125", "150")):
                raise RuntimeError(f"STOR refused: {stor_reply}")
            with local_path.open("rb") as f:
                while True:
                    chunk = f.read(256 * 1024)
                    if not chunk:
                        break
                    data_conn.sendall(chunk)
                    sent += len(chunk)
                    if progress_cb:
                        progress_cb(sent, size)
        finally:
            data_conn.close()

        final_reply = self.read_reply()
        if not final_reply.startswith("226"):
            raise RuntimeError(f"STOR failed: {final_reply}")


def main() -> int:
    default_host, default_port = load_env_defaults()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=PROJECT_ROOT / "build/staged-prefix/soccer13")
    parser.add_argument("--profile", type=Path, default=PROJECT_ROOT / "app/profiles/soccer13.profile")
    parser.add_argument("--host", default=default_host, help="PS4 IP address (defaults to .env PS4_IP/PS4_HOST)")
    parser.add_argument("--port", type=int, default=default_port, help="GoldHEN FTP port (default: 2121)")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE, help="Upload resume state file")
    parser.add_argument("--usb-out", type=Path, help="Export to USB folder instead of network upload")
    parser.add_argument("--check", action="store_true", help="Only verify GoldHEN FTP connection and exit")
    args = parser.parse_args()

    if args.check:
        if not args.host:
            print("[-] PS4_IP / PS4_HOST belum diatur di .env / .ENV atau --host.")
            return 2
        print(f"[+] Memeriksa koneksi FTP ke PS4 ({args.host}:{args.port})...")
        try:
            client = GoldHENClient(args.host, args.port, timeout=5)
            pwd_reply = client.command("PWD")
            client.ctl.close()
            print(f"[OK] TERHUBUNG! GoldHEN FTP aktif di {args.host}:{args.port} ({pwd_reply})")
            return 0
        except Exception as exc:
            print(f"[-] GAGAL terhubung ke {args.host}:{args.port}: {exc}")
            return 1

    if not args.prefix.is_dir():
        print(f"[-] Staged prefix not found: {args.prefix}")
        print("    Run scripts/stage-soccer13-prefix.py first!")
        return 1
    if not args.profile.is_file():
        print(f"[-] Profile not found: {args.profile}")
        return 1

    # Mode 1: USB Export
    if args.usb_out:
        target_usb = args.usb_out.resolve()
        print(f"[+] Exporting to USB destination: {target_usb}...")
        usb_profiles = target_usb / "SOCCER13/profiles"
        usb_prefixes = target_usb / "SOCCER13/prefixes/soccer13"
        usb_profiles.mkdir(parents=True, exist_ok=True)
        usb_prefixes.mkdir(parents=True, exist_ok=True)

        shutil.copy2(args.profile, usb_profiles / "soccer13.profile")
        for p in args.prefix.rglob("*"):
            rel = p.relative_to(args.prefix)
            dst = usb_prefixes / rel
            if p.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            elif p.is_file():
                shutil.copy2(p, dst)
        print(f"[+] USB export complete at {target_usb}/SOCCER13")
        return 0

    # Mode 2: Network GoldHEN FTP Upload
    if not args.host:
        print("[-] Host required for network upload. Pass --host <PS4_IP> or use --usb-out <DIR>")
        return 2

    # Load resume state
    state = {}
    if args.state.is_file():
        try:
            state = json.loads(args.state.read_text(encoding="utf-8")).get("completed", {})
        except Exception:
            state = {}

    print(f"[+] Connecting to GoldHEN FTP at {args.host}:{args.port}...")
    client = GoldHENClient(args.host, args.port)

    # 1. Upload profile
    rem_profile = "/data/prospero-win/profiles/soccer13.profile"
    print(f"[+] Uploading profile -> {rem_profile}...")
    client.put_file(args.profile, rem_profile)

    # 2. Upload prefix files
    all_files = [p for p in args.prefix.rglob("*") if p.is_file()]
    total_files = len(all_files)
    print(f"[+] Uploading prefix ({total_files} files) -> /data/prospero-win/prefixes/soccer13/...")

    for idx, local_file in enumerate(all_files, start=1):
        rel = local_file.relative_to(args.prefix).as_posix()
        rem_path = f"/data/prospero-win/prefixes/soccer13/{rel}"
        mtime = int(local_file.stat().st_mtime)
        size = local_file.stat().st_size

        if state.get(rel) == {"size": size, "mtime": mtime}:
            continue  # Already transferred

        print(f"[{idx}/{total_files}] Uploading {rel} ({size // 1024} KB)...")
        client.put_file(local_file, rem_path)
        state[rel] = {"size": size, "mtime": mtime}

        # Save checkpoint
        args.state.parent.mkdir(parents=True, exist_ok=True)
        args.state.write_text(json.dumps({"completed": state}), encoding="utf-8")

    print("[+] SOCCER13 installation transfer completed successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

