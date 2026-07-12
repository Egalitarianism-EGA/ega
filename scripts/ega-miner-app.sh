#!/usr/bin/env bash
# Simple interactive miner launcher (CPU algos; GPU points to docs)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/src/ega-cli"
EGAD="$ROOT/src/egad"

if [[ ! -x "$EGAD" ]]; then
  echo "Build the node first: bash scripts/easy-install-linux.sh"
  read -r -p "Press Enter..."
  exit 1
fi

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Starting node..."
  bash "$ROOT/scripts/easy-start.sh"
fi

echo ""
echo "Egalitarianism Miner"
echo "--------------------"
echo "1) RandomX     (CPU — modern processors)"
echo "2) YespowerEGA (CPU — weaker machines / phones / Pi)"
echo "3) Scrypt      (harder door — MultiShield security anchor)"
echo "4) Verthash    (GPU — opens instructions)"
echo "5) Quit"
echo ""
read -r -p "Choose [1-5]: " c
case "$c" in
  1) bash "$ROOT/scripts/easy-mine.sh" randomx 1 ;;
  2) bash "$ROOT/scripts/easy-mine.sh" yespower-ega 1 ;;
  3) bash "$ROOT/scripts/easy-mine.sh" scrypt 1 ;;
  4)
    echo ""
    echo "GPU Verthash uses a separate miner against your node."
    echo "Guide: https://github.com/Egalitarianism-EGA/ega-verthash-miner"
    if command -v xdg-open >/dev/null; then
      xdg-open "https://github.com/Egalitarianism-EGA/ega-verthash-miner" 2>/dev/null || true
    fi
    ;;
  *) echo "Bye." ;;
esac
echo ""
read -r -p "Press Enter to close..."
