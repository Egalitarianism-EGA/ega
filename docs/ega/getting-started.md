# Getting started

## Download

Prebuilt Linux: https://github.com/Egalitarianism-EGA/ega/releases

Or build:

```bash
git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
bash scripts/easy-install-linux.sh
```

After upgrading from an older build: wipe local chain data (consensus MultiShield-4):

```bash
bash scripts/reset-mainnet-datadir.sh
```

## Run

```bash
bash scripts/easy-start.sh
bash scripts/easy-wallet.sh
bash scripts/easy-mine.sh randomx
# also: yespower-ega | verthash | scrypt
```

## Explorer & pool (on your PC)

```bash
bash scripts/ega-explorer.sh        # http://127.0.0.1:8088
bash scripts/start-miningcore.sh    # Verthash stratum :3334 · API :4000
# optional lightweight pool UI: bash scripts/ega-pool.sh
```

Website: https://egalitarianism-ega.github.io/ega-website/

## Algorithms (MultiShield-4)

| Algo | Command / path |
|------|----------------|
| RandomX | `easy-mine.sh randomx` |
| YespowerEGA | `easy-mine.sh yespower-ega` |
| Verthash | GPU: [ega-verthash-miner](https://github.com/Egalitarianism-EGA/ega-verthash-miner) |
| Scrypt | `easy-mine.sh scrypt` |

## Always-on public seed (Oracle free ARM)

Cheap Ampere A1 (2 OCPU / 12 GB) is enough for a **seed node** (not mining farm):

- Guide: [`ORACLE-ARM-SEED.md`](./ORACLE-ARM-SEED.md)
- Helper: `bash scripts/setup-seed-node.sh [peer_ip]`

## Gentle multi-algo keep-alive (home PC)

```bash
bash scripts/low-power-mine.sh all 600   # 1 block / 10 min, rotates all 4
```


## Android light node (no VPS)

Run a pruned validating node on Termux — use your phone as a second peer:

- Guide: [`ANDROID-LIGHT-NODE.md`](./ANDROID-LIGHT-NODE.md)
- Config helper: `bash scripts/setup-android-node.sh`

## Web wallet

```bash
bash scripts/start-web-wallet.sh
# http://127.0.0.1:8090/  (phone on Wi-Fi: http://YOUR_LAN_IP:8090/)
```

## Mining UI (solo vs shared)

```bash
bash scripts/ega-pool-ui.sh
# http://127.0.0.1:8089/  → Solo · Shared · Start · Blocks · Wallet
```
