#!/usr/bin/env bash
# Scaffold: Postgres + optional Miningcore for EGA pool (Docker).
# RandomX-first. Full multi-algo needs Miningcore builds with matching algos.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${EGA_POOL_DIR:-$HOME/.ega/pool-stack}"
mkdir -p "$DIR"

RPC_USER=$(grep -E '^rpcuser=' "$HOME/.ega/ega.conf" 2>/dev/null | head -1 | cut -d= -f2- || echo ega)
RPC_PASS=$(grep -E '^rpcpassword=' "$HOME/.ega/ega.conf" 2>/dev/null | head -1 | cut -d= -f2- || echo CHANGE_ME)

if ! command -v docker >/dev/null; then
  echo "Docker is required for the pool stack."
  exit 1
fi

if ! "$ROOT/src/ega-cli" getblockchaininfo >/dev/null 2>&1; then
  echo "Start egad first: bash scripts/easy-start.sh"
  exit 1
fi

# Payout address
if [[ -z "${EGA_POOL_ADDRESS:-}" ]]; then
  EGA_POOL_ADDRESS=$("$ROOT/src/ega-cli" getnewaddress 2>/dev/null || true)
fi
if [[ -z "${EGA_POOL_ADDRESS:-}" ]]; then
  echo "Set EGA_POOL_ADDRESS to a wallet address for pool coinbase payouts."
  exit 1
fi

cat > "$DIR/docker-compose.yml" << EOF
# Egalitarianism pool stack (operator scaffold)
# Postgres is ready for Miningcore. Miningcore image must support your algos.
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: miningcore
      POSTGRES_PASSWORD: miningcore
      POSTGRES_DB: miningcore
    ports:
      - "5432:5432"
    volumes:
      - ega_mc_pg:/var/lib/postgresql/data

  # Uncomment when you have a Miningcore image built with EGA coin support:
  # miningcore:
  #   image: YOUR_MININGCORE_IMAGE
  #   depends_on: [postgres]
  #   network_mode: host
  #   volumes:
  #     - ./config.json:/app/config.json:ro

volumes:
  ega_mc_pg:
EOF

# Example config for operators who build Miningcore themselves
cat > "$DIR/config.example.json" << EOF
{
  "logging": { "level": "info", "enableConsoleLog": true },
  "persistence": {
    "postgres": {
      "host": "127.0.0.1",
      "port": 5432,
      "user": "miningcore",
      "password": "miningcore",
      "database": "miningcore"
    }
  },
  "paymentProcessing": { "enabled": true, "interval": 600 },
  "api": { "enabled": true, "listenAddress": "0.0.0.0", "port": 4000 },
  "pools": [
    {
      "id": "ega-randomx",
      "enabled": true,
      "coin": "ega",
      "address": "${EGA_POOL_ADDRESS}",
      "rewardRecipients": [],
      "blockRefreshInterval": 1000,
      "jobRebroadcastTimeout": 10,
      "clientConnectionTimeout": 600,
      "ports": {
        "3333": {
          "listenAddress": "0.0.0.0",
          "difficulty": 0.1,
          "name": "RandomX",
          "varDiff": {
            "minDiff": 0.01,
            "maxDiff": 10000,
            "targetTime": 15,
            "retargetTime": 90,
            "variancePercent": 30
          }
        }
      },
      "daemon": {
        "host": "127.0.0.1",
        "port": 20202,
        "user": "${RPC_USER}",
        "password": "${RPC_PASS}"
      },
      "paymentProcessing": {
        "enabled": true,
        "minimumPayment": 1,
        "payoutScheme": "PPLNS",
        "payoutSchemeConfig": { "factor": 2 }
      }
    }
  ]
}
EOF

echo "Wrote $DIR/docker-compose.yml and config.example.json"
echo "Pool payout address: $EGA_POOL_ADDRESS"
echo ""
echo "Starting Postgres..."
(cd "$DIR" && docker compose up -d postgres)

echo ""
echo "Postgres is up for Miningcore."
echo "Next:"
echo "  1. Build/run Miningcore with EGA coin profile (see ega-miningcore repo)"
echo "  2. Point it at $DIR/config.example.json (edit coin name/algo as required)"
echo "  3. Stratum RandomX: port 3333 · API: 4000"
echo ""
echo "Until Miningcore is built for EGA, use multi-node solo mining:"
echo "  bash scripts/two-node-mining-demo.sh"
echo "  docs: docs/ega/network-mining.md"
