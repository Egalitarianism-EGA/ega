#!/usr/bin/env bash
# Cross-compile EGA Core for Windows (daemon+cli, no GUI) from Linux.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
HOST=x86_64-w64-mingw32
echo "== depends ($HOST) =="
make -C depends HOST=$HOST -j"$(nproc)"
echo "== configure =="
./autogen.sh
CONFIG_SITE="$ROOT/depends/$HOST/share/config.site" \
  ./configure --prefix=/ --without-gui --disable-tests --disable-bench
echo "== make =="
make -j"$(nproc)"
echo "Look for .exe under src/ (names may still be digibyte* until renamed)"
find src -name '*.exe' 2>/dev/null | head
