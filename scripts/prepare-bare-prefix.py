import os
import shutil

prefix_dir = r"d:\dev\DEV\other\ps4\soccer13\build\bare-prefix"

# Ensure Games does not exist in bare-prefix
games_dir = os.path.join(prefix_dir, "drive_c", "Games")
if os.path.exists(games_dir):
    shutil.rmtree(games_dir)

# Ensure wow64native.dll in syswow64
sys32_wow = os.path.join(prefix_dir, "drive_c", "windows", "system32", "wow64native.dll")
syswow_wow = os.path.join(prefix_dir, "drive_c", "windows", "syswow64", "wow64native.dll")
if os.path.exists(sys32_wow) and not os.path.exists(syswow_wow):
    shutil.copy(sys32_wow, syswow_wow)
    print("Copied wow64native.dll to syswow64")

# Ensure settings.dat in Documents
doc_dir = os.path.join(prefix_dir, "drive_c", "users", "prospero", "Documents", "KONAMI", "Pro Evolution Soccer 2013")
os.makedirs(doc_dir, exist_ok=True)
staged_dat = r"d:\dev\DEV\other\ps4\soccer13\build\staged-prefix\soccer13\drive_c\users\prospero\Documents\KONAMI\Pro Evolution Soccer 2013\settings.dat"
if os.path.exists(staged_dat):
    shutil.copy(staged_dat, os.path.join(doc_dir, "settings.dat"))
    print("Copied settings.dat to Documents")

# Append Konami registry and DllOverrides to system.reg
sys_reg = os.path.join(prefix_dir, "system.reg")
reg_content = open(sys_reg, "r", encoding="utf-8", errors="ignore").read()
if "KONAMI" not in reg_content:
    print("Appending Konami keys and DllOverrides to system.reg...")
    additions = (
        "\n[Software\\Wine\\DllOverrides] 1767225600\n"
        "#time=1dc7ab192810000\n"
        '"d3d8"="native"\n'
        '"d3d9"="native"\n'
        '"d3d10core"="native"\n'
        '"d3d11"="native"\n'
        '"dxgi"="native"\n'
        '"dinput8"="native,builtin"\n'
        "\n[Software\\Wow6432Node\\KONAMI\\PES2013] 1767225600\n"
        "#time=1dc7ab192810000\n"
        '"code"="4NDR-G9KM-G52X-V37R-XWLF"\n'
        '"installdir"="C:\\\\Games\\\\SOCCER13\\\\"\n'
        '"version"="1.0.0.0"\n'
    )
    with open(sys_reg, "a", encoding="utf-8") as f:
        f.write(additions)

total_files = 0
total_bytes = 0
for root, dirs, files in os.walk(prefix_dir):
    for f in files:
        total_files += 1
        total_bytes += os.path.getsize(os.path.join(root, f))
print(f"Total files: {total_files}, Total size: {total_bytes / (1024*1024):.2f} MB")

