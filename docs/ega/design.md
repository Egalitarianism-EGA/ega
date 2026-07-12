# EGA (Egalitarianism) Core — Design Spec

**Status:** Phases 1–6 complete (foundation + tests). Platforms: Linux primary, Windows supported, macOS deferred.  
**Date:** 2026-07-12  
**Working tree:** DigiByte-based sources under the project root; EGA-specific docs live in `docs/ega/` for clarity  

---

## 1. Vision

EGA is a privacy-respecting, egalitarian Proof-of-Work chain for people who are unbanked, underbanked, or capital-poor.

**Access goals**

- Anyone with ordinary hardware can mine: phones, laptops, old PCs, Raspberry Pis, consumer GPUs.
- No premine, no founder allocation in consensus.
- Resist easy capture by a single hardware class (ASIC farms, GPU-only warehouses, or CPU-only botnets dominating *all* block production).

**Honesty limits (explicit)**

- PoW does not make wealth irrelevant: rented hash and large farms can still outpace a single phone.
- Vision = **permissionless access + diversified hardware**, not equal income for all devices.
- If an algo is later broken by specialized hardware, the project may replace that algo via a coordinated upgrade (policy; not Phase 1 code).

---

## 2. Frozen economic parameters

| Parameter | Value | Notes |
|-----------|--------|--------|
| Max supply | **21,000,000,000 EGA** | Twenty-one billion |
| Decimals | **8** | `COIN = 100_000_000` |
| `MAX_MONEY` | `21_000_000_000LL * COIN` | Must fit `int64` (`CAmount`) |
| Block subsidy (height 0) | **50,000 EGA** | `50000 * COIN` |
| Halving interval | **210,000** blocks | Bitcoin-style `nSubsidy >>= halvings` |
| Expected total emission | ~**21B** EGA | Same geometric series as Bitcoin, scaled ×1000 |
| Target block time | **60 seconds** | Overall chain rate |
| Premine / genesis reward | **0** | Fair launch |
| Coinbase maturity | Keep DigiByte/Bitcoin defaults unless later revised | Not a Phase 1 change unless required to compile/test |

**Emission math (reference)**

\[
\sum_{i=0}^{\infty} 50000 \times \frac{1}{2^i} \times 210000 \approx 21\,000\,000\,000
\]

**Out of scope for economics layer:** inflation treasuries, dev tax, masternodes.

---

## 3. Proof-of-Work: four algorithms from genesis (MultiShield-4)

No temporary single-algo mainnet. All four are active from height 0.

| ID | Algorithm | Primary hardware | Role |
|----|-----------|------------------|------|
| 0 | **RandomX** | Modern CPUs / laptops | People CPU |
| 1 | **Verthash** | Consumer GPUs | People GPU |
| 2 | **YespowerEGA** | Phones, low-RAM Pis, weak CPUs | Inclusion |
| 3 | **Scrypt** | ASIC / capital market | Security hard door (~25% share) |

### 3.1 YespowerEGA (custom Yespower instance)

- Family: **Yespower** (known implementation; do not hand-roll crypto).
- Instance name: **YespowerEGA** (code: e.g. `ALGO_YESPOWER_EGA`).
- Differentiation from other Yespower coins:
  - Fixed **personalization string** (e.g. `"YespowerEGA"` — exact bytes locked in Phase 3).
  - Fixed cost parameters **N, r** (and any required yespower fields) aimed at **low-end ARM** (target: usable on devices in roughly the **≤256 MB-class** mining comfort zone; exact numbers chosen and documented when the library is integrated).
- Purpose of customization: prevent merge-mining / work reuse with other Yespower chains; require EGA-specific miner builds. Does **not** claim ASIC immunity forever.

### 3.2 Block version / algo selection

- Extend DigiByte multi-algo version bits for these four active algos.
- Other legacy DigiByte algos (sha256d, groestl, skein, qubit, odo as standalone mainnet set, …) stay inactive unless re-added by upgrade.

### 3.3 Integration notes (Phase 3)

- Vendor or submodule: RandomX, Verthash, Yespower reference impl.
- Wire: `GetPoWHash` / `CheckProofOfWork`, mining RPC, any `GetAlgoName` / RPC surface.
- Build system: `configure`/`Makefile` flags and linked libs for all three.

---

## 4. Difficulty: MultiShield from height 0

DigiByte already implements multi-algo difficulty in `src/pow.cpp` (V1–V4). EGA adopts the **MultiShield V4-style** behavior:

- **Per-algorithm difficulty** (independent `nBits` lineage per algo).
- **Global** retarget using an averaging window so overall block time stays near **60s**.
- **Local** per-algo adjustment so under-represented algos get easier work and over-represented get harder → tends toward **~⅓ / ⅓ / ⅓** share without forced strict alternation.
- **No historical activation ladder** (no “MultiShield at block 400k”). Dispatcher uses the MultiShield path from height 0 on mainnet.

