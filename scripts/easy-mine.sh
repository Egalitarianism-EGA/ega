#!/usr/bin/env bash
# Mine N blocks with one algo. Usage: easy-mine.sh [algo] [blocks]
# algo: randomx | yespower-ega | verthash | scrypt
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="${EGA_CLI:-$ROOT/src/ega-cli}"
ALGO="${1:-randomx}"
N="${2:-1}"
TRIES="${3:-10000000}"

case "$ALGO" in
  randomx|rx) ALGO=randomx ;;
  yespower-ega|yespower|yp|yespowerega) ALGO=yespower-ega ;;
  scrypt) ALGO=scrypt ;;
  verthash|vert|vtc)
    echo "NOTE: 'verthash' here uses the NODE (CPU path)."
    echo "For REAL GPU mining, use: https://github.com/Egalitarianism-EGA/ega-verthash-miner"
    echo "Continuing with node Verthash anyway..."
    ALGO=verthash
    ;;
  *)
    echo "Unknown algo: $ALGO"
    echo "Use: randomx | yespower-ega | verthash | scrypt"
    exit 1
    ;;
esac

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Node not running. bash scripts/easy-start.sh"
  exit 1
fi

ADDR="$("$CLI" getnewaddress)"
echo "Mining $N block(s) with $ALGO → $ADDR"
echo "(This can take seconds to minutes depending on algo/difficulty.)"
"$CLI" generatetoaddress "$N" "$ADDR" "$TRIES" "$ALGO"
echo "Done. Height: $("$CLI" getblockcount)"
echo "Rewards may be immature until coinbase maturity; that's normal."
