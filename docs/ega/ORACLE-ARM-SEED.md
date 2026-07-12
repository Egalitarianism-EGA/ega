# Oracle Cloud Free Tier — Ampere A1 (ARM64) seed node

**Goal:** cheap always-on **public peer / seed** for Egalitarianism (EGA).  
**Not for:** heavy mining, GPU pool, or Miningcore (use your home PC for that).

## What Oracle gives you (Always Free, as of 2026)

| Resource | Typical free allowance |
|----------|------------------------|
| Compute | **Ampere A1** up to **2 OCPU + 12 GB RAM** (ARM64) — one VM or split |
| Storage | **200 GB** block volume |
| Bandwidth | Generous / effectively unmetered for normal node traffic |
| x86 micro | 2× (1/8 OCPU, 1 GB) — **too small** for EGA |

Signup needs a card (auth hold). Idle/abandoned accounts can be reclaimed — keep the VM doing *something* (egad running counts).

**ToS:** normal **full node / seed** is the intended use. Don’t run aggressive public mining farms on free tier.

## Spec fit for EGA

| Workload | 2 OCPU / 12 GB A1 |
|----------|-------------------|
| `egad` seed (listen + sync) | **Yes** — comfortable |
| Wallet + rare solo mine (CPU) | **Yes** — light only |
| Local explorer (Python) | **Yes** if RAM left (~11 GB free after node) |
| Miningcore multi-algo pool | **No** — keep on home x86 + GPU |
| GPU Verthash | **No** — no GPU on A1 |

**Recommended shape:** one VM, **2 OCPU / 8–12 GB RAM**, **50–100 GB** boot volume (200 GB free total is fine), Ubuntu **22.04/24.04 aarch64**.

## Architecture: home PC vs Oracle

```
[ Your PC: RTX / Miningcore / GPU Verthash / optional low-power mine ]
         \  addnode=
          \____ P2P 20201 ____[ Oracle A1: egad seed, always on ]
                                    |
                              public IP:20201
                         (friends / other nodes)
```

- **Oracle** = always-on **seed** (and optional public explorer later).  
- **Home** = wallet, GPU Verthash pool path, low-power MultiShield tests.  
- Peers: `addnode=ORACLE_PUBLIC_IP:20201` and on Oracle `addnode=HOME_IP:20201` if home is reachable.

## 1. Create the VM

1. Oracle Cloud → **Create Instance**.  
2. Image: **Canonical Ubuntu 22.04 or 24.04 (aarch64)**.  
3. Shape: **VM.Standard.A1.Flex** — 2 OCPU, 12 GB (or 1 OCPU / 6 GB if you split).  
4. Networking: assign **public IP**.  
5. Security list / NSG ingress:
   - **TCP 22** (SSH — lock to your IP if possible)  
   - **TCP 20201** (EGA P2P)  
   - Optional later: **TCP 8088** (explorer only if you run it)  
   - **Do not** open **20202** (RPC).

## 2. Build EGA on ARM64 (on the VM)

RandomX ships with **aarch64** support. Scrypt / YespowerEGA / Verthash (CPU verify) are portable C. Build **on the VM** (native ARM) — simplest:

```bash
sudo apt update
sudo apt install -y build-essential libtool autotools-dev automake pkg-config \
  bsdmainutils python3 libevent-dev libboost-system-dev libboost-filesystem-dev \
  libboost-test-dev libboost-thread-dev libsqlite3-dev libminiupnpc-dev \
  libzmq3-dev libssl-dev git cmake curl

git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
# Prefer release tag when available
# git checkout v0.2.0

./autogen.sh
./configure --without-gui --disable-tests --disable-bench --with-incompatible-bdb \
  || ./configure --without-gui --disable-tests --disable-bench --disable-wallet
# If BDB wallet is painful on ARM, --disable-wallet is OK for a pure seed.

make -j$(nproc)
# binaries: src/egad src/ega-cli  (and ega-tx if built)
```

If `configure` fails on wallet BDB:

```bash
sudo apt install -y libdb-dev libdb++-dev
# or seed-only:
./configure --without-gui --disable-wallet --disable-tests --disable-bench
make -j$(nproc)
```

