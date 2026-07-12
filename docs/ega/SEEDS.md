# Seed nodes & public services

## Home operator (early)

| Service | Endpoint | Notes |
|---------|----------|-------|
| P2P | `105.225.100.58:20201` | Home PC — port-forward if public |
| Explorer | `http://105.225.100.58:8088/` | TCP **8088** |
| Pool Verthash | `stratum+tcp://105.225.100.58:3334` | GPU share-verify |
| Pool Scrypt | `stratum+tcp://105.225.100.58:3336` | share-verify |
| Pool API | `http://105.225.100.58:4000/api/pools` | optional |

**RandomX / YespowerEGA:** solo only (`easy-mine` / `low-power-mine`) — not stock Miningcore.

## Oracle Ampere A1 (ARM) — recommended always-on seed

See full guide: **[ORACLE-ARM-SEED.md](./ORACLE-ARM-SEED.md)**

| Item | Value |
|------|--------|
| Shape | VM.Standard.A1.Flex, 2 OCPU / 8–12 GB, aarch64 |
| Role | Public `egad` seed only (not heavy mining) |
| Build | Native on Ubuntu ARM (`./configure && make`) |
| Port | **TCP 20201** ingress |
| `addnode` | `ORACLE_PUBLIC_IP:20201` (fill in when live) |

| Host | Port | Notes |
|------|------|-------|
| *(add after you create the VM)* | 20201 | Always Free Ampere A1 |

## Port-forward checklist (home)

| Port | Service |
|------|---------|
| 20201 | P2P |
| 8088 | Explorer |
| 3334 / 3336 | Pool VH / Scrypt |
| 4000 | Pool API optional |
| **20202** | **Never** public |

## Low-power home mining (all 4, gentle)

```bash
# ~1 block every 10 minutes, rotates RX → YP → Scrypt → Verthash (CPU path)
bash scripts/low-power-mine.sh all 600
# log: /tmp/ega-low-power-mine.log
# stop: kill $(cat /tmp/ega-low-power-mine.pid)
```

GPU Verthash when you want hashrate: `bash scripts/start-gpu-verthash.sh` (heavier).
