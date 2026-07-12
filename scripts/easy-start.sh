#!/usr/bin/env bash
# Start Egalitarianism node (egad) the easy way
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EGAD="${EGA_BIN:-$ROOT/src/egad}"
CLI="${EGA_CLI:-$ROOT/src/ega-cli}"

if [[ ! -x "$EGAD" ]]; then
  echo "egad not found at $EGAD"
  echo "Run first: bash scripts/easy-install-linux.sh"
  exit 1
fi

mkdir -p "$HOME/.ega"
CONF="$HOME/.ega/ega.conf"
if [[ ! -f "$CONF" ]]; then
  PASS="ega$(head -c 12 /dev/urandom | xxd -p 2>/dev/null || date +%s)"
  cat > "$CONF" << EOF
# Egalitarianism (EGA) — auto-created by easy-start.sh
# Full name: Egalitarianism

server=1
listen=1
rpcuser=ega
rpcpassword=$PASS
rpcallowip=127.0.0.1
rpcbind=127.0.0.1

# Default mining algo for templates
algo=randomx

# Optional: connect to a friend's node
# addnode=THEIR_IP:20201
EOF
  echo "Created $CONF"
  echo "RPC password saved in that file (do not share it)."
fi

if "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Node already running."
else
  echo "Starting egad..."
  "$EGAD" -daemon
  sleep 3
fi

echo ""
echo "=== Node status ==="
"$CLI" getblockchaininfo 2>/dev/null | head -25 || echo "(still starting — wait 5s and try: $CLI getblockchaininfo)"
echo ""
echo "Next:"
echo "  bash scripts/easy-wallet.sh     # get an address"
echo "  bash scripts/easy-mine.sh randomx"
echo "  GUI (if built): $ROOT/src/qt/ega-qt"
