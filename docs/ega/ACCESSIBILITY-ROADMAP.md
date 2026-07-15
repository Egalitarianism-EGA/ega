# Accessibility roadmap — mining & nodes for everyone

**Mission:** EGA is for people with weak hardware, old phones, no cloud budget, and no ASICs.  
MultiShield-4 exists so **CPU, weak CPU, GPU, and hard door** all share the same chain (~25% each).  
**Poor people are not second-class:** they get real mining and a real path onto the network.

This document is the **systematic plan**. Everything below is required for “done,” not optional nice-to-haves.

---

## Principles

1. **Solo and shared** available on **all four** algos.  
2. **Light participation** (phone/tablet) is first-class — not “full node or nothing.”  
3. **Zero paid cloud required** — home seed + friend peer is enough to start.  
4. **Downloads** work for Linux first, then Windows, then mobile.  
5. **Honest UX** — never present raw API as the product; never fake hashrate.

---

## What “light node” means (Android / tablet / weak PC)

| Mode | What it does | Hardware | Status |
|------|----------------|----------|--------|
| **Full node** (`egad`) | Validates full chain, relays peers | PC / always-on box | **Shipped** (Linux) |
| **Pruned full node** | Same rules, less disk | Weak PC | Possible (Bitcoin-family prune) — enable & document |
| **Light / SPV client** | Headers + filters / server trust model | Phone, tablet | **To build** |
| **Remote wallet** | Talks to *your* node or public electrum-style server | Phone | **To build** |
| **Web wallet** | Browser UI over remote RPC (careful security) | Any device | **Scaffold** |

**Why light clients matter for accessibility:**  
Every Android that stays online as a **wallet + optional miner** or **light peer** grows the community. Full archival nodes stay on desktops/home PCs. That is still “more of the network” in the social/economic sense (users, hashrate, addresses). Full validating peers remain the security backbone.

**Android full `egad`:** technically possible (Termux / native aarch64) but **battery, storage, and heat** make it a bad default. Prefer: **light wallet + CPU mine (Yespower/RandomX)** on phone; **full node** on free home PC.

---

## Mining for everyone

| Algo | Hardware | Solo | Shared pool |
|------|----------|------|-------------|
| RandomX | Laptop / desktop CPU | **Yes** | **Required** (Miningcore custom) |
| YespowerEGA | Phone / Pi / weak CPU | **Yes** | **Required** (Miningcore custom) |
| Verthash | Consumer GPU | **Yes** | **Live** (Miningcore) |
| Scrypt | CPU / later ASIC door | **Yes** | **Live** (Miningcore) |

**Shared mining** = many people combine work; paid by shares when the pool finds a block (low variance).  
**Solo mining** = you keep the whole block when you find it (high variance).  
Both are part of the mission.

---

## Phases (do in order)

### Phase A — Foundation (mostly done)
- [x] MultiShield-4 consensus  
- [x] Fair launch params, genesis, ports, `egad` / `ega-cli`  
- [x] Linux Release v0.2.0  
- [x] Local explorer + address/reward pages  
- [x] Home seed path (no paid VPS)  
- [x] Verthash + Scrypt stratum (Miningcore)  
- [x] Basic pool human UI (`:8089`)  
- [ ] ≥1 external peer (`getconnectioncount` > 0)

### Phase B — Pool product (HeroMiners-style, EGA only)
- [ ] Full pool site: **Home · Start · Blocks · Payments · Wallet lookup · Workers**  
- [ ] One page per algo (4 networks) with clear stratum strings  
- [ ] RandomX shared pool (custom Miningcore / fork)  
- [ ] YespowerEGA shared pool (custom Miningcore / fork)  
- [ ] Public ports documented; operator runbook  

### Phase C — Desktop GUIs (downloadable)
- [x] `ega-qt` built on operator Linux  
- [ ] Always ship `ega-qt` in Linux release tarball  
- [ ] Installer / portable **Windows** (`egad`, `ega-cli`, `ega-qt`)  
- [ ] Desktop launchers polished (Wallet / Node / Miner)  
- [ ] In-app links: explorer URL, pool Start page, seed `addnode`  

### Phase D — Mobile & light clients
- [ ] **Web wallet** (connect to user node or public light server)  
- [ ] **Android** app or PWA: balance, receive, send (via light server)  
- [ ] **Android miner** (YespowerEGA first, then RandomX if feasible)  
- [ ] Optional Termux guide: light / pruned node for advanced users  
- [ ] Public light/API endpoint docs (when a home/server runs them)

### Phase E — Network growth (still free-first)
- [ ] Second home seed (friend)  
- [ ] `SEEDS.md` + website seed list  
- [ ] Optional Cloudflare tunnel for explorer (no card)  
- [ ] When funds exist: cheap VPS seed (optional, not required)

---

## Engineering notes (for implementers)

### Shared RandomX / Yespower on EGA
Stock Miningcore:
- Verthash / Scrypt = Bitcoin-family header hashers ✓  
- RandomX in Miningcore = Cryptonote path ✗ for EGA  
- YespowerEGA = not present as EGA multi-algo hasher ✗  

Work required:
1. `getblocktemplate` with `algo=randomx` / `yespower-ega`  
2. Job encode Bitcoin-family header + version bits  
3. Share verify via RandomX light + YespowerEGA params (N=2048,r=32)  
4. Submit block via node RPC  
5. Stratum ports e.g. **3333** (RX), **3335** (YP)

### Light client
Short path:
1. Public (or self-hosted) **electrum-style** or **REST** server in front of `egad`  
2. Mobile/web talks only to that server  
3. Later: Neutrino/SPV if we invest in header filters  

### Security
- Never expose RPC `20202` to WAN  
- Mobile web wallet = warn about phishing; prefer deep-link to user’s own node  
- Pool username = payout address only  

---

## Success metrics (mission)

| Metric | Target |
|--------|--------|
| Someone with only a phone | Can hold EGA + mine Yespower or join pool when live |
| Someone with only a laptop | Full node + solo any algo + pool VH/Scrypt |
| Someone with no cloud money | Is a seed via home port-forward |
| Shared mining | All 4 algos on stratum |
| Downloads | Linux + Windows wallets; Android PWA/app |

---

## Immediate next build steps

1. Upgrade pool UI (Start / Blocks / address lookup) using Miningcore API.  
2. Keep shipping explorer + node; document phone path honestly.  
3. Scaffold web wallet shell in-repo.  
4. Spec Miningcore fork for RX/YP.  
5. Bundle `ega-qt` in `make-release.sh`.  

*Last updated: 2026-07-15*
