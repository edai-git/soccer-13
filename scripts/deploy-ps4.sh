#!/usr/bin/env bash
# scripts/deploy-ps4.sh — Safe deploy, log retrieval and monitoring for PS4 HEN
# Adheres strictly to NFR-05: never hardcodes IP addresses or credentials.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# Load configuration from gitignored .env, .ENV, or config.env (strip CRLF if edited on Windows)
for env_candidate in "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.ENV" "$PROJECT_ROOT/config.env"; do
  if [[ -f "$env_candidate" ]]; then
    # shellcheck disable=SC1090
    source <(tr -d '\r' < "$env_candidate")
    break
  fi
done

PS4_HOST="${PS4_HOST:-${PS4_IP:-}}"
PS4_FTP_PORT="${PS4_FTP_PORT:-2121}"
PS4_LOG_PORT="${PS4_LOG_PORT:-9300}"

FTP_PUT="$PROJECT_ROOT/runtime/orbis-win/scripts/ftp-put.py"
FTP_GET="$PROJECT_ROOT/runtime/orbis-win/scripts/ftp-get.py"
PS5LOGD="$PROJECT_ROOT/runtime/orbis-win/scripts/ps5logd.py"

usage() {
  echo "Usage: $0 <command> [args...]"
  echo ""
  echo "Commands:"
  echo "  status                       Check network and FTP connection to PS4"
  echo "  push-profile <profile_file>  Upload game profile to /data/prospero-win/profiles/"
  echo "  push-file <local> <remote>   Upload a file safely to PS4 via GoldHEN FTP"
  echo "  fetch-logs [output_dir]      Download session-0..7 logs to artifacts/logs/"
  echo "  analyze-logs [log_file]      Analyze PS4 session log with 12-stage evaluator"
  echo "  install-soccer13 <game_dir>  Stage and install game & mods to PS4 HEN"
  echo "  listen-logs [port]           Run TCP ps5logd listener (default: $PS4_LOG_PORT)"
  echo ""
  echo "Configuration:"
  echo "  Set PS4_HOST in .env or config.env (do NOT commit to git)."
  echo "  Current PS4_HOST: ${PS4_HOST:-[NOT SET]}"
  echo "  Current PS4_FTP_PORT: $PS4_FTP_PORT"
  echo "  Current PS4_LOG_PORT: $PS4_LOG_PORT"
  exit 1
}

require_host() {
  if [[ -z "$PS4_HOST" ]]; then
    echo "[-] ERROR: PS4_HOST is not set." >&2
    echo "    Create a .env or config.env file with: PS4_HOST=192.168.x.x" >&2
    exit 1
  fi
}

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
  status)
    require_host
    echo "[+] Checking connection to PS4 ($PS4_HOST:$PS4_FTP_PORT)..."
    if ping -c 1 -W 2 "$PS4_HOST" >/dev/null 2>&1; then
      echo "    Ping: OK"
    else
      echo "    Ping: FAILED or ICMP blocked"
    fi
    # Check FTP port
    if nc -z -w 3 "$PS4_HOST" "$PS4_FTP_PORT" 2>/dev/null || (exec 3<>/dev/tcp/"$PS4_HOST"/"$PS4_FTP_PORT" && exec 3<&-) 2>/dev/null; then
      echo "    GoldHEN FTP ($PS4_FTP_PORT): OPEN"
    else
      echo "    GoldHEN FTP ($PS4_FTP_PORT): CLOSED or UNREACHABLE"
    fi
    ;;

  push-profile)
    require_host
    PROFILE_FILE="${1:-}"
    if [[ -z "$PROFILE_FILE" || ! -f "$PROFILE_FILE" ]]; then
      echo "[-] ERROR: Valid profile file required." >&2
      exit 1
    fi
    FILENAME=$(basename "$PROFILE_FILE")
    REMOTE_PATH="/data/prospero-win/profiles/$FILENAME"
    echo "[+] Uploading profile $PROFILE_FILE -> $REMOTE_PATH..."
    python3 "$FTP_PUT" "$PS4_HOST" "$PS4_FTP_PORT" "$PROFILE_FILE" "$REMOTE_PATH"
    echo "[+] Profile uploaded successfully."
    ;;

  push-file)
    require_host
    LOCAL_FILE="${1:-}"
    REMOTE_PATH="${2:-}"
    if [[ -z "$LOCAL_FILE" || ! -f "$LOCAL_FILE" || -z "$REMOTE_PATH" ]]; then
      echo "[-] ERROR: Usage: $0 push-file <local_file> <remote_path>" >&2
      exit 1
    fi
    echo "[+] Uploading $LOCAL_FILE -> $REMOTE_PATH..."
    python3 "$FTP_PUT" "$PS4_HOST" "$PS4_FTP_PORT" "$LOCAL_FILE" "$REMOTE_PATH"
    echo "[+] Upload completed."
    ;;

  fetch-logs)
    require_host
    LOG_OUT="${1:-$PROJECT_ROOT/artifacts/logs}"
    mkdir -p "$LOG_OUT"
    echo "[+] Fetching runtime session logs from /data/prospero-win/logs/ to $LOG_OUT..."
    for i in {0..7}; do
      REMOTE_LOG="/data/prospero-win/logs/session-$i.log"
      LOCAL_LOG="$LOG_OUT/session-$i.log"
      python3 "$FTP_GET" "$PS4_HOST" "$PS4_FTP_PORT" "$REMOTE_LOG" "$LOCAL_LOG" 2>/dev/null || true
    done
    echo "[+] Log retrieval completed. Check $LOG_OUT."
    ;;

  analyze-logs)
    LOG_FILE="${1:-$PROJECT_ROOT/artifacts/logs/session-0.log}"
    if [[ ! -f "$LOG_FILE" ]]; then
      echo "[-] Log file not found at: $LOG_FILE" >&2
      echo "    Run ./scripts/deploy-ps4.sh fetch-logs first or pass path to log file." >&2
      exit 1
    fi
    python3 "$PROJECT_ROOT/scripts/analyze-session-log.py" "$LOG_FILE"
    ;;

  install-soccer13)
    require_host
    GAME_DIR="${1:-}"
    if [[ -z "$GAME_DIR" || ! -d "$GAME_DIR" ]]; then
      echo "[-] ERROR: Valid game directory required." >&2
      echo "    Usage: $0 install-soccer13 <path_to_game_with_pes2013_and_img>" >&2
      exit 1
    fi
    STAGE_DIR="$PROJECT_ROOT/build/staged-prefix/soccer13"
    echo "[+] Step 1: Staging SOCCER13 prefix & mods..."
    python3 "$PROJECT_ROOT/scripts/stage-soccer13-prefix.py" "$STAGE_DIR" --game-source "$GAME_DIR"
    echo "[+] Step 2: Uploading profile & prefix to PS4 ($PS4_HOST:$PS4_FTP_PORT)..."
    python3 "$PROJECT_ROOT/scripts/install-soccer13.py" --prefix "$STAGE_DIR" --host "$PS4_HOST" --port "$PS4_FTP_PORT"
    ;;

  listen-logs)
    LISTEN_PORT="${1:-$PS4_LOG_PORT}"
    echo "[+] Starting ps5logd listener on port $LISTEN_PORT..."
    python3 "$PS5LOGD" "$LISTEN_PORT"
    ;;

  help|*)
    usage
    ;;
esac

