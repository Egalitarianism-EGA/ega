#!/usr/bin/env bash
# Start Miningcore multi-algo pool (Verthash :3334, Scrypt :3336)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MC="${EGA_MININGCORE_DIR:-$HOME/.ega/miningcore}"
export PATH="${HOME}/.dotnet:${PATH}"
export DOTNET_ROOT="${HOME}/.dotnet"
export LD_LIBRARY_PATH="${MC}:${LD_LIBRARY_PATH:-}"

if [[ ! -f "$MC/Miningcore.dll" ]]; then
  echo "Miningcore not at $MC — copy from build or see ega-miningcore repo"
  exit 1
fi
if [[ ! -f "$MC/config.json" ]]; then
  echo "Missing $MC/config.json"
  exit 1
fi
if ! "$ROOT/src/ega-cli" getblockchaininfo >/dev/null 2>&1; then
  echo "Start node first: bash scripts/easy-start.sh"
  exit 1
fi
cd "$MC"
echo "API:              http://0.0.0.0:4000/api/pools"
echo "Stratum Verthash: stratum+tcp://0.0.0.0:3334"
echo "Stratum Scrypt:   stratum+tcp://0.0.0.0:3336"
echo "Username = EGA address (E…), password = x"
echo "Note: RandomX / YespowerEGA use solo node mining (share-verify not in stock Miningcore)."
exec dotnet Miningcore.dll -c config.json