**Prebuilt ARM release:** not guaranteed yet (v0.2.0 is x86_64 Linux). Track Releases; until then build on A1.

### Sanity (seed does not need to mine)

```bash
./src/egad -version
./src/ega-cli -version
```

## 3. Seed config (`~/.ega/ega.conf`)

```bash
mkdir -p ~/.ega
cat > ~/.ega/ega.conf << 'EOF'
# EGA seed — Oracle Ampere A1
server=1
listen=1
daemon=1
txindex=1

# P2P public; RPC localhost only
port=20201
rpcport=20202
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcuser=ega
rpcpassword=CHANGE_ME_LONG_RANDOM
# onlynet=ipv4

# Optional: your home node if reachable
# addnode=YOUR_HOME_PUBLIC_IP:20201

# Fair-launch solo GBT not required on seed
algo=randomx
EOF
chmod 600 ~/.ega/ega.conf
```

Start:

```bash
# from repo
./src/egad
# or install to /usr/local/bin and use systemd (below)
```

Check:

```bash
./src/ega-cli getblockchaininfo
./src/ega-cli getnetworkinfo   # connections should rise when peers addnode you
./src/ega-cli getpeerinfo
```

## 4. systemd (survive reboot)

```bash
sudo tee /etc/systemd/system/egad.service << EOF
[Unit]
Description=Egalitarianism (EGA) full node
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=ubuntu
ExecStart=/home/ubuntu/ega/src/egad -daemon
ExecStop=/home/ubuntu/ega/src/ega-cli stop
PIDFile=/home/ubuntu/.ega/egad.pid
Restart=on-failure
RestartSec=20
LimitNOFILE=8192

[Install]
WantedBy=multi-user.target
EOF
# Adjust User/paths to match your home + binary location
sudo systemctl daemon-reload
sudo systemctl enable --now egad
sudo systemctl status egad
```

## 5. Publish the seed

Once `getnetworkinfo` shows `localservices` and port is reachable:

| Field | Value |
|-------|--------|
| `addnode` | `ORACLE_PUBLIC_IP:20201` |
| Docs | update `docs/ega/SEEDS.md` |
| Website | optional seed line on mine / getting-started |

From home PC:

```bash
# ~/.ega/ega.conf
addnode=ORACLE_PUBLIC_IP:20201
```

```bash
ega-cli addnode ORACLE_PUBLIC_IP:20201 add
ega-cli getconnectioncount
```

## 6. What **not** to run on A1 free tier

- Full **Miningcore** + Postgres multi-algo pool (heavy; keep home).  
- **24/7 multi-algo CPU mining** (noisy, ToS grey area, weak OCPUs).  
- Opening **RPC** to `0.0.0.0`.  
- Storing the only copy of a hot wallet with large balance (use home / hardware).

Optional light explorer on A1:

```bash
# only if you want a second public explorer; bind 0.0.0.0:8088 + security list
EGA_EXPLORER_HOST=0.0.0.0 bash scripts/ega-explorer.sh
```

## 7. Pool honesty (unchanged)

| Algo | Public pool (home Miningcore) | Solo |
|------|-------------------------------|------|
| Verthash | stratum `:3334` share-verify | GPU recommended |
| Scrypt | stratum `:3336` share-verify | CPU/ASIC path |
| RandomX | **not** in stock Miningcore for EGA headers | `easy-mine.sh randomx` |
| YespowerEGA | **not** in stock Miningcore | `easy-mine.sh yespower-ega` |

## 8. Checklist

- [ ] Ubuntu aarch64 VM, 2 OCPU / 8–12 GB  
- [ ] Ingress **20201** (and 22 locked down)  
- [ ] Build `egad` / `ega-cli` on ARM  
- [ ] `listen=1`, RPC localhost only  
- [ ] systemd enabled  
- [ ] Home node `addnode=` Oracle IP  
- [ ] `SEEDS.md` + friends updated  
- [ ] Occasional SSH / `getblockcount` so account isn’t “abandoned”

## Related

- `docs/ega/SEEDS.md` — live seed list  
- `docs/ega/params.md` — ports, magic, genesis  
- `scripts/setup-seed-node.sh` — conf helper  
- `scripts/low-power-mine.sh` — home PC gentle MultiShield keep-alive  
