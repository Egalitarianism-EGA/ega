# EGA — Run a node and mine (launch guide)

For operators who want to **run a full node** and **mine** with RandomX, Verthash, YespowerEGA, or Scrypt.

## 1. Build (Linux)

```bash
sudo apt install -y build-essential libtool autotools-dev automake pkg-config \
  bsdmainutils python3 cmake libssl-dev libevent-dev \
  libboost-system-dev libboost-filesystem-dev libboost-thread-dev \
  libboost-test-dev libminiupnpc-dev libzmq3-dev \
  libdb-dev libdb++-dev

./autogen.sh
./configure --with-daemon --without-gui --enable-wallet --with-incompatible-bdb
make -j$(nproc)
```

Binaries: `src/egad`, `src/ega-cli`  
Friendly names: `contrib/ega/egad`, `ega-cli` (see `contrib/ega/README.md`)

Windows: see [build-windows.md](build-windows.md). macOS: later.

## 2. Configure

```bash
mkdir -p ~/.ega
cp share/examples/ega.conf ~/.ega/ega.conf
# edit rpcuser / rpcpassword
```

Important settings:

```ini
server=1
rpcuser=YOUR_USER
rpcpassword=YOUR_LONG_PASSWORD
# mainnet defaults: P2P 20201, RPC 20202

# default mining algo for templates
algo=randomx

# after you have peers, optionally:
# addnode=IP:20201
```

## 3. Start the node

```bash
./src/egad -daemon
# or: export EGA_BIN_DIR=$PWD/src; contrib/ega/egad -daemon

./src/ega-cli getblockchaininfo
```

Data dir: `~/.ega` · PID: `egad.pid` · Config: `ega.conf`

## 4. Wallet + address

```bash
./src/ega-cli getnewaddress
# → save this address for mining payouts
```

(Older multiwallet: `createwallet "main"` then getnewaddress.)

## 5. Mine (solo, built-in)

Mine **one** block to your address with a chosen algo:

```bash
ADDR=$(./src/ega-cli getnewaddress)

# CPU (modern) — RandomX
./src/ega-cli generatetoaddress 1 "$ADDR" 10000000 randomx

# GPU path — Verthash (first block builds ~256 MiB dataset; can take a minute)
./src/ega-cli generatetoaddress 1 "$ADDR" 10000000 verthash

# Old phones / low-RAM Pi — YespowerEGA
./src/ega-cli generatetoaddress 1 "$ADDR" 10000000 yespower-ega

# Scrypt — MultiShield hard door
./src/ega-cli generatetoaddress 1 "$ADDR" 10000000 scrypt
```

Check:

```bash
./src/ega-cli getblockcount
./src/ega-cli getblock $(./src/ega-cli getblockhash 1) | grep pow_algo
```

**Coinbase maturity:** rewards appear after maturity blocks (same family as Bitcoin/DigiByte). Balance may show `0` until then; use `getbalances` / list transactions.

### Continuous solo mining (simple loop)

```bash
ADDR=YOUR_ADDRESS
ALGO=randomx   # or verthash / yespower-ega
while true; do
  ./src/ega-cli generatetoaddress 1 "$ADDR" 10000000 "$ALGO" || sleep 1
done
```

## 6. External miners (getblocktemplate)

```bash
# Template for a specific algo (2nd argument)
./src/ega-cli getblocktemplate '{"rules":["segwit"]}' randomx
./src/ega-cli getblocktemplate '{"rules":["segwit"]}' verthash
./src/ega-cli getblocktemplate '{"rules":["segwit"]}' yespower-ega

# Submit a solved block
./src/ega-cli submitblock "hexdata"
```

Fair launch defaults:

- **No peers required** for GBT (`-gbtrequirepeers=0`)
- **IBD does not block** GBT (`-gbtrequiresynced=0`)

When the network is busy with peers, you can set `gbtrequirepeers=1` in `ega.conf`.

## 7. Algo names (canonical)

| Algo | CLI strings |
|------|-------------|
| RandomX | `randomx`, `rx` |
| Verthash | `verthash`, `vert`, `vtc` |
| YespowerEGA | `yespower-ega`, `yespower`, `yp`, `yespowerega` |
| Scrypt | `scrypt` |

Default: `-algo=randomx`

## 8. Connect to others

At launch there may be **no DNS seeds**. Share node IPs:

```ini
addnode=1.2.3.4:20201
```

Firewall: open **TCP 20201** (main P2P).

## 9. Freeze list (do not change casually)

See [params.md](params.md) — genesis hash, ports, money, PoW params. Changing genesis = a different coin.

## 10. What is *not* in this MVP

- Public stratum pool
- GUI installer
- Mobile miner app
- Explorer
- macOS packages  

Those are roadmap items after nodes are mining.
