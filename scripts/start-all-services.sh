#!/usr/bin/env bash
# Start operator stack: node (if needed), explorer, web wallet, pool UI, Miningcore, EGA stratum.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Public host for pool UI / links / stratum display. Override anytime:
#   EGA_PUBLIC_HOST=x.x.x.x bash scripts/start-all-services.sh
# Or put the IP in ~/.ega/public-host (one line).
if [[ -z "${EGA_PUBLIC_HOST:-}" ]]; then
  if [[ -f "$HOME/.ega/public-host" ]]; then
    EGA_PUBLIC_HOST="$(tr -d '[:space:]' <"$HOME/.ega/public-host")"
  else
    # Auto-detect public IP when possible, else last known seed.
    EGA_PUBLIC_HOST="$(curl -4 -sS --max-time 4 ifconfig.me 2>/dev/null || true)"
    if [[ -z "$EGA_PUBLIC_HOST" ]]; then
      EGA_PUBLIC_HOST="105.225.132.175"
    fi
  fi
fi
export EGA_PUBLIC_HOST
export EGA_EXPLORER_URL="${EGA_EXPLORER_URL:-http://${EGA_PUBLIC_HOST}:8088}"
export EGA_WALLET_URL="${EGA_WALLET_URL:-http://${EGA_PUBLIC_HOST}:8090}"
echo "EGA_PUBLIC_HOST=$EGA_PUBLIC_HOST"

start_bg() {
  local name="$1" pidfile="$2" cmd="$3"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "already: $name (pid $(cat "$pidfile"))"
    return
  fi
  # shellcheck disable=SC2086
  nohup bash -c "$cmd" >>"/tmp/ega-${name}.log" 2>&1 &
  echo $! >"$pidfile"
  echo "started: $name (pid $!)"
}

if ! src/ega-cli getblockchaininfo >/dev/null 2>&1; then
  echo "Starting egad..."
  src/egad -daemon
  sleep 4
fi

start_bg explorer /tmp/ega-explorer.pid "python3 scripts/ega-explorer.py"
start_bg webwallet /tmp/ega-web-wallet.pid "python3 scripts/ega-web-wallet-server.py"
start_bg poolui /tmp/ega-pool-ui.pid "export EGA_PUBLIC_HOST='$EGA_PUBLIC_HOST' EGA_EXPLORER_URL='$EGA_EXPLORER_URL' EGA_WALLET_URL='$EGA_WALLET_URL'; python3 scripts/ega-pool-dashboard.py"
start_bg stratum /tmp/ega-algo-stratum.pid "python3 scripts/ega-algo-stratum.py"

if [[ -f "$HOME/.ega/miningcore/Miningcore.dll" ]]; then
  if ! curl -sS --max-time 2 http://127.0.0.1:4000/api/pools >/dev/null 2>&1; then
    (
      cd "$HOME/.ega/miningcore"
      export PATH="${HOME}/.dotnet:${PATH}"
      export DOTNET_ROOT="${HOME}/.dotnet"
      export LD_LIBRARY_PATH="${HOME}/.ega/miningcore:${LD_LIBRARY_PATH:-}"
      nohup dotnet Miningcore.dll -c config.json >>/tmp/ega-miningcore.log 2>&1 &
      echo $! >/tmp/miningcore.pid
      echo "started: miningcore"
    )
  else
    echo "already: miningcore"
  fi
else
  echo "skip miningcore (not installed at ~/.ega/miningcore)"
fi

echo
echo "Node RPC     : 127.0.0.1:20202"
echo "Explorer     : http://127.0.0.1:8088/"
echo "Pool UI      : http://127.0.0.1:8089/"
echo "Web wallet   : http://127.0.0.1:8090/"
echo "Stratum RX   : :3333  YP :3335  VH :3334  SC :3336"
echo "Stratum stats: http://127.0.0.1:3337/api/"
src/ega-cli getblockcount 2>/dev/null || true
