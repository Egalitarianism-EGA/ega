# Egalitarianism (EGA) — Whitepaper (v0.1 draft)

**Egalitarianism** is a fair-launch, multi-algorithm Proof-of-Work cryptocurrency designed so ordinary people—not only industrial farms—can participate in securing the network.

> Status: **living draft** aligned with the shipped Core parameters. Not financial advice.

---

## 1. Vision

Money and mining power should not require elite hardware or insider allocation.

**Egalitarianism** aims to:

- Keep **permissionless** access to create and transfer value  
- Keep **mining open** to CPUs, consumer GPUs, phones, and single-board computers  
- Avoid **premine / founder stash** that recreates inequality at genesis  
- Resist capture by a **single hardware class** (ASIC-only, GPU-only, or CPU-botnet monoculture)

Short name / ticker: **EGA**.

---

## 2. Design principles

1. **Fair launch** — no premine; genesis coinbase value is zero.  
2. **Multi-door mining** — three algorithms, three hardware “doors.”  
3. **Simple emission** — Bitcoin-style halvings, transparent math.  
4. **Independence of difficulty** — MultiShield-style per-algo adjustment so one algo’s hashrate does not freeze the others.  
5. **Honesty** — farms can still outspend individuals; the design raises the bar for monopoly, it does not magically erase capital.

---

## 3. Tokenomics (consensus)

| Parameter | Value |
|-----------|--------|
| Name | Egalitarianism |
| Ticker | EGA |
| Max supply | **21,000,000,000** EGA |
| Decimals | **8** (1 EGA = 10⁸ base units) |
| Initial block subsidy | **50,000** EGA |
| Halving interval | **210,000** blocks |
| Target block time | **~60 seconds** (all algos share the chain) |
| Premine | **0** |
| Coinbase maturity | Bitcoin-family maturity rules (rewards unlock after maturity) |

### Emission intuition

Same geometric structure as Bitcoin, scaled:

\[
\sum_{i=0}^{\infty} 50000 \times \frac{1}{2^{i}} \times 210000 \approx 21 \times 10^{9}
\]

Integer halvings yield **just under** 21B due to truncation (same class of effect as Bitcoin).

Approximate timeline (at 60s blocks):

| Era | Blocks | ~Time from genesis | Subsidy |
|-----|--------|--------------------|---------|
| 0 | 0–209,999 | ~0–4 months | 50,000 |
| 1 | 210k–419,999 | ~4–8 months | 25,000 |
| 2 | … | … | 12,500 |
| … | … | decades of tail | → 0 |

*(Exact calendar time depends on real average block intervals.)*

### No allocation table (by design)

| Bucket | % |
|--------|---|
| Premine / team | **0%** |
| VC / ICO | **0%** |
| Public PoW | **100% of emission** |

Development funding, if any, is **off-chain** (donations, voluntary tips)—not baked into consensus.

---

## 4. Consensus & mining

### Algorithms (from height 0)

| Algo | Primary hardware | Role |
|------|------------------|------|
| **RandomX** | Modern CPUs, capable phones/PCs | CPU path |
| **Verthash** | Consumer GPUs | GPU path |
| **YespowerEGA** | Low-RAM / older devices | Inclusive CPU path |

**YespowerEGA** parameters: YESPOWER 1.0, **N=2048**, **r=32**, personalization string **`YespowerEGA`**.

**Verthash (EGA):** same memory-hard seek algorithm as Vertcoin-style Verthash, with EGA dataset tag **`EGA-Verthash-v1`** (256 MiB in Core). GPU miners must use that dataset for valid work.

**RandomX:** light-VM path in Core for broad hardware; full-dataset mode is a future optimization for high-end CPUs.

### Difficulty

**MultiShield-style** (DigiByte V4 family): independent difficulty per algorithm, with global timing pressure so overall block time stays near 60s and shares trend toward balance across algos.

### Network identity

| Item | Mainnet |
|------|---------|
| P2P port | 20201 |
| RPC port | 20202 |
| bech32 HRP | `ega` |
| Magic | `e4 47 41 01` |
| Genesis | See `docs/ega/params.md` |

Changing genesis or money constants after launch creates a **different chain**.

---

## 5. Node software

**Egalitarianism Core** (`egad`, `ega-cli`, `ega-qt`) is a full node derived from DigiByte/Bitcoin Core architecture, customized for the above rules.

- **CLI** for servers and miners  
- **Qt GUI** for desktop wallet use  
- Solo mining via RPC; GBT for external miners  

Source: https://github.com/Egalitarianism-EGA/ega  

---

## 6. Roadmap

### Phase A — Live chain (now → weeks)

- [x] Consensus + triple PoW + genesis  
- [x] Solo mining (CPU + GPU Verthash path)  
- [ ] Green CI  
- [ ] 24/7 seed node(s)  
- [ ] Public `addnode` list  
- [ ] Linux binary release tarball  

### Phase B — Community (weeks → months)

- [ ] 5+ independent nodes  
- [ ] Lightweight or Blockbook explorer  
- [ ] Miningcore (or similar) multi-algo pool  
- [ ] User-facing “How to mine” pages  
- [ ] Security notes for open RPC  

### Phase C — Maturity (months+)

- [ ] Hardened releases (signed binaries)  
- [ ] Optional RandomX full-mem mining  
- [ ] Algo upgrade policy if ASICs appear  
- [ ] Governance discussion (soft/hard fork process only—no on-chain “council premine”)  

---

## 7. Risks

- **Low hashrate** → easier 51% early; mitigated by multi-algo, not eliminated  
- **Software bugs** in a young fork  
- **Regulatory / scam perception** of fair-launch coins—transparency helps  
- **Pool centralization** if one pool dominates a single algo  
- **Dataset/miner mismatch** for Verthash if third-party miners use wrong `verthash.dat`  

---

## 8. Disclaimer

This document describes software and economic parameters. It is **not** an offer of securities, investment advice, or a promise of value. Cryptocurrency involves risk of total loss. Run software at your own risk.

---

## 9. References (in-repo)

- `docs/ega/params.md` — numeric freeze  
- `docs/ega/design.md` — engineering design  
- `docs/ega/STATUS-AND-ROADMAP.md` — operational status  
- `docs/ega/USER-GUIDE-LAUNCH.md` — how to run/mine  
