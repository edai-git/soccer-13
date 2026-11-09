from ftplib import FTP
from pathlib import Path

def get_env():
    host = None
    port = 2121
    for name in ('.env', '.ENV', 'config.env'):
        p = Path(name)
        if p.is_file():
            for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in ('PS4_HOST', 'PS4_IP') and v:
                        host = v
                    elif k == 'PS4_FTP_PORT' and v.isdigit():
                        port = int(v)
            break
    return host, port

def main():
    host, port = get_env()
    print(f"Connecting via ftplib to {host}:{port}...")
    ftp = FTP()
    ftp.connect(host, port, timeout=10)
    ftp.login()
    print("Welcome:", ftp.getwelcome())

    print("\n--- NLST /data/prospero-win/profiles ---")
    try:
        profiles = ftp.nlst("/data/prospero-win/profiles")
        for p in profiles:
            print(" ", p)
    except Exception as e:
        print("Error:", e)

    print("\n--- NLST /data/prospero-win/logs ---")
    try:
        logs = ftp.nlst("/data/prospero-win/logs")
        for l in logs:
            print(" ", l)
    except Exception as e:
        print("Error:", e)

    # Let's download session-0.log if it exists
    for cand in ("/data/prospero-win/logs/session-0.log", "/data/prospero-win/log"):
        try:
            lines = []
            ftp.retrlines(f"RETR {cand}", lines.append)
            print(f"\n--- Content of {cand} ({len(lines)} lines) ---")
            for line in lines[:40]:
                print(line)
            if len(lines) > 40:
                print(f"... and {len(lines)-40} more lines ...")
                for line in lines[-20:]:
                    print(line)
        except Exception as e:
            pass

    # Let's read /data/prospero-win/profiles/soccer13.profile if it exists
    try:
        lines = []
        ftp.retrlines("RETR /data/prospero-win/profiles/soccer13.profile", lines.append)
        print(f"\n--- Content of /data/prospero-win/profiles/soccer13.profile ({len(lines)} lines) ---")
        for line in lines:
            print(line)
    except Exception as e:
        print("Error reading profile:", e)

    # Check prefixes
    try:
        prefixes = ftp.nlst("/data/prospero-win/prefixes")
        print("\n--- Prefixes in /data/prospero-win/prefixes ---")
        for p in prefixes:
            print(" ", p)
    except Exception as e:
        print("Error listing prefixes:", e)

    try:
        games = ftp.nlst("/data/prospero-win/prefixes/soccer13/drive_c/Games/SOCCER13")
        print("\n--- Files in soccer13 Games dir ---")
        for g in games[:20]:
            print(" ", g)
    except Exception as e:
        print("Error listing games dir:", e)

    ftp.quit()

if __name__ == '__main__':
    main()
