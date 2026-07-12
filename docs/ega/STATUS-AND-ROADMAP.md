# Egalitarianism (EGA) — Where we are & what’s next

**Full name:** Egalitarianism  
**Ticker / short:** EGA  

---

## 1. Why GitHub Actions failed

**Not a consensus bug.** CI used ancient DigiByte workflow with **`actions/cache@v2`**, which GitHub **rejects** now.

**Fix:** workflow updated to `actions/checkout@v4` + `actions/cache@v4` and a simpler Linux `egad` build (see `.github/workflows/ci-coverage.yml`). Push that fix and the red X should clear on the next run.

---

## 2. What we **have** (blockchain / node)

| Area | Status |
|------|--------|
| Consensus params (21B, 8 decimals, 50k/210k, 60s, 0 premine) | **Done** |
| MultiShield-4: RandomX, Verthash, YespowerEGA, Scrypt | **Done** |
| MultiShield difficulty | **Done** |
| Genesis freeze (main/test/regtest) | **Done** |
| Network identity (ports, magic, bech32 `ega`, `~/.ega`) | **Done** |
| Binaries `egad` / `ega-cli` / `ega-tx` / `ega-qt` | **Built locally** |
| Wallet RPC + solo mine all 4 algos (MultiShield-4) | **Verified** |
| GPU Verthash (OpenCL, your RTX) | **Verified ~0.9 MH/s** |
| Logos + docs under `docs/ega/` | **Done** |
| GitHub org repos | **Live** (see below) |

### Repos

