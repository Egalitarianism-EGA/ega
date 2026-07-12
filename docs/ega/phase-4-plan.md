# Phase 4 — Genesis freeze

**Status:** Implemented (MultiShield-4)  
**Tool:** `src/ega_mine_genesis` (rebuild with `make -C src ega_mine_genesis`)  
**Canonical values:** also in `docs/ega/params.md` and `src/chainparams.cpp` asserts.

## Frozen genesis (RandomX coinbase header, 0 premine)

| Network | time | nonce | nBits | nVersion | hashGenesisBlock |
|---------|------|-------|-------|----------|------------------|
| **main** | 1751846400 | 2816 | `0x1f0fffff` | 2 (RandomX) | `943c83429a935b34fb988508440ec8702d217525865f3eea7076d64b4592eda5` |
| **test** | 1751846401 | 2722 | `0x1f0fffff` | 2 | `acd68ceeba9e198a8f6c7a62afa5c41b96560290fa2c7cc318d678edc401a195` |
| **regtest** | 1751846402 | 2 | `0x207fffff` | 2 | `beeed73f369163a394f73c5d69c368cc3d01b07ad0f0af42b9cb8ec429cf3a71` |

> **Note:** test/regtest genesis were re-mined for MultiShield-4 coinbase text. Main genesis hash is unchanged from the original fair-launch freeze.

### Coinbase messages

- main: `EGA fair launch: equality of opportunity, not outcome — anyone may mine.`
- test: `EGA testnet: MultiShield-4 RandomX Verthash YespowerEGA Scrypt`
- regtest: `EGA regtest MultiShield-4`

### Merkle roots

- main: `e30d15a8674c033ae2e00393f849b1d1bed85970b2aa7a5c6b843722020ddf01`
- test: `ee22876ee16319fa6d5eb6fecbac21035cd1ec9f8f676746b7e21c3989e6038b`
- regtest: `9086eeaa14ec3861f3e5fb4d6b37e7ab3dc2b7015eb12341da43cdaeb574460f`

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
make -C src egad ega-cli
datadir=$(mktemp -d)
./src/egad -regtest -datadir="$datadir" -daemon
./src/ega-cli -regtest -datadir="$datadir" getblockhash 0
# expect beeed73f369163a394f73c5d69c368cc3d01b07ad0f0af42b9cb8ec429cf3a71
./src/ega-cli -regtest -datadir="$datadir" stop
```
