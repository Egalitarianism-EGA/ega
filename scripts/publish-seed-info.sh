#!/usr/bin/env bash
# Print what to publish as a seed node (no secrets).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/src/ega-cli"

echo "=== EGA seed info ==="
if "$CLI" getblockchaininfo >/dev/null 2>&1; then
  "$CLI" getblockchaininfo | python3 -c "import sys,json;d=json.load(sys.stdin);print('chain',d.get('chain'),'height',d.get('blocks'),'best',d.get('bestblockhash','')[:16]+'…')"
  "$CLI" getnetworkinfo | python3 -c "import sys,json;d=json.load(sys.stdin);print('connections',d.get('connections'),'subver',d.get('subversion'))"
else
  echo "egad not running"
fi

PUB=""
PUB=$(curl -4 -sS --max-time 4 ifconfig.me 2>/dev/null || curl -4 -sS --max-time 4 icanhazip.com 2>/dev/null || true)
echo
echo "P2P port: 20201 (must be open on firewall/router)"
echo "RPC port: 20202 (keep localhost only)"
if [[ -n "$PUB" ]]; then
  echo "Detected public IPv4: $PUB"
  echo
  echo "Peers should use:"
  echo "  addnode=${PUB}:20201"
else
  echo "Could not detect public IP — fill in manually."
fi
echo
echo "Checklist:"
echo "  [ ] listen=1 in ega.conf"
echo "  [ ] TCP 20201 reachable from outside"
echo "  [ ] MultiShield-4 binary (v0.2.0+)"
echo "  [ ] Update docs/ega/SEEDS.md + website when stable 24/7"
