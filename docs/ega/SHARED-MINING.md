# Shared mining — plain English

## Three different ideas people mix up

### 1) Solo mining (easiest)
- You run a node and mine.
- When **you** find a block, **you** get the 50,000 EGA (minus maturity wait).
- Scripts: `scripts/easy-mine.sh randomx (also yespower-ega, scrypt)`

### 2) Shared **network** (still solo rewards)
- Friends run nodes and connect to you (`addnode=`).
- Everyone can mine.
- Each person keeps **their own** blocks.
- This is how a fair launch starts with multiple people.

### 3) Shared **rewards** = mining **pool**
- Many people send work to **one pool server**.
- When *anyone* finds a block, the pool **splits** coins by work contributed.
- Needs Miningcore (or similar) + configs from **ega-miningcore**.
- Harder; do **after** solo works.

---

## What to do at launch

| Goal | Do |
|------|-----|
| Just me testing | Solo scripts |
| Me + friends | Each solo + `addnode` to your seed |
| Public hashrate / mobile farm | Run a pool later |

---

## Friend connects to your PC

**On your PC:** leave `egad` running, port **20201** reachable  
(or use free **Tailscale** — no router config).

**On friend PC:** in `~/.ega/ega.conf`:

```
addnode=YOUR_IP:20201
```

They install with `scripts/easy-install-linux.sh` same as you.

---

## CPU “shared” without a pool

There is no magic “share my CPU hashrate into one wallet” without either:

- mining **to the same address** (trust), or  
- a **pool**.

If a group trusts one address:

```bash
# everyone uses the SAME address
ega-cli generatetoaddress 1 SHARED_ADDRESS 10000000 randomx (also yespower-ega, scrypt)
```

Then someone has to split coins manually — fragile. Prefer solo or a real pool.
