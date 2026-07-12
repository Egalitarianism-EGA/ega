# Phase 2 — Network identity

**Status:** Implemented (2026-07-12)  
**Spec:** `docs/ega/design.md` §5  

## Goals

1. Unique magic bytes per network (no DigiByte collision)
2. Stable EGA P2P/RPC port map
3. No DigiByte DNS/fixed seeds
4. No DigiByte checkpoints / assumevalid / chainTx stats
5. Distinct address encoding (base58 + bech32) so funds are not confused with DGB
6. Soft-fork bits usable on a fresh chain (ALWAYS_ACTIVE where needed)

## Port map (frozen)

| Network | P2P | RPC |
|---------|-----|-----|
| main | 20201 | 20202 |
| test | 20203 | 20204 |
| regtest | 20205 | 20206 |

## Magic

| Network | Bytes |
|---------|--------|
| main | `e4 47 41 01` |
| test | `e4 47 41 02` |
| regtest | `e4 47 41 03` |

## Out of scope

- PoW libraries / YespowerEGA
- Final genesis mine
- Binary rename (`egad`)
