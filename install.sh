#!/bin/sh
# Install kc (kill-claude-for-memory) as a single executable — needs only python3.
#
#   From a clone:  ./install.sh
#   Without clone: curl -fsSL https://raw.githubusercontent.com/dwivedi-ritik/kcfm/main/install.sh | sh
#
# Override the repo with KC_REPO=owner/name, branch with KC_BRANCH, dir with KC_BIN.
set -e

REPO="${KC_REPO:-dwivedi-ritik/kcfm}"
BRANCH="${KC_BRANCH:-main}"
BIN_DIR="${KC_BIN:-$HOME/.local/bin}"

command -v python3 >/dev/null 2>&1 || { echo "python3 is required"; exit 1; }
mkdir -p "$BIN_DIR"

SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/src/kc" ]; then
    SRC="$SCRIPT_DIR/src"                       # running from a clone
    CLEANUP=""
else                                           # curl'd: fetch the source tarball
    command -v curl >/dev/null 2>&1 || { echo "curl is required"; exit 1; }
    TMP="$(mktemp -d)"
    CLEANUP="$TMP"
    echo "downloading $REPO@$BRANCH..."
    curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" | tar xz -C "$TMP"
    SRC="$TMP/${REPO#*/}-$BRANCH/src"
fi

python3 -m zipapp "$SRC" -m "kc.cli:main" -p "/usr/bin/env python3" -o "$BIN_DIR/kc"
chmod +x "$BIN_DIR/kc"
[ -n "$CLEANUP" ] && rm -rf "$CLEANUP"

echo "installed to $BIN_DIR/kc"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "note: add $BIN_DIR to your PATH" ;;
esac
