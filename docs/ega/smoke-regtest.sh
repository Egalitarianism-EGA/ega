#!/usr/bin/env bash
# EGA Phase 6 smoke: regtest start, genesis, three algos listed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${EGA_BIN_DIR:-$ROOT/src}"
DATADIR="$(mktemp -d)"
cleanup() {
  "$BIN/ega-cli" -regtest -datadir="$DATADIR" stop >/dev/null 2>&1 || true
  rm -rf "$DATADIR"
}
trap cleanup EXIT

echo "== EGA regtest smoke =="
"$BIN/egad" -regtest -datadir="$DATADIR" -daemon
sleep 2

GENESIS="$("$BIN/ega-cli" -regtest -datadir="$DATADIR" getblockhash 0)"
echo "genesis: $GENESIS"
test "$GENESIS" = "7db0bcedfac1596d0be2a5b42c4b88043c207f8f29bac2796fba10ea06ae5ac0"

INFO="$("$BIN/ega-cli" -regtest -datadir="$DATADIR" getblockchaininfo)"
echo "$INFO" | grep -q randomx
echo "$INFO" | grep -q verthash
echo "$INFO" | grep -q yespower-ega

echo "OK: genesis + triple-algo difficulties present"
