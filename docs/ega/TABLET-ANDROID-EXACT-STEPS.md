# Exact steps: node + wallet + miner on your Android tablet

**Goal:** tablet runs a real EGA node, a wallet, and can solo-mine (YespowerEGA).  
**Home PC** stays the public seed: `105.225.132.175:20201`  
**Time:** first time can take 1–3+ hours (compile). Charging recommended.

---

## Before you start (on the tablet)

1. Plug in the charger.  
2. Connect to **Wi‑Fi** (same home Wi‑Fi as the PC is easiest).  
3. Free **at least 4 GB** storage.  
4. Install **F-Droid**: https://f-droid.org/  
5. In F-Droid, install **Termux** (package `com.termux`).  
   - Do **not** use the old Termux from Play Store if F-Droid is available.

---

## Step 1 — Open Termux and update

Open the **Termux** app. Type each block, then press Enter.

```bash
pkg update && pkg upgrade -y
```

Allow any prompts. When finished:

```bash
pkg install -y git clang make autoconf automake libtool pkg-config \
  boost-dev libevent-dev openssl-dev sqlite-dev python cmake wget
```

If a package fails, run `pkg update` again and retry that install line.

---

## Step 2 — Download EGA source

```bash
cd ~
git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
```

---

## Step 3 — Build the node (long wait)

```bash
./autogen.sh
./configure --without-gui --disable-tests --disable-bench
make -j$(nproc)
```

If `configure` errors about Berkeley DB / wallet:

```bash
./configure --without-gui --disable-wallet --disable-tests --disable-bench
make -j$(nproc)
```

When done, test:

```bash
./src/egad -version
./src/ega-cli -version
```

You should see version text, not “not found”.

---

## Step 4 — Create light-node config

```bash
mkdir -p ~/.ega
```

Create the config file:

```bash
cat > ~/.ega/ega.conf << 'EOF'
server=1
listen=1
txindex=0
prune=1024
dbcache=100
maxconnections=8
listenonion=0

rpcuser=ega
rpcpassword=CHANGE_THIS_TO_A_LONG_SECRET
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcport=20202
port=20201

# Home seed (public IP — keep updated if ISP changes)
addnode=105.225.132.175:20201

algo=yespower-ega
EOF
```

**Important:** edit the password:

```bash
nano ~/.ega/ega.conf
```

- Change `CHANGE_THIS_TO_A_LONG_SECRET` to something only you know  
- Save: **Volume-down + O** (or Ctrl+O), Enter, then **Volume-down + X** (or Ctrl+X)

---

## Step 5 — Start the node (tablet as peer)

```bash
cd ~/ega
./src/egad -daemon
```

Wait ~5 seconds, then:

```bash
./src/ega-cli getblockchaininfo
./src/ega-cli getconnectioncount
./src/ega-cli getblockcount
```

**What good looks like**

| Command | Good result |
|---------|-------------|
| `getblockcount` | Number rising / near home PC height |
| `getconnectioncount` | **1 or more** (connected to home seed) |

If count stays **0**:

- Home PC must be running `egad`  
- Router must forward **TCP 20201 → PC LAN IP** (your PC was `192.168.0.97`)  
- Tablet on Wi‑Fi, not blocked by VPN  
- Seed IP must be current: **105.225.132.175**

### Keep Termux alive

Android → **Settings → Apps → Termux → Battery → Unrestricted**  
Optional in Termux:

```bash
pkg install -y termux-api
termux-wake-lock
```

---

## Step 6 — Wallet on the tablet

### A) CLI wallet (always works)

```bash
cd ~/ega
./src/ega-cli getnewaddress
```

Copy that address (starts with **E**). That is your receive address.

```bash
./src/ega-cli getwalletinfo
./src/ega-cli getbalance
```

**Backup:** copy `~/.ega/wallet.dat` somewhere safe (Google Drive private folder, USB, etc.).  
Never post `wallet.dat` or your RPC password online.

### B) Web wallet in Chrome (same tablet)

On the **tablet**, still in Termux (node must be running):

```bash
cd ~/ega
bash scripts/start-web-wallet.sh
```

Leave that running. Open **Chrome** on the tablet:

```
http://127.0.0.1:8090/
```

1. Tap **Open wallet**  
2. Tap **New address** if needed  
3. Use **Send** only after balance is spendable (not immature)

To stop web wallet later: in Termux press **Ctrl+C**.

---

## Step 7 — Miner on the tablet (solo)

YespowerEGA is the right algo for a tablet CPU.

```bash
cd ~/ega
ADDR=$(./src/ega-cli getnewaddress)
echo "Mining to $ADDR"
./src/ega-cli generatetoaddress 1 "$ADDR" 500000 yespower-ega
```

- Keep charging; tablet will get warm.  
- One block can take a while.  
- After it finds a block:

```bash
./src/ega-cli getblockcount
./src/ega-cli getwalletinfo
```

Rewards start as **immature**, then become spendable after enough confirmations (~8).

### Shared pool mining (from tablet)

If you install a stratum-capable CPU miner later:

| Setting | Value |
|---------|--------|
| URL | `stratum+tcp://105.225.132.175:3335` |
| Algorithm | Yespower / yespower-ega (if listed) |
| Username | Your **E…** address |
| Password | `x` |

Home PC must leave stratum running and (for internet) forward port **3335**.  
On home Wi‑Fi only, you can try `192.168.0.97:3335` instead of the public IP.

RandomX shared: port **3333** (heavier on a tablet — Yespower is better).

---

## Step 8 — Useful daily commands

```bash
cd ~/ega

# Is node up?
./src/ega-cli getblockchaininfo

# Peers (want ≥ 1)
./src/ega-cli getconnectioncount

# Balance
./src/ega-cli getwalletinfo

# Stop node cleanly
./src/ega-cli stop

# Start node again
./src/egad -daemon
```

---

## Checklist

- [ ] Termux from F-Droid  
- [ ] EGA built (`egad` / `ega-cli` work)  
- [ ] `~/.ega/ega.conf` with seed `105.225.132.175:20201`  
- [ ] `egad -daemon` running  
- [ ] `getconnectioncount` ≥ 1 when home is online  
- [ ] Address saved + wallet backed up  
- [ ] Optional: web wallet on `:8090`  
- [ ] Optional: solo mined at least one Yespower block  

---

## Links (current public host)

| What | Address |
|------|---------|
| Seed (P2P) | `105.225.132.175:20201` |
| Explorer | http://105.225.132.175:8088/ |
| Pool UI | http://105.225.132.175:8089/ |
| Web wallet (if PC serves it) | http://105.225.132.175:8090/ |
| Shared Yespower | `stratum+tcp://105.225.132.175:3335` |
| Website | https://egalitarianism-ega.github.io/ega-website/ |
| Source | https://github.com/Egalitarianism-EGA/ega |

If the home public IP changes again, update `addnode=` / site / `externalip=` to the new IP.
