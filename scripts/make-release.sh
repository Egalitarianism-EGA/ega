#!/usr/bin/env bash
# Package prebuilt Linux binaries for GitHub Releases
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VER="${1:-$(git describe --tags --always 2>/dev/null || echo dev)}"
VER="${VER#v}"
ARCH="$(uname -m)"
NAME="ega-${VER}-linux-${ARCH}"
OUT="${RELEASE_DIR:-/tmp}/${NAME}"
rm -rf "$OUT"
mkdir -p "$OUT/bin" "$OUT/scripts" "$OUT/docs"

need() { [[ -x "$1" ]] || { echo "Missing $1 — build first"; exit 1; }; }
need src/egad
need src/ega-cli

cp -a src/egad src/ega-cli "$OUT/bin/"
[[ -x src/ega-tx ]] && cp -a src/ega-tx "$OUT/bin/" || true
[[ -x src/qt/ega-qt ]] && cp -a src/qt/ega-qt "$OUT/bin/" || true

cp -a scripts/easy-start.sh scripts/easy-wallet.sh scripts/easy-mine.sh \
  scripts/ega-explorer.sh scripts/ega-explorer.py \
  scripts/ega-pool.sh scripts/ega-pool.py \
  scripts/install-desktop-apps.sh \
  "$OUT/scripts/" 2>/dev/null || true

cp docs/ega/getting-started.md docs/ega/params.md "$OUT/docs/" 2>/dev/null || true
cp README.md "$OUT/" 2>/dev/null || true

cat > "$OUT/README-RELEASE.txt" << EOF
Egalitarianism (EGA) ${VER} — Linux ${ARCH}

Binaries: bin/egad  bin/ega-cli  [bin/ega-qt]

Quick start:
  export PATH="\$PWD/bin:\$PATH"
  egad -daemon
  ega-cli getblockchaininfo
  ega-cli getnewaddress

Or from extracted tree:
  bash scripts/easy-start.sh
  bash scripts/ega-explorer.sh   # http://127.0.0.1:8088
  bash scripts/ega-pool.sh       # http://127.0.0.1:8089  stratum :3333

Site: https://egalitarianism-ega.github.io/ega-website/
EOF

chmod +x "$OUT/bin/"* "$OUT/scripts/"*.sh "$OUT/scripts/"*.py 2>/dev/null || true
TAR="/tmp/${NAME}.tar.gz"
tar -C "$(dirname "$OUT")" -czf "$TAR" "$(basename "$OUT")"
echo "Wrote $TAR"
ls -lh "$TAR"
echo "$TAR"
