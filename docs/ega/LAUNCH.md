# EGA Launch plan — node + mining ready

## Goal (this milestone)

Anyone can:

1. Build or install the node (Linux first; Windows path documented)
2. Start a node with `ega.conf`
3. Create an address (wallet)
4. Mine with **RandomX**, **Verthash**, or **YespowerEGA**
5. Connect to peers once seeds/IPs exist

## Ship now (MVP)

| Item | Status |
|------|--------|
| Consensus params + genesis | **Done** |
| Triple PoW + MultiShield | **Done** |
| Wallet Linux build (`--enable-wallet --with-incompatible-bdb`) | **Done** (verified) |
| Solo mine all 3 algos (`generatetoaddress`) | **Done** (regtest verified) |
| `getblocktemplate` solo without peers / IBD block | **Done** |
| Launch user guide | **Done** → [USER-GUIDE-LAUNCH.md](USER-GUIDE-LAUNCH.md) |
| Example conf + wrappers | **Done** |
| Linux build guide | **Done** |
| Windows build guide | Docs ready; release zip still roadmap |

## Roadmap (after MVP)

- Public DNS seeds / seed node list
- Pool software + stratum
- GUI wallet / installers
- macOS builds
- Full binary rename digibyted→egad in autotools
- Explorer
- RandomX full-dataset mode for high-end miners
- Clean dead DigiByte packaging paths

## Operator checklist (day of launch)

1. Publish this repo + `docs/ega/params.md` + genesis hashes  
2. Publish build instructions  
3. At least 1–2 seed IPs (`addnode=` in conf)  
4. Announce mining RPCs / algo names  
5. Freeze params (changing genesis = new coin)  