**Spacing sketch (Phase 1 constants; tune only if needed later)**

| Constant | Intent |
|----------|--------|
| `nPowTargetSpacing` / chain target | **60** seconds (overall) |
| `NUM_ALGOS` | **4** |
| Per-algo MultiShield spacing | **~240** seconds (4 × 60) |
| Target share | **~25%** per algo |
| `nAveragingInterval` | Start from DigiByte-like **10** unless testing shows need to change |

Legacy V1/V2-only paths should not gate mainnet once simplified; regtest/testnet may allow min-difficulty rules as today.

---

## 5. Network identity (Phase 2)

| Item | Direction |
|------|-----------|
| Magic bytes | EGA-unique (existing WIP `0xe4 0x47 0x41 …` is fine to keep if still unique) |
| P2P / RPC ports | EGA-specific (WIP used 20201-class ports; freeze in Phase 2) |
| DNS seeds | Empty at fair launch; community adds later |
| Checkpoints / assumevalid | Reset for new chain |
| Genesis | Placeholder until Phase 4; **no** final mainnet genesis until Phases 1–3 are done |

Full binary/datadir rename (`egad`, etc.) may wait for Phase 5 so consensus work is not blocked on rebrand churn.

---

## 6. Phased implementation order

Work **strictly** in dependency order. Do not freeze genesis early.

```
Phase 1  Economic constants + 60s timing + MultiShield spacing for 3 algos
Phase 2  Network identity (magic, ports, seeds, checkpoint reset)
Phase 3  RandomX + Verthash + YespowerEGA + V4 MultiShield dispatcher
Phase 4  Mine and freeze genesis (main/test/regtest as needed)
Phase 5  Rebrand, sample conf, README alignment
Phase 6  Tests and hardening
```

### Phase 1 — detailed scope (next implementation)

**In scope**

- `src/amount.h`: 8 decimals; `MAX_MONEY = 21e9 * COIN` (fix overflow).
- `src/validation.cpp`: `GetBlockSubsidy` → 50000 * COIN, halving every `nSubsidyHalvingInterval`.
- `src/chainparams.cpp` (and base where needed):
  - `nSubsidyHalvingInterval = 210000`
  - All relevant target spacings → **60** (and multi-algo spacing **180** for 3 algos)
  - Comments consistent with 21B / dual-no → **triple** algo
  - Premine 0 already intended; keep genesis reward 0
- `docs/ega/params.md`: machine-readable freeze of numbers above
- Minimal comment/README economic section only if needed for consistency

**Out of scope for Phase 1**

- Linking RandomX/Verthash/Yespower libraries
- Final genesis nonces/hashes
- Full DigiByte → EGA string/binary rename
- Explorer, pool, mobile wallet

**Phase 1 done when**

- Constants match this spec
- Subsidy at heights 0, 209999, 210000, 420000 matches Bitcoin-style schedule for 50k start
- `MoneyRange` / `MAX_MONEY` consistent with 21B × 1e8
- Project still builds (or known build gaps documented if pre-existing)

---

## 7. Workspace and hygiene

- Prefer **new clean folders** for EGA product docs: `docs/ega/`.
- Third-party PoW sources may later live under something like `src/crypto/` or `third_party/` when integrated.
- Do not assume git remotes are EGA upstream; commit only when the maintainer requests.
- Avoid drive-by refactors unrelated to the current phase.

---

## 8. Testing expectations

| Phase | Tests |
|-------|--------|
| 1 | Manual or unit checks for subsidy and money constants; `make` as available |
| 3 | PoW self-tests / known vectors per algo if provided by upstream libs |
| 4 | Fresh datadir start, reindex, restart agree on genesis |
| 6 | Functional tests for subsidy, algo activation, basic multi-algo mining |

---

## 9. Non-goals (near term)

- Masternodes, PoS hybrid, DAG
- ASIC-friendly algos “for hashrate marketing”
- Premine or hidden allocations
- Claiming farms are impossible

---

## 10. Decision log

| Decision | Choice |
|----------|--------|
| Max supply | 21 billion EGA |
| Decimals | 8 (`int64`-safe) |
| Emission | Bitcoin-style scaled (50k / 210k halvings) |
| Block time | 60 seconds |
| PoW count | 3 from genesis |
| Algos | RandomX, Verthash, YespowerEGA |
| Difficulty | MultiShield V4-style from height 0 |
| Launch | Fair, 0 premine |
| Delivery order | Foundation layers (this doc §6) |

---

## 11. Open items

**Resolved in Phase 2–3:** magic/ports, YespowerEGA params, RandomX light + seed, Verthash 256 MiB EGA dataset, MultiShield V4-only.

**Still open (Phase 4+):**

- Final genesis timestamp / nonce / bits under real PoW hashes  
- Optional RandomX full-dataset mining path  
- Whether regtest uses reduced Verthash dataset for CI speed  
- Full binary rebrand (`egad`)

---

*End of design spec.*
