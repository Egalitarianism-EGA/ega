# Android: node + wallet — step by step

You can use a phone/tablet as a **real EGA node** (pruned) so you don’t need a VPS or a friend’s PC.

## What you’ll have

1. **Node** (`egad`) validating the chain and talking to the seed  
2. **Wallet** (CLI in Termux and/or web wallet in Chrome)  
3. Optional **solo mining** (YespowerEGA is best for phones)

---

## Part A — Install Termux

1. Install **Termux from F-Droid** (not the old Play Store app):  
   https://f-droid.org/packages/com.termux/  
2. Open Termux, allow storage if asked.  
3. Run:

```bash
pkg update && pkg upgrade -y
```

4. Install build tools:

```bash
pkg install -y git clang make autoconf automake libtool pkg-config \
  boost-dev libevent-dev openssl-dev sqlite-dev python cmake wget
```

---

## Part B — Build the node on the phone

```bash
cd ~
git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
./autogen.sh
./configure --without-gui --disable-tests --disable-bench
make -j$(nproc)
```

If configure fails on wallet BDB:

```bash
./configure --without-gui --disable-wallet --disable-tests --disable-bench
make -j$(nproc)
```

Wait — first build can take a long time on a phone. Keep charging.

Check:

```bash
./src/egad -version
./src/ega-cli -version
```

---

## Part C — Light node config

```bash
mkdir -p ~/.ega
nano ~/.ega/ega.conf
```

Paste (change password):

```
server=1
listen=1
txindex=0
prune=1024
dbcache=100
maxconnections=8
listenonion=0

rpcuser=ega
rpcpassword=pick-a-long-secret
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcport=20202
port=20201

addnode=105.225.132.175:20201
algo=yespower-ega
```

Save: Ctrl+O, Enter, Ctrl+X.

Or from the repo (if script is present):

```bash
bash scripts/setup-android-node.sh 105.225.132.175
# then edit rpcpassword in ~/.ega/ega.conf
```

---

## Part D — Start the node

```bash
cd ~/ega
./src/egad -daemon
sleep 3
./src/ega-cli getblockchaininfo
./src/ega-cli getconnectioncount
```

- `blocks` should start rising / match the network  
- `getconnectioncount` ≥ 1 when it reaches the home seed  

Keep Termux alive: Android → Settings → Apps → Termux → Battery → **Unrestricted**.  
Optional: `termux-wake-lock`

Stop later:

```bash
./src/ega-cli stop
```

---

## Part E — Wallet on Android

### Option 1 — CLI (simplest)

```bash
./src/ega-cli getnewaddress
./src/ega-cli getwalletinfo
./src/ega-cli getbalance
```

Backup: copy `~/.ega/wallet.dat` somewhere safe (and never post it online).

### Option 2 — Web wallet in Chrome (same phone)

On the phone, in Termux:

```bash
cd ~/ega
# need the web wallet server (same repo)
bash scripts/start-web-wallet.sh
```

Then open Chrome on the phone:

```
http://127.0.0.1:8090/
```

Tap **Open wallet** → see balance, new address, send.

### Option 3 — Web wallet from another device on Wi‑Fi

Only if you bind RPC carefully (default is localhost-only — safer).  
Prefer Option 2 on the phone itself.

---

## Part F — Solo mine on the phone

```bash
ADDR=$(./src/ega-cli getnewaddress)
./src/ega-cli generatetoaddress 1 $ADDR 500000 yespower-ega
```

Heat and battery will rise — use while charging.

Shared pool from phone (when you have a miner app that speaks stratum):

```
stratum+tcp://105.225.132.175:3335
user = your E… address
pass = x
```

(YespowerEGA shared port)

---

## Part G — Free second peer (your plan)

| Device | Role |
|--------|------|
| Home PC | Public seed, port **20201** forwarded |
| Android | Node with `addnode=105.225.132.175:20201` |

On home PC check:

```bash
./src/ega-cli getconnectioncount
```

When the phone is online and connected, this can become **1+** without a VPS.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `configure` fails | Install missing `pkg` packages; try `--disable-wallet` |
| `getconnectioncount` 0 | Home seed offline / wrong IP / phone offline; check home `egad` and forward |
| No balance after mine | Wait for maturity (~8 blocks); check `getwalletinfo` immature |
| Termux killed | Battery unrestricted + wake-lock |
| Out of space | `prune=1024` already limits; free storage |

---

## Links

- Seed: `105.225.132.175:20201`  
- Pool UI: http://105.225.132.175:8089/ (if port forwarded)  
- Explorer: http://105.225.132.175:8088/  
- Site: https://egalitarianism-ega.github.io/ega-website/  
- Repo: https://github.com/Egalitarianism-EGA/ega  
