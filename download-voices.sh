#!/usr/bin/env bash
# download-voices.sh — Download piper voice models for say4linux
# Usage: bash download-voices.sh [--all | --us | --uk | VOICE_NAME]
set -euo pipefail

MODEL_DIR="${SAY4LINUX_MODELS:-${HOME}/.local/share/say4linux/models}"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en"

EN_US_SPEAKERS=(amy arctic bryce danny hfc_female hfc_male joe john lessac libritts_r ljspeech ryan)
EN_GB_SPEAKERS=(alan alba aru cori jenny_dioco northern_english_male semaine southern_english_female)
QUALITIES=(low medium high)

download_voice() {
    local lang="$1" spk="$2" quality="$3"
    local dir="${MODEL_DIR}/${lang}/${spk}/${quality}"
    local onnx="en_${lang}-${spk}-${quality}.onnx"
    local url="${BASE_URL}/${lang}/${spk}/${quality}"

    if [ -f "${dir}/${onnx}" ]; then
        echo "  [skip] ${lang}/${spk}/${quality} (already exists)"
        return 0
    fi

    mkdir -p "${dir}"
    echo "  [downloading] ${lang}/${spk}/${quality}..."
    if wget -q --show-progress -O "${dir}/${onnx}" "${url}/${onnx}?download=1" 2>/dev/null; then
        wget -q -O "${dir}/${onnx}.json" "${url}/${onnx}.json?download=1" 2>/dev/null || {
            echo "    (no config JSON found; removing model)"
            rm -f "${dir}/${onnx}"
            return 1
        }
        echo "  [✓] ${lang}/${spk}/${quality}"
    else
        echo "  [✗] ${lang}/${spk}/${quality} not available"
        rmdir -p --ignore-fail-on-non-empty "${dir}" 2>/dev/null || true
        return 1
    fi
}

show_help() {
    echo "Usage: bash download-voices.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  --all         Download all US and UK voices (all qualities)"
    echo "  --us          Download all US English voices"
    echo "  --uk          Download all UK English voices"
    echo "  --list        List available voice names"
    echo "  VOICE_NAME    Download a specific voice (e.g., en_US/amy/medium)"
    echo ""
    echo "Models are saved to: ${MODEL_DIR}"
}

list_voices() {
    echo "Available US English voices:"
    for spk in "${EN_US_SPEAKERS[@]}"; do
        echo "  en_US/${spk}  (qualities: low, medium, high)"
    done
    echo ""
    echo "Available UK English voices:"
    for spk in "${EN_GB_SPEAKERS[@]}"; do
        echo "  en_GB/${spk}  (qualities: low, medium, high)"
    done
}

download_us() {
    echo "Downloading all US English voices..."
    for spk in "${EN_US_SPEAKERS[@]}"; do
        for q in "${QUALITIES[@]}"; do
            download_voice "en_US" "$spk" "$q" || true
        done
    done
}

download_uk() {
    echo "Downloading all UK English voices..."
    for spk in "${EN_GB_SPEAKERS[@]}"; do
        for q in "${QUALITIES[@]}"; do
            download_voice "en_GB" "$spk" "$q" || true
        done
    done
}

case "${1:-}" in
    --all)
        download_us
        download_uk
        ;;
    --us)
        download_us
        ;;
    --uk)
        download_uk
        ;;
    --list)
        list_voices
        ;;
    --help|-h|"")
        show_help
        ;;
    *)
        # Try to parse as lang/speaker/quality
        IFS='/' read -r lang spk quality <<< "$1"
        if [ -z "$lang" ] || [ -z "$spk" ] || [ -z "$quality" ]; then
            echo "ERROR: Specify voice as LANG/SPEAKER/QUALITY (e.g., en_US/amy/medium)"
            exit 1
        fi
        download_voice "$lang" "$spk" "$quality"
        ;;
esac

echo ""
echo "Done. Models saved to: ${MODEL_DIR}"
