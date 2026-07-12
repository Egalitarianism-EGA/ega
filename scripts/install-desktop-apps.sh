#!/usr/bin/env bash
# Install Egalitarianism desktop launchers (Linux app menu)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APPDIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONDIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR" "$ICONDIR"

ICON_SRC="$ROOT/share/pixmaps/ega256.png"
if [[ -f "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "$ICONDIR/egalitarianism.png"
fi

# Resolve binaries
EGAD="$ROOT/src/egad"
EGA_CLI="$ROOT/src/ega-cli"
EGA_QT="$ROOT/src/qt/ega-qt"
MINER_HELPER="$ROOT/scripts/ega-miner-app.sh"

cat > "$APPDIR/egalitarianism-wallet.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Egalitarianism Wallet
Comment=EGA desktop wallet
Exec=$EGA_QT
Icon=egalitarianism
Terminal=false
Categories=Office;Finance;
Keywords=crypto;ega;wallet;
EOF

cat > "$APPDIR/egalitarianism-node.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Egalitarianism Node
Comment=Start EGA full node (egad)
Exec=$ROOT/scripts/ega-node-app.sh
Icon=egalitarianism
Terminal=true
Categories=Network;
Keywords=crypto;ega;node;
EOF

cat > "$APPDIR/egalitarianism-miner.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Egalitarianism Miner
Comment=Mine EGA (CPU — choose algorithm)
Exec=$MINER_HELPER
Icon=egalitarianism
Terminal=true
Categories=Network;
Keywords=crypto;ega;mine;
EOF

chmod +x "$ROOT/scripts/ega-node-app.sh" "$ROOT/scripts/ega-miner-app.sh" 2>/dev/null || true
chmod +x "$APPDIR"/egalitarianism-*.desktop

# update desktop database if available
update-desktop-database "$APPDIR" 2>/dev/null || true

echo "Installed application shortcuts to:"
echo "  $APPDIR"
echo ""
echo "Look for:"
echo "  • Egalitarianism Wallet"
echo "  • Egalitarianism Node"
echo "  • Egalitarianism Miner"
echo ""
if [[ ! -x "$EGA_QT" ]]; then
  echo "Note: Wallet app needs ega-qt built first:"
  echo "  ./configure --with-gui=qt5 --enable-wallet --with-incompatible-bdb && make -j\$(nproc)"
fi
if [[ ! -x "$EGAD" ]]; then
  echo "Note: Node not built yet. Run: bash scripts/easy-install-linux.sh"
fi
