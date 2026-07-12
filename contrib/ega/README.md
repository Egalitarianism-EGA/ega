# EGA binaries

Primary build outputs (after rename):

| Binary | Role |
|--------|------|
| `src/egad` | Full node daemon |
| `src/ega-cli` | RPC client |
| `src/ega-tx` | Transaction utility |
| `src/qt/ega-qt` | Desktop GUI (if `--with-gui`) |

Wrappers in this folder call the build tree (`EGA_BIN_DIR`) or PATH, with fallback to old `digibyte*` names if present.

```bash
export EGA_BIN_DIR="$PWD/src"
./contrib/ega/egad -version
./contrib/ega/ega-cli getblockchaininfo
```

Default data directory: `~/.ega` · config: `~/.ega/ega.conf`
