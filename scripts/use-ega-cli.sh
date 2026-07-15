#!/usr/bin/env bash
# Fix "ega-cli: command not found" — add built binaries to PATH for this shell.
# Usage:  source scripts/use-ega-cli.sh
# Then:   ega-cli getblockcount
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ROOT/src:$PATH"
echo "PATH += $ROOT/src"
command -v ega-cli
command -v egad
ega-cli getblockcount 2>/dev/null || true
