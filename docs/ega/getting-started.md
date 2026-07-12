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
