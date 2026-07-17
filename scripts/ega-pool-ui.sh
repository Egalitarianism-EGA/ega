#!/usr/bin/env bash
# Human pool dashboard (not raw JSON API)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EGA_POOL_UI_HOST="${EGA_POOL_UI_HOST:-0.0.0.0}"
export EGA_POOL_UI_PORT="${EGA_POOL_UI_PORT:-8089}"
export EGA_POOL_API="${EGA_POOL_API:-http://127.0.0.1:4000/api/pools}"
export EGA_PUBLIC_HOST="${EGA_PUBLIC_HOST:-105.225.132.175}"
echo "Pool UI → http://127.0.0.1:${EGA_POOL_UI_PORT}/"
exec python3 "$ROOT/scripts/ega-pool-dashboard.py"
