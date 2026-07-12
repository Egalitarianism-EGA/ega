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

## Proof of work

| Key | Value |
|-----|--------|
| `NUM_ALGOS` | `3` |
| `ALGO_0` | `RandomX` |
| `ALGO_1` | `Verthash` |
| `ALGO_2` | `YespowerEGA` |
| `DIFFICULTY` | `MultiShield-V4-style from height 0` |
| `MULTI_ALGO_TARGET_SPACING` | `180` (seconds, 3 × block time) |

## YespowerEGA (Phase 3 lock)

| Key | Value |
|-----|--------|
| `PERSONALIZATION` | `YespowerEGA` (11 bytes) |
| `version` | YESPOWER_1_0 |
| `N` | `2048` |
| `r` | `32` (~256 KiB working memory) |

## RandomX (Phase 3)

| Key | Value |
|-----|--------|
| mode | light VM (no FULL_MEM dataset) |
| seed tag | `EGA-RandomX` |
| epoch | `nTime / (2048 * 60)` seconds |

## Verthash (Phase 3)

| Key | Value |
|-----|--------|
| algorithm | Vertcoin-style memory seek (`verthash_hash`) |
| dataset size | 256 MiB |
| dataset tag | `EGA-Verthash-v1` (SHA256 expansion) |

## Network identity (Phase 2)

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
| DNS / fixed seeds | empty until community adds |
| checkpoints | genesis only (Phase 4) |
| assumevalid / min chain work | `0x00` |
| main genesis hash | `943c83429a935b34fb988508440ec8702d217525865f3eea7076d64b4592eda5` |
| main nBits | `0x1f0fffff` (`powLimit` = `~0 >> 12`) |
| genesis algo | RandomX (`nVersion` = 2) |
| data directory | `~/.ega` |
| config / pid | `ega.conf` / `egad.pid` |
| wrappers | `contrib/ega/egad`, `ega-cli`, `ega-tx` → digibyte* binaries |
