#!/usr/bin/env bash
# Shared stratum for RandomX (:3333) + YespowerEGA (:3335)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EGA_POW_HASH="${EGA_POW_HASH:-$ROOT/src/ega-pow-hash}"
if [[ ! -x "$EGA_POW_HASH" ]]; then
  echo "Building ega-pow-hash..."
  make -C "$ROOT/src" ega-pow-hash -j"$(nproc)"
fi
if ! "$ROOT/src/ega-cli" getblockchaininfo >/dev/null 2>&1; then
  echo "Start node first: bash scripts/easy-start.sh"
  exit 1
fi
echo "RandomX    stratum+tcp://0.0.0.0:3333"
echo "YespowerEGA stratum+tcp://0.0.0.0:3335"
echo "Username = EGA address · password = x"
exec python3 "$ROOT/scripts/ega-algo-stratum.py"
