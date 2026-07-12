#!/usr/bin/env bash
# Desktop "Node" app — starts egad and shows status
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$ROOT/src:$PATH"
EGAD="$ROOT/src/egad"
CLI="$ROOT/src/ega-cli"

if [[ ! -x "$EGAD" ]]; then
  echo "egad not found. Build first: bash scripts/easy-install-linux.sh"
  read -r -p "Press Enter to close..."
  exit 1
fi

bash "$ROOT/scripts/easy-start.sh"
echo ""
echo "Node is running in the background."
echo "Wallet GUI: $ROOT/src/qt/ega-qt"
echo "Mine: bash $ROOT/scripts/easy-mine.sh randomx"
echo ""
read -r -p "Press Enter to close this window..."
