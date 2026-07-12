#!/usr/bin/env bash
# Verify wallet + one block per algo on regtest.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${EGA_BIN_DIR:-$ROOT/src}"
DATADIR="$(mktemp -d)"
cleanup() {
  "$BIN/ega-cli" -regtest -datadir="$DATADIR" stop >/dev/null 2>&1 || true
  rm -rf "$DATADIR"
}
trap cleanup EXIT

"$BIN/egad" -regtest -datadir="$DATADIR" -daemon
sleep 2
ADDR="$("$BIN/ega-cli" -regtest -datadir="$DATADIR" getnewaddress)"
echo "payout: $ADDR"

for ALGO in randomx verthash yespower-ega; do
  echo "mining $ALGO..."
  "$BIN/ega-cli" -regtest -datadir="$DATADIR" generatetoaddress 1 "$ADDR" 10000000 "$ALGO"
done

H="$("$BIN/ega-cli" -regtest -datadir="$DATADIR" getblockcount)"
test "$H" = "3"
echo "OK: height=$H, mined all three algos"
for h in 1 2 3; do
  hash="$("$BIN/ega-cli" -regtest -datadir="$DATADIR" getblockhash "$h")"
  "$BIN/ega-cli" -regtest -datadir="$DATADIR" getblock "$hash" | grep pow_algo
done
