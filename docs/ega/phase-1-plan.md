# Phase 1 implementation plan — Economic foundation

**Status:** Implemented (2026-07-12)  
**Spec:** `docs/ega/design.md` §2, §6 Phase 1  
**Goal:** Freeze money, subsidy, 60s block time, and MultiShield spacing for **3** algos. No PoW libraries, no genesis freeze, no full rebrand.

## Checklist

1. **`src/amount.h`**
   - `COIN = 100000000` (8 decimals)
   - `CENT = 1000000`
   - `MAX_MONEY = 21000000000LL * COIN` (21 billion EGA)
   - Comments match EGA (not DigiByte 21B DGB / 12 decimals)

2. **`src/validation.cpp` — `GetBlockSubsidy`**
   - Start: `50000 * COIN`
   - Halvings: `nHeight / nSubsidyHalvingInterval`
   - Zero when `halvings >= 64`
   - No DigiByte multi-period reward curve

3. **`src/chainparams.cpp`** (main, test, regtest as applicable)
   - `nSubsidyHalvingInterval = 210000`
   - `nPowTargetSpacing` / `nTargetSpacing` / re-target spacings → **60**
   - `multiAlgoTargetSpacing` / `V4` → **180** (3 algos × 60s)
   - Recompute `nAveragingTargetTimespan*` from interval × multi spacing
   - Comments: 21B, 50k subsidy, triple algo + MultiShield intent
   - Genesis reward stays **0**; do not pin final genesis hashes

4. **`src/chainparamsbase.cpp`** if RPC/P2P default ports only — leave ports for Phase 2 unless already EGA; no drive-by renames

5. **`docs/ega/params.md`** — confirm values match code

6. **Sanity**
   - Mental/unit: subsidy(0)=50000*COIN, subsidy(210000)=25000*COIN, subsidy(420000)=12500*COIN
   - `MAX_MONEY` ≤ `INT64_MAX`
   - Avoid breaking unrelated WIP (algo enum names may already be RandomX/Verthash; Phase 1 may note third algo in comments only if block.h still has 2 — full 3-algo enum is Phase 3)

## Explicit non-goals

- RandomX / Verthash / Yespower library link
- `NUM_ALGOS = 3` enum if it requires full PoW switch (defer to Phase 3); spacing constants still assume 3
- Binary rename, README full rewrite (optional one-line economic sync only if trivial)

## Done criteria

- Code matches `docs/ega/params.md`
- No 12-decimal or 210M-supply leftovers in amount/subsidy path
- Build still configures; note pre-existing build issues separately
