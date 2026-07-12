# Building EGA Core for Windows

**Target:** Windows 10/11 x64 (native MinGW or cross-compile from Linux).  
GUI optional; start with daemon + CLI.

## Option A — Cross-compile from Linux (recommended for release)

Uses the existing DigiByte/Bitcoin `depends` system.

```bash
# On Debian/Ubuntu host
sudo apt install -y g++-mingw-w64-x86-64 mingw-w64 cmake

# Build dependencies for Windows
cd depends
make HOST=x86_64-w64-mingw32 -j$(nproc)
cd ..

./autogen.sh
CONFIG_SITE=$PWD/depends/x86_64-w64-mingw32/share/config.site \
  ./configure --prefix=/ --without-gui --disable-wallet
make -j$(nproc)
```

Outputs under `src/` as `.exe` when configured for mingw (exact names still `digibyted.exe` / `digibyte-cli.exe` until full rename). Ship with `contrib/ega` wrappers adapted for Windows, or rename in packaging.

**RandomX:** cmake must be available during the Windows target build; if depends does not build RandomX, ensure `src/crypto/randomx/build` is produced for the mingw toolchain (may need a mingw-aware cmake invocation in `Makefile.am` for CI).

## Option B — Native build on Windows (MSYS2)

1. Install [MSYS2](https://www.msys2.org/).
2. In **MINGW64** shell:

```bash
pacman -S --needed base-devel mingw-w64-x86_64-toolchain mingw-w64-x86_64-cmake \
  mingw-w64-x86_64-boost mingw-w64-x86_64-openssl mingw-w64-x86_64-libevent \
  mingw-w64-x86_64-zeromq git python
```

3. Clone/build as on Linux (`./autogen.sh && ./configure --without-gui && make`).

Default data directory on Windows: `%APPDATA%\EGA\`  
Config: `%APPDATA%\EGA\ega.conf`

## Packaging checklist

- [ ] `digibyted.exe` / `digibyte-cli.exe` (or renamed `egad.exe`)
- [ ] Example `ega.conf` from `share/examples/ega.conf`
- [ ] Note ports 20201/20202 in firewall docs
- [ ] VC++ / MinGW runtime if required by your toolchain

## Known gaps

- Full Qt GUI packaging for Windows not in Phase 6 scope.
- macOS: deferred (see design status); use Linux/Windows first.
