#!/usr/bin/env bash
# scripts/docker-entrypoint.sh — CLI dispatcher inside Docker container
set -euo pipefail

cd /workspace

CMD="${1:-bash}"
shift || true

case "$CMD" in
  build)
    exec /workspace/scripts/build.sh "$@"
    ;;
  test)
    exec /workspace/scripts/test.sh "$@"
    ;;
  release)
    exec /workspace/scripts/release.sh "$@"
    ;;
  clean)
    exec /workspace/scripts/build.sh --clean "$@"
    ;;
  validate)
    exec /workspace/scripts/validate.sh "$@"
    ;;
  package)
    exec /workspace/scripts/package.sh "$@"
    ;;
  bash|sh)
    exec /bin/bash "$@"
    ;;
  *)
    exec "$CMD" "$@"
    ;;
esac

