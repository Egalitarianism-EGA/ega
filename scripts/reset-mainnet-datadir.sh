#!/usr/bin/env bash
# Wipe local mainnet data for a clean test / re-launch.
# ONLY for early testing when you control the chain and accept losing local blocks/wallet.
set -euo pipefail
DATADIR="${1:-$HOME/.ega}"

echo "This deletes local chain + wallet in: $DATADIR"
echo "Peers elsewhere are unaffected unless they also reset."
read -r -p "Type RESET to continue: " ans
[[ "$ans" == "RESET" ]] || { echo "Aborted."; exit 1; }

# stop node
if [[ -f "$DATADIR/egad.pid" ]]; then
  kill "$(cat "$DATADIR/egad.pid")" 2>/dev/null || true
  sleep 2
fi

# keep conf
CONF=""
[[ -f "$DATADIR/ega.conf" ]] && CONF=$(cat "$DATADIR/ega.conf")

rm -rf "$DATADIR"
mkdir -p "$DATADIR"
if [[ -n "$CONF" ]]; then
  printf '%s\n' "$CONF" > "$DATADIR/ega.conf"
  # ensure useful defaults
  grep -q 'txindex=' "$DATADIR/ega.conf" || echo 'txindex=1' >> "$DATADIR/ega.conf"
else
  cat > "$DATADIR/ega.conf" << EOF
server=1
listen=1
txindex=1
rpcuser=ega
rpcpassword=ega$(head -c 8 /dev/urandom | xxd -p)
rpcallowip=127.0.0.1
rpcbind=127.0.0.1
algo=randomx
EOF
fi

echo "Clean datadir ready: $DATADIR"
echo "Start: bash scripts/easy-start.sh"
