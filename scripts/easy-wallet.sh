#!/usr/bin/env bash
# Get a receive address + backup reminder
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="${EGA_CLI:-$ROOT/src/ega-cli}"

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Node not running. Start it:"
  echo "  bash scripts/easy-start.sh"
  exit 1
fi

ADDR="$("$CLI" getnewaddress)"
echo "=========================================="
echo "  YOUR EGA RECEIVE ADDRESS"
echo "=========================================="
echo ""
echo "  $ADDR"
echo ""
echo "Save this. Mine rewards can go here."
echo ""
echo "BACKUP (important):"
echo "  $CLI backupwallet $HOME/ega-wallet-backup.dat"
echo "Keep that file offline and private."
echo "=========================================="
echo "$ADDR"
