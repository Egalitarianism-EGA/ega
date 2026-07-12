# EGA frozen parameters (quick reference)

Source of truth for numbers: also see `design.md`. Update both together.

## Economy

| Key | Value |
|-----|--------|
| `MAX_SUPPLY_EGA` | `21000000000` |
| `DECIMALS` | `8` |
| `COIN` | `100000000` |
| `MAX_MONEY` | `21000000000 * COIN` |
| `INITIAL_SUBSIDY_EGA` | `50000` |
| `SUBSIDY_HALVING_INTERVAL` | `210000` |
| `BLOCK_TIME_SECONDS` | `60` |
| `GENESIS_REWARD` | `0` |

## Proof of work (MultiShield-4)

| Key | Value |
|-----|--------|
| `NUM_ALGOS` | `4` |
| `ALGO_0` | `RandomX` |
| `ALGO_1` | `Verthash` |
| `ALGO_2` | `YespowerEGA` |
| `ALGO_3` | `Scrypt` |
| Target share | ~**25% each** |
| `DIFFICULTY` | MultiShield-V4-style from height 0 |
| `MULTI_ALGO_TARGET_SPACING` | `240` (seconds, 4 × block time) |
| Reward | Same subsidy for every algo |

| Algo | Hardware | Role |
|------|----------|------|
| RandomX | Modern CPU / laptop | People CPU |
| Verthash | Consumer GPU | People GPU |
| YespowerEGA | Phone / Pi / weak CPU | Inclusion |
| Scrypt | ASIC / capital market | Security hard door |

## YespowerEGA

| Key | Value |
|-----|--------|
| `PERSONALIZATION` | `YespowerEGA` (11 bytes) |
| `version` | YESPOWER_1_0 |
| `N` | `2048` |
| `r` | `32` (~256 KiB working memory) |

## RandomX

| Key | Value |
|-----|--------|
| mode | light VM (no FULL_MEM dataset) |
| seed tag | `EGA-RandomX` |
| epoch | `nTime / (2048 * 60)` seconds |

## Verthash

| Key | Value |
|-----|--------|
| algorithm | Vertcoin-style memory seek (`verthash_hash`) |
| dataset size | 256 MiB |
| dataset tag | `EGA-Verthash-v1` (SHA256 expansion) |

## Scrypt

| Key | Value |
|-----|--------|
| function | `scrypt_1024_1_1_256` (Litecoin/DigiByte-compatible) |
| input | 80-byte block header |

## Network identity

| Network | Magic | P2P | RPC | bech32 HRP |
|---------|-------|-----|-----|------------|
| main | `e4 47 41 01` | 20201 | 20202 | `ega` |
| test | `e4 47 41 02` | 20203 | 20204 | `tega` |
| regtest | `e4 47 41 03` | 20205 | 20206 | `egart` |

| Key | main value |
|-----|------------|
| base58 pubkey version | `33` (leading `E`) |
| base58 script version | `92` |
| base58 secret version | `176` |
| main genesis hash | `943c83429a935b34fb988508440ec8702d217525865f3eea7076d64b4592eda5` |
| test genesis hash | `acd68ceeba9e198a8f6c7a62afa5c41b96560290fa2c7cc318d678edc401a195` |
| regtest genesis hash | `beeed73f369163a394f73c5d69c368cc3d01b07ad0f0af42b9cb8ec429cf3a71` |
| main nBits | `0x1f0fffff` |
| genesis algo | RandomX (`nVersion` = 2) |
| data directory | `~/.ega` |
| config / pid | `ega.conf` / `egad.pid` |

**Note:** Adding Scrypt is a consensus change. Wipe local chain data after upgrading (`scripts/reset-mainnet-datadir.sh`) before mining MultiShield-4 blocks.
