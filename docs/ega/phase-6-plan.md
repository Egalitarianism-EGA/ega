# Phase 6 — Tests & hardening

**Status:** Implemented (2026-07-12)

## Tests

| Suite | File | What |
|-------|------|------|
| Subsidy + money | `src/test/main_tests.cpp` | 50k/210k schedule, ~21B sum, COIN/MAX_MONEY, ports/spacing |
| Amount | `src/test/amount_tests.cpp` | 8 decimals, MAX_MONEY range |
| PoW | `src/test/ega_pow_tests.cpp` | algo names, distinct hashes, main genesis PoW valid |
| Smoke | `docs/ega/smoke-regtest.sh` | regtest genesis + 3 algos in RPC |

```bash
make -C src check
# or
./src/test/test_digibyte -t main_tests -t ega_pow_tests -t amount_tests
./docs/ega/smoke-regtest.sh
```

## Platforms

| OS | Status |
|----|--------|
| **Linux** | Primary — [build-linux.md](build-linux.md) |
| **Windows** | Supported path — [build-windows.md](build-windows.md) (mingw cross or MSYS2) |
| **macOS** | Deferred (toolchain/SDK pain); not blocked for Linux/Windows |

## Hardening notes

- Unit tests link `LIBRANDOMX` (same as daemon).
- Genesis and money constants covered by asserts + Boost tests.
- Full multi-algo *mining* functional test (mine 1 block per algo) needs wallet/`generatetoaddress` + runtime; smoke covers RPC surface of difficulties for now.
