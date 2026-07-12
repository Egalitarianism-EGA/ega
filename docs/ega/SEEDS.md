# Seed nodes & public services

## Published (operator PC — early network)

| Service | Endpoint | Notes |
|---------|----------|-------|
| P2P seed | `105.225.100.58:20201` | `addnode=105.225.100.58:20201` |
| Explorer | `http://105.225.100.58:8088/` | Forward TCP **8088** |
| Pool Verthash | `stratum+tcp://105.225.100.58:3334` | GPU; Miningcore share-verify |
| Pool Scrypt | `stratum+tcp://105.225.100.58:3336` | Miningcore share-verify |
| Pool API | `http://105.225.100.58:4000/api/pools` | Forward TCP **4000** if public |

RandomX / YespowerEGA: **solo** on the node (not stock Miningcore).

## Port-forward checklist

| Port | Service |
|------|---------|
| 20201 | P2P |
| 8088 | Explorer |
| 3334 | Verthash stratum |
| 3336 | Scrypt stratum |
| 4000 | Pool API (optional) |
| **20202** | RPC — **do not** expose |

## Operator start

```bash
bash scripts/easy-start.sh
bash scripts/ega-explorer.sh          # or EGA_EXPLORER_HOST=0.0.0.0
bash scripts/start-miningcore.sh
bash scripts/start-gpu-verthash.sh    # RTX Verthash 24/7
```
