# Building EGA Core on Linux (primary target)

## Dependencies (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y build-essential libtool autotools-dev automake pkg-config \
  bsdmainutils python3 cmake \
  libssl-dev libevent-dev libboost-system-dev libboost-filesystem-dev \
  libboost-test-dev libboost-thread-dev \
  libminiupnpc-dev libzmq3-dev
# Optional wallet:
# sudo apt install -y libdb-dev libdb++-dev   # or Berkeley DB 4.8 via contrib/install_db4.sh
```

## Build

```bash
./autogen.sh
./configure --with-daemon --without-gui --enable-wallet --with-incompatible-bdb
# GUI optional:
# ./configure --with-daemon --with-gui=qt5 --enable-wallet --with-incompatible-bdb
make -j$(nproc)
```

Binaries: **`src/egad`**, **`src/ega-cli`**, **`src/ega-tx`** (GUI: **`src/qt/ega-qt`**)

**cmake is required** (RandomX static library under `src/crypto/randomx/build/`).

## Tests

```bash
make -C src check
# or focused:
./src/test/test_digibyte -t main_tests -t ega_pow_tests -t amount_tests
./docs/ega/smoke-regtest.sh
./docs/ega/mine-all-algos-regtest.sh
```

## Run

```bash
./src/egad -daemon
./src/ega-cli getblockchaininfo
# data: ~/.ega  config: ~/.ega/ega.conf
```

## Cross-compile for Windows

See [build-windows.md](build-windows.md) (depends + mingw).
