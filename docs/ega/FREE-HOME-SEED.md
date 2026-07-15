# Free path: home PC as the public seed (no Oracle, no paid VPS)

You do **not** need a cloud credit card to run EGA.  
Your **home PC is the network** until friends join.

## What you already have (free)

| Piece | Status |
|--------|--------|
| Full node `egad` | Runs on your PC |
| MultiShield-4 + mining | Local (low-power or GPU) |
| Explorer | `http://127.0.0.1:8088` |
| Pool (VH + Scrypt) | Local Miningcore |
| Linux release | GitHub (free for others to download) |
| Website | GitHub Pages (free) |

## What “public network” means without money

1. **You** leave the PC on (or on a schedule).
2. Router **port-forwards TCP 20201** → your PC (free; only needs your router admin).
3. Friends download **v0.2.0** (or build) and put:
   ```
   addnode=YOUR_PUBLIC_IP:20201
   ```
4. Optional free HTTPS explorer: **Cloudflare quick tunnel** (no card for temporary URL).

That **is** a real peer-to-peer coin launch path. Almost every fair-launch started from someone’s home or a single VPS.

## Step 1 — Keep the node running

```bash
cd ~/ega   # or your clone path
src/egad -daemon
# or: bash scripts/easy-start.sh
```

Confirm:

```bash
src/ega-cli getblockcount
src/ega-cli getnetworkinfo   # listen should be active
```

In `~/.ega/ega.conf` you want:

```
server=1
listen=1
txindex=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
# optional if you know your public IP:
# externalip=YOUR.PUBLIC.IP
```

**Never** open RPC **20202** to the internet.

## Step 2 — Free “always on seed”: port-forward 20201

On your **router** (browser → usually `192.168.0.1` or `192.168.1.1`):

| Setting | Value |
|---------|--------|
| External port | **20201** |
| Internal IP | Your PC’s LAN IP (e.g. `192.168.0.97`) |
| Internal port | **20201** |
| Protocol | **TCP** |

Find LAN IP: `ip -4 addr` or `hostname -I`.

Find public IP: https://ifconfig.me  

Test from a phone on **mobile data** (not Wi‑Fi):

```text
# from another network, or ask a friend:
# nc -vz YOUR.PUBLIC.IP 20201
```

If that connects, you **are** a public seed.

Optional extras (only if you want outsiders to use them):

| Port | Service |
|------|---------|
| 8088 | Explorer (or use Cloudflare tunnel instead) |
| 3334 | Verthash pool |
| 3336 | Scrypt pool |

## Step 3 — Free public explorer URL (no card)

Cloudflare **quick tunnels** need no account for a temporary `*.trycloudflare.com` link:

```bash
# explorer must be running first
bash scripts/ega-explorer.sh   # or already on :8088

/tmp/cloudflared tunnel --url http://127.0.0.1:8088
# copy the https://….trycloudflare.com URL it prints
```

URL changes when the tunnel restarts. Good enough for friends; not a permanent domain.

## Step 4 — Second peer for free

Anyone with a spare laptop:

1. Download https://github.com/Egalitarianism-EGA/ega/releases/tag/v0.2.0  
2. Run node  
3. Config: `addnode=YOUR.PUBLIC.IP:20201`  
4. When both show `getconnectioncount` ≥ 1, you have a **network**

You + one friend = enough to prove multi-node tips.

## Step 5 — Mining without burning the PC

```bash
# gentle: 1 block every 10 minutes, all 4 algos rotate
bash scripts/low-power-mine.sh all 600
```

Or stop mining entirely and only run the **node** (seed still works; chain just grows when someone mines).

## What you skip (until you have money/card)

- Oracle / AWS / paid VPS  
- Fancy stable custom domain (optional later)  
- 24/7 GPU farm  

## Success checklist

- [ ] PC left on when you want the network live  
- [ ] `listen=1`, node running  
- [ ] Router: TCP **20201** → PC  
- [ ] Friend can `addnode` your public IP  
- [ ] `getconnectioncount` > 0  
- [ ] Optional: Cloudflare explorer link for browsers  

## Honest framing

**You are the bootstrap.** That’s normal.  
Publish: “Seed: `IP:20201` · Release: GitHub v0.2.0 · MultiShield-4.”  
When someone else runs a node for free on *their* home internet, capacity doubles — still $0.
