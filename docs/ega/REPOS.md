# Egalitarianism (EGA) — GitHub organization map

**Org:** [Egalitarianism-EGA](https://github.com/Egalitarianism-EGA)  
**Full project name:** Egalitarianism · **Ticker:** EGA  

## Do you need a separate wallet repo?

**Full-node wallet is already in Core** (`egad` + `ega-cli` + `ega-qt`).  
A separate **ega-wallet** repo is the **hub/docs** for wallets + future light/mobile wallets — not a second competing full node.

| Need | Where it lives |
|------|----------------|
| Store keys, send/receive, mine to self | **ega** (Core) |
| GUI desktop | **ega** → `ega-qt` |
| Light/mobile later | **ega-wallet** (roadmap) |
| Mine RandomX / Yespower | **ega** (built-in) + **ega-miners** docs |
| Mine Verthash on GPU | **ega-verthash-miner** |
| Public pool | **ega-miningcore** configs + you run Miningcore |
| Explorer | **ega-blockbook** config + you run Blockbook |
| One-PC live setup | **ega-homelab** |
| Landing page | **ega-website** (GitHub Pages) |

## Complete repo list

| Repo | URL | Purpose | Launch critical? |
|------|-----|---------|------------------|
| **ega** | https://github.com/Egalitarianism-EGA/ega | Full node, consensus, RPC wallet, GUI | **Yes** |
| **ega-wallet** | https://github.com/Egalitarianism-EGA/ega-wallet | Wallet docs + future light wallets | Docs yes; light later |
| **ega-miners** | https://github.com/Egalitarianism-EGA/ega-miners | Mining hub for all 3 algos | **Yes** (docs) |
| **ega-verthash-miner** | https://github.com/Egalitarianism-EGA/ega-verthash-miner | GPU Verthash guide + dataset | **Yes** for GPU |
| **ega-miningcore** | https://github.com/Egalitarianism-EGA/ega-miningcore | Pool coin profiles | No (after solo) |
| **ega-blockbook** | https://github.com/Egalitarianism-EGA/ega-blockbook | Explorer coin def | No (after peers) |
| **ega-homelab** | https://github.com/Egalitarianism-EGA/ega-homelab | One-PC live scripts | Recommended |
| **ega-website** | https://github.com/Egalitarianism-EGA/ega-website | Static landing / Pages | Nice to have |

## Systematic order (together)

1. ~~Core chain + mining~~  
2. ~~Org repos map + wallet/miners hubs~~  
3. CI green + 24/7 node on your PC  
4. Website Pages on  
5. Friends `addnode`  
6. Optional explorer / pool when needed  

## What is *not* a separate product yet

- Standalone Electrum-EGA light wallet binary  
- Mobile app store wallets  
- Fully patched multi-algo Miningcore daemon (configs only; may need pool software patches)  

Those are **roadmap**, not launch blockers if everyone uses Core full-node wallet + solo/GPU mining.
