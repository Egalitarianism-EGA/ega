# Multi-algo security notes (honest)

External critique (paraphrased):

> Multi-algo only helps against 51% if each door is expensive. RandomX is botnet-friendly; cheap algos make botfarms easy. DigiByte mixes expensive SHA-256/scrypt with GPU algos. Verthash alone is fine, but paired with cheap CPU work the chain is easy to dominate. KawPow would raise the cost of GPU capture.

## What they got right

1. **MultiShield is not magic.** It balances *share of blocks* across algos. If one algo’s hashrate is tiny in *economic* terms, attackers still abuse the cheap doors.
2. **RandomX** is efficient on CPUs and phones — great for “anyone can mine,” bad for botnet resistance (this is a known trade-off, same class as early Monero-before-RandomX debates, but RandomX itself is still CPU-farmable at scale).
3. **YespowerEGA** is deliberately cheap/low-RAM — maximizes inclusion, minimizes cost to attack that slice.
4. **Low early difficulty** (powLimit) means until real hashrate arrives, *any* algo is cheap. Explorer will show that.
5. **DigiByte’s mix** (SHA-256 + scrypt + GPU set) forces more diverse capital than three light-ish consumer algos.

## What the vision was optimizing for

- No premine, no ICO
- Phones / Pi / old PCs / consumer GPUs can participate
- Avoid single ASIC monoculture on day one

That vision **conflicts** with “make mining as expensive as BTC/KAWPOW.” You cannot fully have both.

## Options if we take the critique seriously

Chain is still tiny — a clean reset + param change is still possible before a public community locks genesis.

| Option | Effect | Cost |
|--------|--------|------|
| **A. Keep current set, raise min difficulty** | Harder spam until real hashrate | Soft; still botnet-friendly long-term |
| **B. Drop YespowerEGA** | Removes easiest botnet door | Loses “old phone” path |
| **C. Replace RandomX with heavier CPU or remove it** | Fewer botnets | Less “laptop mine” story |
| **D. Replace Verthash with KawPow (or similar)** | Costlier GPU farm | Breaks current Verthash miner path; bigger code change |
| **E. Hybrid: KawPow + one CPU (RandomX or yespower) only** | Closer to “two expensive doors” | Smaller multi-algo set |
| **F. DigiByte-like expensive mix** | Strongest 51% story | Needs SHA-256/scrypt (or similar) support + farms |

## Recommendation for launch honesty

- Treat multi-algo as **participation + gradual balance**, not “un-51%-able.”
- Publish **per-algo difficulty and hashrate on the explorer** so nobody is fooled by vanity hashrate.
- If security > inclusion: plan a **pre-community hard fork** of the algo set (KawPow + one hard CPU, or DGB-style expensive mix) and reset the young chain.
- If inclusion > security: keep the set, accept botnet risk, push for many independent nodes and social monitoring.

## Not changing in this doc

Consensus params stay frozen unless the project explicitly chooses a reset/fork. This file is decision support, not a silent consensus change.
