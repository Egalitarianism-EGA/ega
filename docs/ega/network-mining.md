# Multi-miner network (same chain)

On a normal cryptocurrency network, miners do **not** need a pool to “mine the same blockchain.”  
They need to be **peers** (or both connected to peers) so they share the **same block tip**.

```
[ Miner A: egad + CPU ] ----P2P 20201---- [ Miner B: egad + GPU ]
         \                                      /
          \--------- same chain history -------/
```

Whoever finds the next valid block first gets **that** block’s reward.  
Everyone else builds on top of it. That is standard PoW.

## Pool vs network

| | Network peers | Mining pool |
|--|---------------|-------------|
| Same chain? | Yes | Yes |
| Share **rewards**? | No (winner takes block) | Yes (split by work) |
| Needed for launch? | **Yes** (at least 2 nodes) | Optional |

## Setup: two people, one chain

### Person A (seed)

1. Install Core, start `egad`.
2. Note public IP or Tailscale IP.
3. Firewall: allow **TCP 20201** (or Tailscale only).
4. Mine if you want: `bash scripts/easy-mine.sh randomx`

### Person B

1. Same install.
2. In `~/.ega/ega.conf`:

```
addnode=PERSON_A_IP:20201
```

3. Start node, wait until `getblockcount` matches A (or catches up).
4. Mine with any algo — still the **same** coin and history.

### One PC demo

```bash
bash scripts/two-node-mining-demo.sh
```

Spins two regtest nodes, connects them, mines on both (RandomX + YespowerEGA), checks shared tip.

## GPU + CPU on same network

- CPU operators: RandomX / YespowerEGA / Scrypt via CLI or Miner app.  
- GPU operators: VerthashMiner → GBT on their own `egad` (or later a pool).  
- All `egad` instances with `addnode` to each other form **one** Egalitarianism network.

## Pool (shared rewards) later

When you want “we all mine together and split coins,” deploy Miningcore using  
https://github.com/Egalitarianism-EGA/ega-miningcore  

Until then, multi-node **solo** is a real multi-miner network.
