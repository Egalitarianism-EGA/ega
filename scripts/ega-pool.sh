#!/usr/bin/env bash
# Start EGA pool dashboard + stratum (ports 8089 / 3333)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/src/ega-cli"

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Starting node..."
  bash "$ROOT/scripts/easy-start.sh"
  sleep 2
fi

export EGA_POOL_HOST="${EGA_POOL_HOST:-0.0.0.0}"
export EGA_POOL_WEB_PORT="${EGA_POOL_WEB_PORT:-8089}"
export EGA_POOL_STRATUM_PORT="${EGA_POOL_STRATUM_PORT:-3333}"
export EGA_POOL_ALGO="${EGA_POOL_ALGO:-randomx}"

echo "Pool dashboard: http://127.0.0.1:${EGA_POOL_WEB_PORT}/"
echo "Stratum:        stratum+tcp://0.0.0.0:${EGA_POOL_STRATUM_PORT}"
echo "Username = your EGA address"
exec python3 "$ROOT/scripts/ega-pool.py"
