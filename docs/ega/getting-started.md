# Getting started with Egalitarianism (EGA)

Install the software, open a wallet, run a node, and mine.  
Works on Linux today (Windows build docs available; macOS later).

## What you get

| Application | Program | Purpose |
|-------------|---------|---------|
| **Wallet** | `ega-qt` | Desktop wallet (send / receive) |
| **Node** | `egad` | Full network participant |
| **CLI** | `ega-cli` | Control node & mine from terminal |
| **GPU miner** | VerthashMiner + EGA dataset | Mine Verthash on a GPU |

All of this comes from: https://github.com/Egalitarianism-EGA/ega  
GPU guide: https://github.com/Egalitarianism-EGA/ega-verthash-miner  

---

## Linux install

```bash
git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
bash scripts/easy-install-linux.sh
```

Optional desktop wallet (needs Qt5 packages):

```bash
sudo apt install qtbase5-dev qttools5-dev-tools libqrencode-dev
./configure --with-gui=qt5 --enable-wallet --with-incompatible-bdb
make -j$(nproc)
```

### Install desktop shortcuts (optional)

```bash
bash scripts/install-desktop-apps.sh
```

That puts **Egalitarianism Wallet**, **Egalitarianism Node**, and **Egalitarianism Miner** in your app menu (Linux `.desktop` files).

---

## Run a node

```bash
bash scripts/easy-start.sh
# or: ./src/egad -daemon
```

Config lives in `~/.ega/ega.conf`.  
P2P port **20201** (for other nodes). Keep **RPC 20202** local only.

---

## Wallet

**GUI**

```bash
./src/qt/ega-qt
```

**Terminal**

```bash
bash scripts/easy-wallet.sh
# or: ./src/ega-cli getnewaddress
./src/ega-cli backupwallet ~/ega-wallet-backup.dat
```

---

## Mining

### Solo (you keep the block)

```bash
bash scripts/easy-mine.sh randomx        # CPU
bash scripts/easy-mine.sh yespower-ega   # CPU / weaker machines
# GPU Verthash → see ega-verthash-miner
```

### Two or more miners on the **same chain** (normal network)

This is how Bitcoin-style networks work: nodes connect, everyone builds on the **same tip**, whoever finds the next block gets that reward.

1. Computer A runs `egad` (seed).
2. Computer B installs the same software.
3. On B, set in `~/.ega/ega.conf`:

```
addnode=IP_OF_A:20201
```

4. Both mine (solo or pool). They compete on the same chain; the network stays one history.

Automated local test (two nodes on one PC):

```bash
bash scripts/two-node-mining-demo.sh
```

### Pool (shared rewards)

Optional later. Configs: https://github.com/Egalitarianism-EGA/ega-miningcore  
Not required for a live multi-miner network.

---

## Join someone else’s node

```
# ~/.ega/ega.conf
addnode=THEIR_IP:20201
```

Same software version / same genesis as Core docs.

---

## More detail

- Network parameters: `docs/ega/params.md`  
- Whitepaper draft: `docs/ega/WHITEPAPER.md`  
- Continuity for developers: `EGA-HANDOFF.txt`  
