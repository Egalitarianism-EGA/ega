#!/usr/bin/env bash
# Very low-usage MultiShield keep-alive: one block, then long sleep.
# Rotates algos so all four stay exercised without cooking the PC.
#
# Usage:
#   bash scripts/low-power-mine.sh              # all 4, 10 min between blocks
#   bash scripts/low-power-mine.sh all 600      # pause seconds
#   bash scripts/low-power-mine.sh randomx 300  # single algo
#   EGA_MINE_TRIES=500000 bash scripts/low-power-mine.sh all 900
#
# Stop: kill $(cat /tmp/ega-low-power-mine.pid)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="${EGA_CLI:-$ROOT/src/ega-cli}"
MODE="${1:-all}"
PAUSE="${2:-600}"          # default 10 minutes between blocks
TRIES="${EGA_MINE_TRIES:-500000}"  # soft cap; at min-diff usually finds much sooner
LOG="${EGA_MINE_LOG:-/tmp/ega-low-power-mine.log}"
PIDFILE="${EGA_MINE_PID:-/tmp/ega-low-power-mine.pid}"

if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
  echo "Node not running — bash scripts/easy-start.sh"
  exit 1
fi

case "$MODE" in
  all) ALGOS=(randomx yespower-ega scrypt verthash) ;;
  randomx|yespower-ega|verthash|scrypt) ALGOS=("$MODE") ;;
  *) echo "usage: $0 [all|randomx|yespower-ega|verthash|scrypt] [pause_sec]"; exit 1 ;;
esac

echo $$ > "$PIDFILE"
ADDR="$("$CLI" getnewaddress)"
echo "$(date -u +%FT%TZ) low-power mine mode=$MODE pause=${PAUSE}s addr=$ADDR algos=${ALGOS[*]}" | tee -a "$LOG"

i=0
while true; do
  ALGO="${ALGOS[$((i % ${#ALGOS[@]}))]}"
  i=$((i + 1))
  if ! "$CLI" getblockchaininfo >/dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) node down" | tee -a "$LOG"
    exit 1
  fi
  # single-flight: this script only runs one generate at a time
  BEFORE="$("$CLI" getblockcount)"
  echo "$(date -u +%FT%TZ) mining 1× $ALGO (height $BEFORE)..." | tee -a "$LOG"
  if out=$(timeout 300 "$CLI" generatetoaddress 1 "$ADDR" "$TRIES" "$ALGO" 2>&1); then
    AFTER="$("$CLI" getblockcount)"
    echo "$(date -u +%FT%TZ) OK $ALGO $BEFORE->$AFTER" | tee -a "$LOG"
  else
    echo "$(date -u +%FT%TZ) $ALGO fail/timeout: $out" | tee -a "$LOG"
  fi
  echo "$(date -u +%FT%TZ) sleep ${PAUSE}s" | tee -a "$LOG"
  sleep "$PAUSE"
done
