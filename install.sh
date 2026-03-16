#!/usr/bin/env bash
# install.sh — One-step installer for say4linux
# Usage: bash install.sh
set -euo pipefail

INSTALL_DIR="${HOME}/.local/share/say4linux"
BIN_DIR="${HOME}/.local/bin"
MODEL_DIR="${INSTALL_DIR}/models"
VENV_PATH="/opt/piper-tts"
DEFAULT_VOICE="en_US-amy-medium"

echo "=== say4linux installer ==="
echo ""

# --- 1. Check Python 3 ---
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not found."
    echo "Install it with: sudo apt install python3 python3-venv"
    exit 1
fi
echo "[✓] python3 found: $(python3 --version)"

# --- 2. Install piper-tts in system venv ---
if [ -x "${VENV_PATH}/bin/piper" ]; then
    echo "[✓] piper-tts already installed at ${VENV_PATH}"
else
    echo "[*] Installing piper-tts to ${VENV_PATH} (requires sudo)..."
    sudo python3 -m venv "${VENV_PATH}"
    sudo "${VENV_PATH}/bin/pip" install --upgrade pip
    sudo "${VENV_PATH}/bin/pip" install piper-tts
    echo "[✓] piper-tts installed"
fi

# --- 3. Check for audio player ---
if command -v paplay &>/dev/null; then
    echo "[✓] Audio player found: paplay (PulseAudio)"
elif command -v aplay &>/dev/null; then
    echo "[✓] Audio player found: aplay (ALSA)"
else
    echo "[!] WARNING: No audio player found (paplay or aplay)."
    echo "    Install PulseAudio: sudo apt install pulseaudio-utils"
    echo "    Or ALSA:            sudo apt install alsa-utils"
fi

# --- 4. Copy say.py into place ---
mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${SCRIPT_DIR}/say.py" "${INSTALL_DIR}/say.py"
chmod +x "${INSTALL_DIR}/say.py"

# Create or update symlink
ln -sf "${INSTALL_DIR}/say.py" "${BIN_DIR}/say"
echo "[✓] Installed say -> ${BIN_DIR}/say"

# --- 5. Check PATH ---
if echo "${PATH}" | tr ':' '\n' | grep -q "^${BIN_DIR}$"; then
    echo "[✓] ${BIN_DIR} is in your PATH"
else
    echo "[!] ${BIN_DIR} is NOT in your PATH."
    echo "    Add this to your ~/.bashrc or ~/.zshrc:"
    echo "      export PATH=\"\${HOME}/.local/bin:\${PATH}\""
fi

# --- 6. Download a default voice model ---
mkdir -p "${MODEL_DIR}"
VOICE_DIR="${MODEL_DIR}/en_US/amy/medium"
ONNX_FILE="en_en_US-amy-medium.onnx"

if [ -f "${VOICE_DIR}/${ONNX_FILE}" ]; then
    echo "[✓] Default voice model already downloaded"
else
    echo "[*] Downloading default voice (${DEFAULT_VOICE})..."
    mkdir -p "${VOICE_DIR}"
    BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium"
    wget -q --show-progress -O "${VOICE_DIR}/${ONNX_FILE}" "${BASE_URL}/${ONNX_FILE}?download=1"
    wget -q --show-progress -O "${VOICE_DIR}/${ONNX_FILE}.json" "${BASE_URL}/${ONNX_FILE}.json?download=1"
    echo "[✓] Default voice downloaded"
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Test it out:"
echo "  say 'Hello from say4linux'"
echo ""
echo "List available voices:"
echo "  say -v list"
echo ""
echo "Download more voices:"
echo "  bash $(dirname "${BASH_SOURCE[0]}")/download-voices.sh"
