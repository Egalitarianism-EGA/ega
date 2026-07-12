# EGA ecosystem: GUI, explorer, stratum pool

## What ships in *this* repo

| Piece | Binary | Ready? |
|-------|--------|--------|
| Full node + wallet (RPC) | `egad` + `ega-cli` | **Yes** (Linux build with `--enable-wallet`) |
| Desktop GUI wallet | `ega-qt` | **Buildable with Qt** — not in default headless configure |
| Block explorer | — | **Separate project** (fork + rebrand) |
| Stratum mining pool | — | **Separate project** (fork + rebrand) |

You do **not** need DigiByte’s explorer/pool code inside this Core tree. Standard practice: keep Core lean; run explorer + pool as their own services.

---

## GUI wallet (`ega-qt`)

Source lives under `src/qt/` (DigiByte Qt heritage). Icons now use EGA coin art (`src/qt/res/icons/ega.png`, etc.).

```bash
# Debian/Ubuntu
sudo apt install -y qtbase5-dev qttools5-dev-tools libqrencode-dev protobuf-compiler libprotobuf-dev

./configure --with-daemon --with-gui=qt5 --enable-wallet --with-incompatible-bdb
make -j$(nproc)
./src/qt/ega-qt
```

If configure cannot find Qt, stick with CLI mining for launch; GUI can ship in a later installer.

---

## Block explorer (recommended approach)

**Yes — use a basic open explorer and rebrand**, not DigiByte Core itself.

Good starting points:

| Project | Notes |
|---------|--------|
| **[Blockbook](https://github.com/trezor/blockbook)** | Production-grade, multi-coin; add an EGA coin definition (ports, genesis, RPC) |
| **Insight API / insight-ui** (Bitcore family) | Older but simple; many alts still fork it |
| **BTC RPC Explorer** style | Single-node explorer talking to `egad` RPC |

**Minimal path for launch day:**

1. Run `egad` with `txindex=1` and RPC enabled  
2. Deploy **Blockbook** or Insight pointed at `127.0.0.1:20202`  
3. Replace logos with `logo/coinlogo.jpg` + `logo/blockchainlogo.jpg`  
4. Set coin name EGA, ticker EGA, ports from `docs/ega/params.md`  

We can add a thin `ecosystem/explorer/` config template in a follow-up (coin.json / env file) without vendoring the whole explorer.

---

## Stratum mining pool

**Yes — fork a multi-algo pool**, not DigiByte’s wallet.

| Project | Notes |
|---------|--------|
| **NOMP** / **node-open-mining-portal** forks | Node.js; many algo plugins |
| **Yiimp** | PHP; multi-algo; heavier ops |
| **Miningcore** | C#; modern; multi-algo |

EGA needs **four** stratum ports or one portal with algo selection:

| Algo | Suggested stratum port (example) |
|------|----------------------------------|
| RandomX | 3333 |
| Verthash | 3334 |
| YespowerEGA | 3335 |
| Scrypt | 3336 |

Pool talks to `egad` via:

- `getblocktemplate` + algo argument  
- `submitblock`  
- wallet/RPC for payouts  

Point each algo at EGA’s hash: RandomX (light/full), Verthash (EGA dataset), Yespower **`YespowerEGA`** (N=2048, r=32), Scrypt (1024/1/1).

**Launch-day alternative (no pool yet):** users solo-mine with:

```bash
ega-cli generatetoaddress 1 "$ADDR" 10000000 randomx
# also: verthash | yespower-ega | scrypt
```

Also: lightweight explorer `bash scripts/ega-explorer.sh` and Miningcore `bash scripts/start-miningcore.sh`.

---

## DigiByte’s own explorer/pool?

- DigiByte **Core** does not ship a modern public explorer/pool inside this tree.  
- DigiByte community tools exist separately; forking **generic** multi-coin software is usually cleaner than reverse-engineering DGB-specific services.  
- Reuse **this** node’s RPC + logos + params — that is the DigiByte-shaped piece you already have.

---

## Suggested order

1. ~~Core node + mining~~ (done)  
2. **Ship `egad` / `ega-cli` + logos** (this pass)  
3. Optional: build **ega-qt** for desktop users  
4. Stand up **explorer** (Blockbook + EGA coin def)  
5. Stand up **pool** (Miningcore or NOMP fork) when demand exists  

---

## Logos

| File | Use |
|------|-----|
| `logo/coinlogo.jpg` | Coin / app icon (pixmaps, Qt, favicon) |
| `logo/blockchainlogo.jpg` | Brand / README / explorer header |
| `share/pixmaps/ega*.png` | Generated icons |
| `doc/ega_logo.png` | README brand mark |
