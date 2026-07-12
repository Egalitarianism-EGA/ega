# Egalitarianism (EGA) — for normal people

No jargon first. **Egalitarianism** is digital money you can help secure by **running a program** and optionally **mining**.

---

## Three things you can do

| I want to… | Do this |
|------------|---------|
| **Use a wallet** (addresses, balance) | Run the node + use GUI or simple commands |
| **Mine** (create new coins for myself) | One command or GPU app |
| **Help the network** | Leave the node running |

You do **not** need a pool, explorer, or VPS to start.

---

## Super simple (Linux)

### 1) Install once

```bash
cd ~
git clone https://github.com/Egalitarianism-EGA/ega.git
cd ega
bash scripts/easy-install-linux.sh
```

Wait until it finishes. Coffee is allowed.

### 2) Start the node

```bash
bash scripts/easy-start.sh
```

### 3) Get an address (wallet)

```bash
bash scripts/easy-wallet.sh
```

Copy the address somewhere safe. **Back up** when the script tells you.

### 4) Mine (CPU — easiest)

```bash
# RandomX (good modern CPU)
bash scripts/easy-mine.sh randomx

# Yespower (also fine on weaker CPUs)
bash scripts/easy-mine.sh yespower-ega
```

### 5) Mine (GPU — Verthash)

Follow: https://github.com/Egalitarianism-EGA/ega-verthash-miner  
(Uses your graphics card. A bit more steps.)

### 6) Desktop app (optional)

If you built with GUI:

```bash
./src/qt/ega-qt
```

Otherwise stick to the scripts + `ega-cli`.

---

## Shared mining — what does that mean?

| Mode | What happens | Hard? |
|------|----------------|-------|
| **Solo** | You mine alone; **you** get the block reward | Easy — use our scripts |
| **Shared network** | Friends run nodes connected to you; each still mines solo | Easy — `addnode` |
| **Pool (true shared rewards)** | Many miners share luck; payouts split | Harder — needs pool software |

For launch: **solo is fine.**  
“Shared mining” as people usually mean it = **pool** (later).

To connect a friend to **your** node:

```
# in their ~/.ega/ega.conf
addnode=YOUR_IP_OR_TAILSCALE_IP:20201
```

---

## Don’t do this

- Don’t share your `rpcpassword` or wallet backup.  
- Don’t open port **20202** (RPC) to the whole internet.  
- Don’t change genesis / money rules after others join.

---

## Help links

- Full operator guide: [USER-GUIDE-LAUNCH.md](USER-GUIDE-LAUNCH.md)  
- All GitHub repos: [REPOS.md](REPOS.md)  
- Status: [STATUS-AND-ROADMAP.md](STATUS-AND-ROADMAP.md)  
- Website: https://egalitarianism-ega.github.io/ega-website/  
