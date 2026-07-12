#!/usr/bin/env bash
# Run local explorer and (optionally) a Cloudflare quick tunnel for a public URL.
# Requires: node running, scripts/ega-explorer.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${EGA_EXPLORER_HOST:-127.0.0.1}"
PORT="${EGA_EXPLORER_PORT:-8088}"

if ! "$ROOT/src/ega-cli" getblockchaininfo >/dev/null 2>&1; then
  echo "Node not running — start with: bash scripts/easy-start.sh"
  exit 1
fi

# Start explorer if not already on PORT
if ! ss -lptn "sport = :${PORT}" 2>/dev/null | grep -q LISTEN; then
  echo "Starting explorer on http://${HOST}:${PORT}/"
  EGA_EXPLORER_HOST="$HOST" EGA_EXPLORER_PORT="$PORT" \
    nohup python3 "$ROOT/scripts/ega-explorer.py" >/tmp/ega-explorer.log 2>&1 &
  sleep 1
else
  echo "Explorer already listening on :${PORT}"
fi

CF="${CLOUDFLARED_BIN:-}"
if [[ -z "$CF" ]]; then
  for c in cloudflared /tmp/cloudflared "$HOME/bin/cloudflared"; do
    if [[ -x "$c" ]]; then CF="$c"; break; fi
  done
fi

if [[ -z "${CF}" ]]; then
  echo
  echo "Explorer is local only: http://${HOST}:${PORT}/"
  echo "For a public URL, install cloudflared then re-run:"
  echo "  https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
  echo "  export CLOUDFLARED_BIN=/path/to/cloudflared"
  echo "  bash scripts/start-public-explorer.sh"
  exit 0
fi

echo "Opening Cloudflare quick tunnel → http://127.0.0.1:${PORT}"
echo "(URL prints below; paste it into the website explorer page when stable)"
exec "$CF" tunnel --url "http://127.0.0.1:${PORT}"
