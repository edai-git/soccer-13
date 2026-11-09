#!/usr/bin/env python3
"""scripts/ps4-logging.py -- switch SOCCER13 diagnostics on/off on the PS4.

    python scripts/ps4-logging.py off  --host <PS4_IP>     # performance mode (default for play)
    python scripts/ps4-logging.py on   --host <PS4_IP>     # diagnostics mode (to capture bug logs)
    python scripts/ps4-logging.py status --host <PS4_IP>

Controls (all verified against orbis-win sources):
  * /data/prospero-win/radv.env      MESA_LOG_LEVEL / MESA_LOG_FILE / ORBIS_DUMP_HUNG
      (RADV default is level=info into /data/prospero-win/radv.log: ~600 lines/s)
  * soccer13.profile [debug] winedebug   (-all  vs  -all,err+ntdll)
  * soccer13.profile [display] show_fps  (on-screen FPS counter, drawn every frame)

The host comes from --host or the PS4_HOST env var (never commit an IP); the
FTP port defaults to 2121 (GoldHEN).
"""

from __future__ import annotations

import argparse
import ftplib
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "app" / "profiles" / "soccer13.profile"
RADV_ENV = ROOT / "app" / "config" / "radv.env"
REMOTE_ROOT = "/data/prospero-win"

RADV_OFF = "MESA_LOG_LEVEL=error\nMESA_LOG_FILE=/dev/null\nORBIS_DUMP_HUNG=0\n"
RADV_ON = "MESA_LOG_LEVEL=info\nMESA_LOG_FILE=/data/prospero-win/radv.log\nORBIS_DUMP_HUNG=1\n"


def set_profile_logging(text: str, enabled: bool) -> str:
    """Return profile text with winedebug and show_fps set for the mode."""
    winedebug = "-all,err+ntdll" if enabled else "-all"
    show_fps = "true" if enabled else "false"
    text = re.sub(r"(?m)^winedebug\s*=.*$", f"winedebug = {winedebug}", text)
    if re.search(r"(?m)^show_fps\s*=", text):
        text = re.sub(r"(?m)^show_fps\s*=.*$", f"show_fps = {show_fps}", text)
    else:
        text = re.sub(r"(?m)^(scaling\s*=.*)$", rf"\1\nshow_fps = {show_fps}", text, count=1)
    return text


def upload(ftp: ftplib.FTP, remote: str, data: bytes) -> None:
    try:
        ftp.delete(remote)  # GoldHEN FTP refuses STOR over an existing file
    except ftplib.error_perm:
        pass
    ftp.storbinary(f"STOR {remote}", io.BytesIO(data))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["on", "off", "status"])
    ap.add_argument("--host", default=os.environ.get("PS4_HOST"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PS4_FTP_PORT", "2121")))
    ap.add_argument("--local-only", action="store_true", help="only rewrite the files under app/")
    args = ap.parse_args()

    if args.mode == "status":
        print("radv.env :", RADV_ENV.read_text().strip().replace("\n", " "))
        print("profile  :", [l for l in PROFILE.read_text().splitlines() if l.startswith(("winedebug", "show_fps"))])
        return 0

    enabled = args.mode == "on"
    RADV_ENV.write_text(RADV_ON if enabled else RADV_OFF, newline="\n")
    profile_text = set_profile_logging(PROFILE.read_text(encoding="utf-8"), enabled)
    PROFILE.write_text(profile_text, encoding="utf-8", newline="\n")
    print(f"[+] local app/ files set to logging {args.mode.upper()}")

    if args.local_only:
        return 0
    if not args.host:
        print("[!] no --host / PS4_HOST: local files updated only", file=sys.stderr)
        return 1

    ftp = ftplib.FTP()
    ftp.connect(args.host, args.port, timeout=10)
    ftp.login()
    upload(ftp, f"{REMOTE_ROOT}/radv.env", RADV_ENV.read_bytes())
    upload(ftp, f"{REMOTE_ROOT}/profiles/soccer13.profile", profile_text.encode("utf-8"))
    if not enabled:
        try:
            ftp.delete(f"{REMOTE_ROOT}/radv.log")
        except ftplib.error_perm:
            pass
    ftp.quit()
    print(f"[+] uploaded radv.env + soccer13.profile to {REMOTE_ROOT}; relaunch the game to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())

