# Phase 3 — Triple PoW + MultiShield

**Status:** Implemented (2026-07-12)  
**Spec:** `docs/ega/design.md` §3–4  

## Delivered

| Algo | Implementation | Notes |
|------|----------------|-------|
| **RandomX** | tevador RandomX (vendored `src/crypto/randomx/`), light VM | Seed epoch = `nTime / (2048*60)`; tag `EGA-RandomX`. Light mode (no 2 GB dataset) for verify/mine on low RAM. |
| **Verthash** | Vertcoin-style `verthash_hash` + tiny_sha3 | EGA dataset 256 MiB expanded from `EGA-Verthash-v1` (not Vertcoin’s 1 GB `verthash.dat`). Same seeking algorithm. |
| **YespowerEGA** | openwall yespower 1.0 | `N=2048`, `r=32` (~256 KiB), personalization `"YespowerEGA"`. |

## Wiring

- `src/crypto/ega_pow.{h,cpp}` — dispatch
- `CBlockHeader::GetPoWAlgoHash` → `EgaGetPoWHash`
- `NUM_ALGOS = 3`, version bits for all three
- `IsAlgoActive` — all three from genesis
- `GetNextWorkRequired` — **V4 MultiShield only** (no DGB ladder)
- Build: yespower + verthash in `libdigibyte_consensus.a`; RandomX static lib via cmake

## Build notes

```bash
# RandomX is built automatically as EXTRA_* dependency:
# src/crypto/randomx/build/librandomx.a
make -C src digibyted
```

Requires `cmake` for RandomX.

## Still Phase 4

- Mine genesis under **real** PoW hashes (not `GetHash` placeholder searcher)
- Pin hashGenesisBlock / merkle / nBits for production difficulty
- Optional: RandomX full dataset mode for high-end miners
