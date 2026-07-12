# What is Qt? What is a pool coin profile?

**Project full name:** **Egalitarianism** (ticker / short name **EGA**).

---

## What is Qt?

**Qt** is a toolkit for building **desktop apps with windows, buttons, menus** (cross-platform: Linux, Windows, macOS).

- **`ega-qt`** = Egalitarianism’s **graphical wallet** (like DigiByte-Qt / Bitcoin-Qt).
- **`egad` + `ega-cli`** = headless daemon + command line (no windows).

| You want… | Use |
|-----------|-----|
| Run a node / mine / script | `egad` + `ega-cli` |
| Point-and-click send/receive | `ega-qt` (needs Qt5 libraries to build) |

Qt is **not** required for launch mining. CLI is enough.

Build GUI later:

```bash
sudo apt install qtbase5-dev qttools5-dev-tools libqrencode-dev
./configure --with-gui=qt5 --enable-wallet --with-incompatible-bdb
make -j$(nproc)
./src/qt/ega-qt
```

---

## What is a “pool coin profile”?

A **mining pool** is separate software that:

1. Talks to **your node** (`egad`) via RPC (`getblocktemplate` / `submitblock`)
2. Talks to **miners** via **Stratum** (port like 3333)
3. Splits rewards among workers

A **coin profile** (also called coin config / coin definition) is a small config file that tells the pool:

| Field | EGA example |
|-------|-------------|
| Name / ticker | Egalitarianism / EGA |
| Node RPC | `127.0.0.1:20202` |
| Algorithm | `randomx` or `verthash` or `yespower` |
| Algo params | Yespower: N=2048, r=32, pers=`YespowerEGA` |
| Block time | 60s |
| Explorer link | (when you have one) |
| Payout address | pool wallet |

Many pools run **one profile per algo** (4 stratum ports for MultiShield-4).

You don’t invent that from Core — you **fork Miningcore / NOMP / Yiimp** and add an `ega.json` (or similar) profile. See `ECOSYSTEM.md`.

---

## Fork GUI / explorer / pool?

| Component | Source | Modify |
|-----------|--------|--------|
| **GUI** | Already in this repo (`src/qt/`) | Rebuild as `ega-qt`, logos already partly applied |
| **Explorer** | Fork **Blockbook** or Insight | New coin def + logos + RPC to egad |
| **Pool** | Fork **Miningcore** or NOMP | Coin profile(s) + 4 algos |

DigiByte Core is the **node**; explorer/pool are **other projects** that sit next to it.

---

## Mining on this machine

- **RandomX + YespowerEGA** → **CPU** (your Ryzen is ideal)
- **Verthash** → designed for **GPU**; in *this* node, `generatetoaddress … verthash` still runs the Verthash **hash on CPU** (works for testing; a real GPU miner is a separate binary that uses the GPU and submits via GBT/stratum)

So:
- CLI can fully test all four algos for **correctness**
- **GPU hashrate** for Verthash needs a GPU Verthash miner + pool or GBT later
