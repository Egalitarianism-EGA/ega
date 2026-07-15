# What is left vs what is done (honest, 2026-07-15)

## Done (real)

| Area | Status |
|------|--------|
| MultiShield-4 consensus (4 algos) | Done |
| Node `egad` / `ega-cli` / Linux release v0.2.0 | Done |
| Qt wallet binary on operator Linux | Built (`ega-qt`) |
| Home seed + port forward docs | Done |
| Explorer (blocks, tx, rewards, address) | Done |
| Web wallet UI + server (:8090) | Done |
| Pool UI Solo/Shared/Start/Blocks/Wallet (:8089) | Done (improving) |
| Shared stratum all 4 ports 3333–3336 | Live on operator |
| Android Termux light node guide | Done |
| Website pages | Live on GitHub Pages |
| Miningcore VH + Scrypt | Live |

## Still a boatload (must do for “like real coins”)

### Pool product (HeroMiners-level)
- [x] Workers + payments pages on pool UI (basic)
- [ ] Richer PPLNS charts / multi-region
- [ ] Charts (your earnings / pool HR over time)
- [ ] Multi-region hosts (later)
- [ ] Stable domain (not raw IP)
- [ ] Mobile-optimized pool CSS polish
- [ ] Harden ega-algo-stratum (payouts, merkle edge cases, more miner clients)

### Network
- [ ] `getconnectioncount` > 0 (phone or friend online)
- [ ] Second public seed IP
- [ ] DNS seeds (later)

### Downloads
- [ ] Always ship `ega-qt` in every Linux release (when built on CI)
- [x] CI workflow for linux-aarch64 (manual/dispatch; needs ARM runner)
- [ ] Publish aarch64 tarball to Releases when CI green
- [ ] **Windows** egad/ega-cli/ega-qt zip
- [ ] Signed checksums

### Mobile apps
- [x] Web wallet PWA installable in browser
- [ ] Native Android APK (optional later)
- [ ] In-app miner for Yespower
- [ ] Push notifications (optional)

### Wallet
- [ ] Web wallet CORS/proxy hardened for remote use
- [ ] Seed phrase / HD backup UX in Qt
- [ ] Light server (Electrum-style) so phones don’t need full node

### Ops
- [ ] systemd units for pool, explorer, wallet, stratum
- [ ] Auto-restart, logrotate
- [ ] Monitoring if seed dies

### Quality
- [ ] CI green always
- [ ] Full DigiByte string cleanup
- [ ] Security review before “mainnet marketing”

## Priority order

1. Get **one peer** (Android node or friend)  
2. Keep improving **pool UI** toward HeroMiners  
3. **aarch64** binary release  
4. **Windows** release  
5. Light server + nicer Android app  
