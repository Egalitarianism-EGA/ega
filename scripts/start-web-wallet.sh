#!/usr/bin/env bash
# Serve EGA web wallet + same-origin RPC proxy (so phones/browsers can use it).
# Default: http://0.0.0.0:8090/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EGA_WEB_WALLET_HOST="${EGA_WEB_WALLET_HOST:-0.0.0.0}"
export EGA_WEB_WALLET_PORT="${EGA_WEB_WALLET_PORT:-8090}"
export EGA_RPC_URL="${EGA_RPC_URL:-http://127.0.0.1:20202}"
# Load rpcuser/pass from conf if present
if [[ -f "$HOME/.ega/ega.conf" ]]; then
  export EGA_RPC_USER="${EGA_RPC_USER:-$(grep -E '^rpcuser=' "$HOME/.ega/ega.conf" | cut -d= -f2-)}"
  export EGA_RPC_PASS="${EGA_RPC_PASS:-$(grep -E '^rpcpassword=' "$HOME/.ega/ega.conf" | cut -d= -f2-)}"
fi
echo "Web wallet → http://127.0.0.1:${EGA_WEB_WALLET_PORT}/"
echo "On phone (same Wi-Fi): http://$(hostname -I | awk '{print $1}'):${EGA_WEB_WALLET_PORT}/"
exec python3 "$ROOT/scripts/ega-web-wallet-server.py"
