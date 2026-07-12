#!/usr/bin/env bash
# EGA smoke: regtest start, genesis, MultiShield-4 algos listed.
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
test "$GENESIS" = "beeed73f369163a394f73c5d69c368cc3d01b07ad0f0af42b9cb8ec429cf3a71"

INFO="$("$BIN/ega-cli" -regtest -datadir="$DATADIR" getblockchaininfo)"
echo "$INFO" | grep -q randomx
echo "$INFO" | grep -q verthash
echo "$INFO" | grep -q yespower-ega
echo "$INFO" | grep -q scrypt

echo "OK: genesis + MultiShield-4 difficulties present"
