#!/usr/bin/env bash
# Start Miningcore (EGA Verthash stratum) against local egad
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MC="${EGA_MININGCORE_DIR:-$HOME/.ega/miningcore}"
export PATH="${HOME}/.dotnet:${PATH}"
export DOTNET_ROOT="${HOME}/.dotnet"
export LD_LIBRARY_PATH="${MC}:${LD_LIBRARY_PATH:-}"

if [[ ! -f "$MC/Miningcore.dll" ]]; then
  echo "Miningcore not installed at $MC"
  echo "Build from https://github.com/oliverw/miningcore (see ega-miningcore repo)"
  exit 1
fi
if [[ ! -f "$MC/config.json" ]]; then
  echo "Missing $MC/config.json — copy from ega-miningcore"
  exit 1
fi
if ! "$ROOT/src/ega-cli" getblockchaininfo >/dev/null 2>&1; then
  echo "Start node first: bash scripts/easy-start.sh"
  exit 1
fi

cd "$MC"
echo "Miningcore API:     http://127.0.0.1:4000/api/pools"
echo "Stratum Verthash:   stratum+tcp://0.0.0.0:3334"
echo "Username = EGA address (legacy E…), password = x"
exec dotnet Miningcore.dll -c config.json
