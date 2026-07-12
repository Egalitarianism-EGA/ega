# Phase 5 — Product surface / rebrand polish

**Status:** Implemented (2026-07-12)

## Done

| Item | Detail |
|------|--------|
| Data dir | `~/.ega` (Win: `%APPDATA%\EGA`, Mac: `~/Library/Application Support/EGA`) |
| Config / PID | `ega.conf` / `egad.pid` |
| Thread names | `ega-*` |
| CLIENT_NAME | already `EGA` |
| configure.ac | package **EGA Core**, copyright holders EGA Core, year 2026 |
| Example conf | `share/examples/ega.conf` |
| Wrappers | `contrib/ega/{egad,ega-cli,ega-tx}` |
| README / INSTALL | Aligned with frozen params; DigiByte 5-algo/15s marketing removed |

## Intentionally deferred

- Renaming every autotools target from `digibyted` → `egad` (large Makefile/CI churn). Wrappers cover UX for now.
- Full Qt string/icon rebrand
- Wallet default-on in configure (still optional via `--enable-wallet` when BDB available)

## Next (Phase 6)

Functional tests for subsidy, multi-algo mining smoke, CI notes.
