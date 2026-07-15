#!/usr/bin/env bash
# Start operator stack: node (if needed), explorer, web wallet, pool UI, Miningcore, EGA stratum.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

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
start_bg poolui /tmp/ega-pool-ui.pid "python3 scripts/ega-pool-dashboard.py"
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