| Repo | Role |
|------|------|
| [ega](https://github.com/Egalitarianism-EGA/ega) | Full node (this code) |
| [ega-miningcore](https://github.com/Egalitarianism-EGA/ega-miningcore) | Pool **configs** (not full pool install) |
| [ega-blockbook](https://github.com/Egalitarianism-EGA/ega-blockbook) | Explorer **coin def** |
| [ega-verthash-miner](https://github.com/Egalitarianism-EGA/ega-verthash-miner) | GPU Verthash how-to + dataset script |

---

## 3. What’s **left** (honest)

### On-chain / Core (medium)

- Public **seed nodes** (you or friends run 24/7 `egad` + share IP)
- Optional: raise/adjust min difficulty after launch hashrate exists
- Optional: RandomX **full dataset** mode for high-end CPU farms
- Deeper DigiByte string cleanup (internal code still says digibyte in places)
- Release **binaries** (Linux tarball / Windows zip) so non-builders can join
- CI green after workflow fix
- GUI polish (window titles still partly DigiByte heritage)

### Network services (not inside Core)

| Service | Status | Free home-PC option |
|---------|--------|---------------------|
| **Second peer** | Need ≥2 nodes for a “network” | Friend’s PC or second machine |
| **DNS seeds** | Empty | Later; until then `addnode=IP` |
| **Explorer** | Config only | Blockbook/Insight on your PC + free tunnel |
| **Stratum pool** | Config only | Miningcore on your PC (heavier: needs Postgres) |
| **Website** | Live (Pages) | https://egalitarianism-ega.github.io/ega-website/ |
| **Whitepaper** | Draft in repo | `docs/ega/WHITEPAPER.md` |
| **Multi-node mining** | Demo verified | `scripts/two-node-mining-demo.sh` |

### Product / go-to-market

- [x] Getting started guide (`docs/ega/getting-started.md`)  
- [x] Desktop app launchers (Wallet / Node / Miner)  
- [x] Network multi-miner docs  
- [ ] Prebuilt Releases for non-builders  
- [ ] Public seed IP list  
- Security review of wallet/RPC exposure if you open ports to internet  

---

## 4. Miners: what exists & how to run them

| Algo | Who mines | How today |
|------|-----------|-----------|
| **RandomX** | CPU (Ryzen etc.) | `ega-cli generatetoaddress 1 $ADDR 10000000 randomx` |
| **YespowerEGA** | CPU / phones / Pi | same with `yespower-ega` |
| **Scrypt** | ASIC / capital market | `… scrypt` |
| **Verthash** | GPU | **VerthashMiner** + EGA dataset + GBT (see ega-verthash-miner) |

There is **no** bundled third-party “download installer miner” for RandomX/Yespower yet — use:

1. **Built-in solo** (simplest for launch)  
2. **External GPU** for Verthash (proven)  
3. **Pool** later when Miningcore is fully wired for multi-algo  

### Solo (any algo) — on your PC

```bash
egad -daemon
ADDR=$(ega-cli getnewaddress)
ega-cli generatetoaddress 1 "$ADDR" 10000000 randomx
ega-cli generatetoaddress 1 "$ADDR" 10000000 yespower-ega
# GPU Verthash: follow ega-verthash-miner README (algo=verthash in ega.conf)
```

### GPU Verthash (real GPU)

See: https://github.com/Egalitarianism-EGA/ega-verthash-miner  
Needs: `egad` with `algo=verthash`, dataset file, VerthashMiner OpenCL.

### Pool (later)

Configs only in **ega-miningcore**. You still install Miningcore + Postgres, then point miners at `stratum+tcp://YOUR_IP:3333` etc.

---

## 5. Host everything on **one PC** for free?

**Yes for a private / “friends & family” live network.**  
**No for a huge public internet product** without more ops.

| Stack | Free on home PC? | Notes |
|-------|------------------|--------|
| `egad` node | Yes | Always on, port **20201** if others connect |
| Solo mining (CPU+GPU) | Yes | What you already did |
| Wallet GUI | Yes | `ega-qt` |
| Explorer | Yes* | Blockbook or light RPC explorer; RAM/disk hungry |
| Pool | Possible* | Miningcore + DB; more setup |
| Public HTTPS | Free tunnels | **Cloudflare Tunnel** / ngrok free tier (no router port-forward) |
| Domain | Cheap/free | Free subdomain via tunnel, or buy domain later |

\*Explorer/pool are **separate installs**, not one click from Core.

### Minimal “go live on my PC only”

1. Run `egad` 24/7 (mainnet), open **20201** or use Tailscale/Cloudflare Tunnel  
2. Mine with CPU + GPU (you) so the chain moves  
3. Friends: `addnode=YOUR_PUBLIC_OR_TUNNEL:20201` + same software  
4. Optional: simple explorer later  
5. Pool when hashrate > solo convenience  

That’s a **real live chain** even with one powerful PC — just small and not “global infrastructure.”

---

## 6. Next steps (recommended order)

| # | Action | Why |
|---|--------|-----|
| 1 | **Revoke exposed GitHub PAT** if not already | Security |
| 2 | Push CI fix, confirm Actions green | Trust for contributors |
| 3 | Write **tokenomics + whitepaper + roadmap** (MD in repo) | Narrative for launch |
| 4 | **24/7 egad** on your PC + mine (keep tip fresh) | Live chain |
| 5 | Share `addnode` with 1–2 friends | Network > 1 |
| 6 | Optional free explorer (RPC explorer / Blockbook) | Visibility |
| 7 | Miningcore when you want public hashrate | Pool |
| 8 | Linux release tarball of `egad`/`ega-cli`/`ega-qt` | Non-builders |

---

## 7. Tokenomics / whitepaper (what to publish)

Already decided technically — document as **Egalitarianism**:

- Max supply **21,000,000,000 EGA**  
- **8** decimals  
- Block **50,000 EGA**, halve every **210,000** blocks  
- Block time **~60s**  
- **0 premine**, fair launch  
- PoW: RandomX + Verthash + YespowerEGA + Scrypt (MultiShield-4)  
- Vision: anyone can mine (CPU / GPU / low-end)  

Still to write as narrative: why multi-algo, emission chart, no VC allocation, risk disclaimer, roadmap timeline.

---

## Bottom line

| Question | Answer |
|----------|--------|
| CI red? | **Deprecated cache action** — fixed in workflow update |
| Blockchain core ready to run/mine? | **Yes** |
| Full global network product? | **Not yet** — needs seeds, peers, optional explorer/pool |
| Miners ready? | **Solo CLI all 4 algos + GPU Verthash**; pool not fully deployed |
| Host free on your PC? | **Yes** for node + mining + optional tunnel; explorer/pool heavier but doable |
| Whitepaper? | **Should do** — next doc deliverable |

**You are at: “launchable single-operator / small community chain.”**  
**Not yet at: “exchange-ready multi-continent infra.”**
