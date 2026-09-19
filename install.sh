#!/bin/sh
# Install ccbear as a single executable. Needs only python3 (no uv, no pip):
# bundles the package into one zipapp file on your PATH.
set -e

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required"
    exit 1
fi

SRC="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="${CCBEAR_BIN:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"

python3 -m zipapp "$SRC/src" \
    -m "ccbear.cli:main" \
    -p "/usr/bin/env python3" \
    -o "$BIN_DIR/ccbear"
chmod +x "$BIN_DIR/ccbear"

echo "installed to $BIN_DIR/ccbear"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "note: add $BIN_DIR to your PATH" ;;
esac
