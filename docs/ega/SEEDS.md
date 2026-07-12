# Seed nodes & public services

## Status (honest)

| Service | Status |
|---------|--------|
| Prebuilt node | **v0.2.0** on GitHub Releases |
| Your home node P2P | Port **20201** (must be reachable) |
| Public seed list | Operators publish IPs below as they go live |
| Public explorer | Tunnel or VPS → update website `explorer.html` |
| Public pool | **Not published** yet |

## Be a seed (operator)

1. Run MultiShield-4 build (`v0.2.0+`).
2. `egad` listening on **0.0.0.0:20201** (`listen=1`).
3. Open **TCP 20201** on router/firewall (RPC **20202** stays localhost).
4. Share: `addnode=YOUR_PUBLIC_IP:20201`
5. Optional: keep a local explorer up and tunnel it (see `scripts/start-public-explorer.sh`).

```bash
# ~/.ega/ega.conf essentials
server=1
listen=1
txindex=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
# do NOT expose RPC to the internet
```

## Join a seed (peer)

```bash
# ega.conf or CLI
addnode=SEED_IP:20201
```

Or:

```bash
ega-cli addnode SEED_IP:20201 add
ega-cli getpeerinfo
```

## Published seeds

| Host | Port | Notes |
|------|------|-------|
| `105.225.100.58` | 20201 | Operator home node (early; confirm router port-forward) |
| Explorer tunnel | HTTPS | `https://deposit-represented-seem-wrestling.trycloudflare.com` (ephemeral quick tunnel) |

When you publish one, also update:

- this table  
- website home / explorer pages  
- `share/examples/ega.conf` `#addnode=` comment  

## Security

- Never put `rpcuser` / `rpcpassword` on a public page.
- Do not open **20202** to the world.
- Prefer Tailscale/VPN between friends if you do not want a public IP.
