# Miningcore: shared mining for all 4 EGA algos

## Goal
Users can **solo or shared-mine** every MultiShield-4 algorithm.

## Current

| Algo | Stratum | Share verify |
|------|---------|--------------|
| Verthash | `:3334` | Yes (stock Miningcore + EGA dataset) |
| Scrypt | `:3336` | Yes (stock scrypt hasher) |
| RandomX | — | Solo only — needs custom work |
| YespowerEGA | — | Solo only — needs custom work |

## Why stock Miningcore is not enough for RX / YP

EGA uses **Bitcoin-family block headers** with **algo version bits** and:

```
getblocktemplate … "algo": "randomx" | "yespower-ega" | "verthash" | "scrypt"
```

Miningcore’s **RandomX** path is **Cryptonote/Monero**-oriented (blob/seed hash), not EGA’s multi-algo Bitcoin header + `pow_algo` version field.

**YespowerEGA** (N=2048, r=32) is not a stock Bitcoin header hasher in Miningcore’s algorithm list (unlike Scrypt/Verthash).

## Engineering plan (fork Miningcore)

### 1. Coin definitions
- `ega-randomx` — `blockTemplateRpcExtraParams: ["randomx"]`, custom header hash hook  
- `ega-yespower` — `blockTemplateRpcExtraParams: ["yespower-ega"]`, custom hasher  

### 2. Job manager
- Call node RPC `getblocktemplate` with EGA algo argument  
- Build stratum notify from Bitcoin-family template (nVersion includes algo bits)  
- Extra nonce / coinbase like other Bitcoin pools  

### 3. Share verification
- **RandomX:** use same params as `src/crypto/ega_pow.cpp` / RandomX light  
- **YespowerEGA:** call Yespower with EGA N,r (or link to EGA consensus library)  
- Compare hash to share target; on block solution, `submitblock`  

### 4. Ports (reserved)
| Algo | Port |
|------|------|
| RandomX | 3333 |
| Verthash | 3334 |
| YespowerEGA | 3335 |
| Scrypt | 3336 |

### 5. UI
Pool dashboard already lists four networks; flip RX/YP from “solo” to “shared” when stratum is live.

### 6. Acceptance tests
- Miner submits shares → accepted  
- Forced low diff finds block → appears on chain with correct `pow_algo`  
- Explorer shows reward address  

## Interim (accessibility without shared RX/YP)

- Solo: `easy-mine.sh` / low-power-mine  
- Shared: Verthash GPU + Scrypt  
- Document clearly on Start page  

## Effort estimate

Non-trivial C#/native work: **days to weeks** for a solid fork, not a config-only afternoon.  
This is **required for mission completion**, tracked in `ACCESSIBILITY-ROADMAP.md` Phase B.
