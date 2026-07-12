# Installing EGA Core

Build from source (see [README.md](README.md) and `doc/build-*.md`).

```bash
./autogen.sh
./configure
make
sudo make install   # installs digibyted / digibyte-cli unless renamed
```

**EGA-friendly names** (wrappers, no reinstall required):

```bash
sudo cp contrib/ega/egad contrib/ega/ega-cli contrib/ega/ega-tx /usr/local/bin/
# ensure digibyted is on PATH, or set EGA_BIN_DIR to your build src/
```

Default paths:

| Item | Path |
|------|------|
| Data | `~/.ega/` |
| Config | `~/.ega/ega.conf` |
| PID | `~/.ega/egad.pid` |

Copy `share/examples/ega.conf` to `~/.ega/ega.conf` and set `rpcuser` / `rpcpassword`.
