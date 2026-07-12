#!/usr/bin/env bash
# 24/7 GPU Verthash → local Miningcore :3334
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAY="${EGA_MINE_ADDRESS:-}"
if [[ -z "$PAY" && -f "$HOME/.ega/miningcore/config.json" ]]; then
  PAY=$(python3 -c "import json;print(json.load(open('$HOME/.ega/miningcore/config.json'))['pools'][0]['address'])")
fi
[[ -n "$PAY" ]] || { echo "Set EGA_MINE_ADDRESS"; exit 1; }
DAT="${EGA_VERTHASH_DAT:-/tmp/ega-verthash.dat}"
[[ -f "$DAT" ]] || DAT="$HOME/.ega/miningcore/verthash.dat"
BIN="${VERTHASH_MINER:-/tmp/VerthashMiner/build/VerthashMiner}"
[[ -x "$BIN" ]] || { echo "VerthashMiner not found at $BIN"; exit 1; }
cd "$(dirname "$BIN")"
exec ./VerthashMiner -a verthash \
  -o stratum+tcp://127.0.0.1:3334 \
  -u "$PAY" -p x \
  --all-cl-devices \
  -f "$DAT" \
  --no-verthash-data_verification
