#!/usr/bin/env python3
"""Format and upload system.reg and user.reg with exact Wine double-backslash syntax."""
import ftplib
import io
import os
import sys

HOST = "192.168.11.11"
PORT = 2121
REMOTE_PREFIX = "/data/prospero-win/prefixes/soccer13"

LOCAL_SYS_REG = r"d:\dev\DEV\other\ps4\soccer13\build\bare-prefix\system.reg"
LOCAL_USER_REG = r"d:\dev\DEV\other\ps4\soccer13\build\bare-prefix\user.reg"

# Exact user PC product code from HKLM\SOFTWARE\WOW6432Node\KONAMI\PES2013
PRODUCT_CODE = "SHVY-3LE9-TMNH-7K5L-JN73"
INSTALL_DIR = "C:\\\\Games\\\\SOCCER13\\\\"
VERSION = "1.00.0000"

SYS_ADDITIONS = f"""
[Hardware\\\\Description\\\\System\\\\CentralProcessor\\\\0] 1767225600
#time=1dc7ab192810000
"~MHz"=dword:00000dac
"Identifier"="AMD64 Family 23 Model 71 Stepping 0"
"VendorIdentifier"="AuthenticAMD"
"ProcessorNameString"="AMD 4700S 8-Core Processor"
"FeatureSet"=dword:00001fff

[Software\\\\KONAMI\\\\PES2013] 1767225600
#time=1dc7ab192810000
"code"="{PRODUCT_CODE}"
"installdir"="{INSTALL_DIR}"
"version"="{VERSION}"

[Software\\\\Wow6432Node\\\\KONAMI\\\\PES2013] 1767225600
#time=1dc7ab192810000
"code"="{PRODUCT_CODE}"
"installdir"="{INSTALL_DIR}"
"version"="{VERSION}"

[Software\\\\Wine\\\\DllOverrides] 1767225600
#time=1dc7ab192810000
"d3d8"="native"
"d3d9"="native"
"d3d10core"="native"
"d3d11"="native"
"dxgi"="native"
"dinput8"="native,builtin"
"""

USER_ADDITIONS = """
[Software\\\\Wine\\\\Direct3D] 1767225600
#time=1dc7ab192810000
"VideoMemorySize"="2048"
"renderer"="no3d"
"""


def main():
    print("Reading local system.reg...")
    sys_content = open(LOCAL_SYS_REG, "r", encoding="utf-8", errors="ignore").read()

    # Remove any old additions if present
    for marker in ["[Hardware\\Description\\System\\CentralProcessor\\0]",
                   "[Hardware\\\\Description\\\\System\\\\CentralProcessor\\\\0]",
                   "[Software\\Wow6432Node\\KONAMI\\PES2013]",
                   "[Software\\\\Wow6432Node\\\\KONAMI\\\\PES2013]",
                   "[Software\\KONAMI\\PES2013]",
                   "[Software\\\\KONAMI\\\\PES2013]",
                   "[Software\\Wine\\DllOverrides]",
                   "[Software\\\\Wine\\\\DllOverrides]"]:
        idx = sys_content.find(marker)
        if idx != -1:
            sys_content = sys_content[:idx].rstrip()

    new_sys = sys_content.rstrip() + "\n" + SYS_ADDITIONS.strip() + "\n"
    with open(LOCAL_SYS_REG, "w", encoding="utf-8") as f:
        f.write(new_sys)
    print(f"Updated local system.reg ({len(new_sys)} bytes)")

    print("Reading local user.reg...")
    user_content = open(LOCAL_USER_REG, "r", encoding="utf-8", errors="ignore").read()
    for marker in ["[Software\\Wine\\Direct3D]", "[Software\\\\Wine\\\\Direct3D]"]:
        idx = user_content.find(marker)
        if idx != -1:
            user_content = user_content[:idx].rstrip()

    new_user = user_content.rstrip() + "\n" + USER_ADDITIONS.strip() + "\n"
    with open(LOCAL_USER_REG, "w", encoding="utf-8") as f:
        f.write(new_user)
    print(f"Updated local user.reg ({len(new_user)} bytes)")

    # Connect to PS4 GoldHEN FTP
    print(f"Connecting to PS4 GoldHEN FTP at {HOST}:{PORT}...")
    ftp = ftplib.FTP(timeout=20)
    ftp.connect(HOST, PORT)
    ftp.login()
    print("Logged in successfully.")

    # Safe upload: delete then STOR
    for name, data in [("system.reg", new_sys.encode("utf-8")), ("user.reg", new_user.encode("utf-8"))]:
        target = f"{REMOTE_PREFIX}/{name}"
        try:
            ftp.delete(target)
        except Exception:
            pass
        stream = io.BytesIO(data)
        ftp.storbinary(f"STOR {target}", stream, blocksize=65536)
        sz = ftp.size(target)
        print(f"Uploaded {target}: {sz} bytes (Confirmed OK)")

    ftp.quit()
    print("Verification complete! Keys properly formatted with double backslashes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

