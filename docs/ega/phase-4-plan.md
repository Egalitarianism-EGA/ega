# Phase 4 — Genesis freeze

**Status:** Implemented (2026-07-12)  
**Tool:** `src/ega_mine_genesis` (rebuild with `make -C src ega_mine_genesis`)

## Frozen genesis (RandomX, 0 premine)

| Network | time | nonce | nBits | nVersion | hashGenesisBlock |
|---------|------|-------|-------|----------|------------------|
| **main** | 1751846400 | 2816 | `0x1f0fffff` | 2 (RandomX) | `943c83429a935b34fb988508440ec8702d217525865f3eea7076d64b4592eda5` |
| **test** | 1751846401 | 2551 | `0x1f0fffff` | 2 | `86ec8743951d8dcfcc7c6aad05c8a4365108f96075bf4c995dfbca98ffde1c98` |
| **regtest** | 1751846402 | 0 | `0x207fffff` | 2 | `7db0bcedfac1596d0be2a5b42c4b88043c207f8f29bac2796fba10ea06ae5ac0` |

### Coinbase messages

- main: `EGA fair launch: equality of opportunity, not outcome — anyone may mine.`
- test: `EGA testnet: RandomX + Verthash + YespowerEGA MultiShield`
- regtest: `EGA regtest`

### Merkle roots

- main: `e30d15a8674c033ae2e00393f849b1d1bed85970b2aa7a5c6b843722020ddf01`
- test: `6b33d07186b851c3a2e750d2c2d9846be06bfdc18df4cf827d742b0d9c129501`
- regtest: `492e199b683b7b542713244df27840e94dee345d02ac62c21c79b82b334c02b8`

## Validation

On load, each network asserts:

1. `hashGenesisBlock` matches frozen value  
2. `hashMerkleRoot` matches  
3. `CheckProofOfWork(GetPoWAlgoHash(genesis), nBits, consensus)`  

No runtime nonce search remains.

## powLimit

Main/test: `~uint256(0) >> 12` (compact `0x1f0fffff`) — ~1/4096 at min difficulty for open fair launch; MultiShield adjusts from real hashrate.  
Regtest: max target (easy).

## Smoke test

```bash
make -C src digibyted digibyte-cli
datadir=$(mktemp -d)
./src/digibyted -regtest -datadir="$datadir" -daemon
./src/digibyte-cli -regtest -datadir="$datadir" getblockhash 0
# expect 7db0bcedfac1596d0be2a5b42c4b88043c207f8f29bac2796fba10ea06ae5ac0
./src/digibyte-cli -regtest -datadir="$datadir" stop
```
