#!/usr/bin/env bash
# Start the lightweight EGA block explorer (http://127.0.0.1:8088)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/src/ega-cli"

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Node not running — starting..."
  bash "$ROOT/scripts/easy-start.sh"
  sleep 2
fi

# Remind about txindex for full tx lookup
if ! grep -qE '^[[:space:]]*txindex=1' "$HOME/.ega/ega.conf" 2>/dev/null; then
  echo "Tip: add txindex=1 to ~/.ega/ega.conf for full tx lookup (may need reindex)."
fi

export EGA_EXPLORER_HOST="${EGA_EXPLORER_HOST:-127.0.0.1}"
export EGA_EXPLORER_PORT="${EGA_EXPLORER_PORT:-8088}"
echo "Opening explorer on http://${EGA_EXPLORER_HOST}:${EGA_EXPLORER_PORT}/"
exec python3 "$ROOT/scripts/ega-explorer.py"
