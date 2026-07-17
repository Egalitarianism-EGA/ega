# Android / tablet light node (no VPS)

**Yes — this is part of the product.** Weak devices should help the network.

EGA’s chain is still small, so a **pruned full node on Termux** is practical: it still validates blocks and can open P2P peers. That is a real node, not a fake.

## What you get

| Mode | On Android Termux |
|------|-------------------|
| Pruned full node | Validates + relays (recommended) |
| Wallet | `ega-cli` or web wallet → your phone’s node |
| Mine | Solo YespowerEGA / RandomX (CPU); pool when available |
| Disk | `prune=1024` (~1 GB block storage target) |

## Requirements

- Android 8+ (aarch64), **Termux** from F-Droid (not Play Store dead builds)
- ~2–4 GB free storage to start (more as chain grows; prune keeps blocks capped)
- Charger recommended if mining
- Optional: same Wi‑Fi as home seed, or open port 20201 on mobile hotspot (harder)

## 1. Install Termux + tools

In Termux:

```bash
pkg update && pkg upgrade -y
pkg install -y git clang make autoconf automake libtool pkg-config \
  boost-dev libevent-dev openssl-dev sqlite-dev python cmake wget
```

## 2. Build EGA (on the phone)

```bash
cd ~
git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
./autogen.sh
./configure --without-gui --disable-tests --disable-bench --disable-wallet=no \
  CXXFLAGS="-O2" CFLAGS="-O2"
# If wallet BDB fails:
# ./configure --without-gui --disable-wallet --disable-tests --disable-bench
make -j$(nproc)
```

When we publish **linux-aarch64** releases, you can skip compile and use the tarball instead.

## 3. Light / pruned config

```bash
mkdir -p ~/.ega
cat > ~/.ega/ega.conf << 'EOF'
# EGA light full node — Android / weak device
server=1
listen=1
txindex=0
prune=1024
dbcache=100
maxconnections=8
listenonion=0

rpcuser=ega
rpcpassword=CHANGE_ME_PHONE_SECRET
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcport=20202
port=20201

# Community seed (operator home — update if IP changes)
addnode=105.225.132.175:20201

algo=yespower-ega
EOF
chmod 600 ~/.ega/ega.conf
```

**Notes**

- `prune=1024` = auto-prune toward ~1 GiB of block files (incompatible with `txindex=1`).
- `dbcache=100` keeps RAM lower.
- RPC only on localhost — use Termux web wallet or SSH tunnel for remote UI.

## 4. Run

```bash
cd ~/ega
./src/egad -daemon
./src/ega-cli getblockchaininfo
./src/ega-cli getconnectioncount
./src/ega-cli getnewaddress
```

Keep Termux awake: Android settings → battery → unrestricted for Termux.  
Optional: `termux-wake-lock`.

## 5. Solo mine on the phone (Yespower first)

```bash
./src/ega-cli generatetoaddress 1 $(./src/ega-cli getnewaddress) 500000 yespower-ega
# or randomx if you can spare heat/battery
```

Shared pool on phone: when RandomX/Yespower stratum is live, point a mobile miner at those ports; until then solo is valid mining.

## 6. Web wallet on the same phone

1. On the phone, open Termux and serve the wallet (or use desktop `scripts/start-web-wallet.sh` against this node via USB/`adb reverse`).
2. Prefer **http://127.0.0.1:8090** with the node’s RPC on the same device (see `scripts/start-web-wallet.sh` proxy).

## 7. Second “free seed” strategy (your idea)

Until VPS money:

1. Home PC = primary seed (port 20201 forwarded).  
2. Android on Wi‑Fi = second node with `addnode=105.225.132.175:20201` **and** home has `addnode=<phone LAN IP>:20201` if reachable.  
3. Result: `getconnectioncount` ≥ 1 with **$0**.

If the phone is only on mobile data, inbound peers are hard (CGNAT). Outbound `addnode` to home still helps **you** sync and mine; inbound seed role needs a reachable address (home PC is better for that).

## 8. What this is *not*

- Not a 100 GB archival explorer node.  
- Not as strong as a rack full of seeds — but **real validation + real peer** when online.  
- Mission: many small nodes beat zero poor users.

## Related

- `docs/ega/ACCESSIBILITY-ROADMAP.md`  
- `docs/ega/FREE-HOME-SEED.md`  
- `share/examples/ega-light.conf`  
- `scripts/setup-android-node.sh`  
