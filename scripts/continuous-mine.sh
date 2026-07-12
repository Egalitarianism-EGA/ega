#!/usr/bin/env bash
# Solo continuous mining on the local node (CPU path for all algos).
# Usage: continuous-mine.sh [algo|all] [pause_sec]
#   algo: randomx | yespower-ega | verthash | scrypt | all (default randomx)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="${EGA_CLI:-$ROOT/src/ega-cli}"
MODE="${1:-randomx}"
PAUSE="${2:-2}"
TRIES="${EGA_MINE_TRIES:-10000000}"
LOG="${EGA_MINE_LOG:-/tmp/ega-continuous-mine.log}"

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Node not running" | tee -a "$LOG"
  exit 1
fi

case "$MODE" in
  all) ALGOS=(randomx yespower-ega verthash scrypt) ;;
  randomx|yespower-ega|verthash|scrypt) ALGOS=("$MODE") ;;
  *) echo "algo: randomx|yespower-ega|verthash|scrypt|all"; exit 1 ;;
esac

ADDR="$("$CLI" getnewaddress)"
echo "$(date -u +%FT%TZ) continuous mine start mode=$MODE addr=$ADDR" | tee -a "$LOG"
i=0
while true; do
  ALGO="${ALGOS[$((i % ${#ALGOS[@]}))]}"
  i=$((i + 1))
  if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) node down, exit" | tee -a "$LOG"
    exit 1
  fi
  BEFORE="$("$CLI" getblockcount)"
  if out="$("$CLI" generatetoaddress 1 "$ADDR" "$TRIES" "$ALGO" 2>&1)"; then
    AFTER="$("$CLI" getblockcount)"
    echo "$(date -u +%FT%TZ) $ALGO height $BEFORE->$AFTER $out" | tee -a "$LOG"
  else
    echo "$(date -u +%FT%TZ) $ALGO FAIL $out" | tee -a "$LOG"
  fi
  sleep "$PAUSE"
done
