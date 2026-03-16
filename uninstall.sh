#!/usr/bin/env bash
# uninstall.sh — Remove say4linux
set -euo pipefail

INSTALL_DIR="${HOME}/.local/share/say4linux"
BIN_LINK="${HOME}/.local/bin/say"

echo "=== say4linux uninstaller ==="
echo ""

if [ -L "${BIN_LINK}" ]; then
    rm -f "${BIN_LINK}"
    echo "[✓] Removed ${BIN_LINK}"
else
    echo "[·] No symlink at ${BIN_LINK}"
fi

if [ -d "${INSTALL_DIR}" ]; then
    read -rp "Remove ${INSTALL_DIR} and all downloaded models? [y/N] " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "${INSTALL_DIR}"
        echo "[✓] Removed ${INSTALL_DIR}"
    else
        echo "[·] Kept ${INSTALL_DIR}"
    fi
else
    echo "[·] No install directory at ${INSTALL_DIR}"
fi

echo ""
echo "Note: piper-tts at /opt/piper-tts was NOT removed."
echo "To remove it: sudo rm -rf /opt/piper-tts"
