#!/usr/bin/env bash
# Egalitarianism (EGA) — one-shot Linux build for non-experts
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"

echo "=========================================="
echo "  Egalitarianism (EGA) — easy install"
echo "=========================================="
echo "This installs build tools (needs sudo) and compiles egad + ega-cli."
echo ""

if ! command -v sudo >/dev/null; then
  echo "ERROR: sudo required to install packages."
  exit 1
fi

echo "[1/4] Installing packages (Ubuntu/Debian)..."
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  build-essential libtool autotools-dev automake pkg-config bsdmainutils \
  python3 cmake git ca-certificates ccache \
  libssl-dev libevent-dev \
  libboost-system-dev libboost-filesystem-dev libboost-thread-dev \
  libboost-chrono-dev libboost-test-dev \
  libdb-dev libdb++-dev \
  libminiupnpc-dev libzmq3-dev \
  || { echo "If package install failed, see docs/ega/build-linux.md"; exit 1; }

echo "[2/4] Generating build system..."
if [[ ! -x ./configure ]]; then
  ./autogen.sh
fi

echo "[3/4] Configuring (wallet ON, GUI OFF — simple & reliable)..."
./configure \
  --with-daemon \
  --without-gui \
  --enable-wallet \
  --with-incompatible-bdb \
  --disable-bench \
  --disable-tests \
  CC="${CC:-ccache gcc}" CXX="${CXX:-ccache g++}"

echo "[4/4] Compiling (this can take a while)..."
make -C src egad ega-cli -j"$(nproc 2>/dev/null || echo 2)"

echo ""
echo "=========================================="
echo "  SUCCESS"
echo "=========================================="
echo "Programs:"
echo "  $ROOT/src/egad"
echo "  $ROOT/src/ega-cli"
echo ""
echo "Next:"
echo "  bash scripts/easy-start.sh"
echo "  bash scripts/easy-wallet.sh"
echo "  bash scripts/easy-mine.sh randomx"
echo "=========================================="
