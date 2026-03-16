#!/usr/bin/env bash
# sample-voices.sh — Listen to all installed voices to find your favorite
# Usage: bash sample-voices.sh [TEXT]
set -euo pipefail

SAMPLE_TEXT="${*:-Hello! This is a sample of my voice. How do I sound?}"
SAY_CMD="${SAY_CMD:-say}"

echo "=== say4linux Voice Sampler ==="
echo "Sample text: \"${SAMPLE_TEXT}\""
echo ""
echo "Press ENTER to play the next voice, or 'q' to quit."
echo "Type 's' to hear the current voice again."
echo ""

# Get list of voices
voices=$("${SAY_CMD}" -v list 2>/dev/null | grep -oP '^\s+\K\S+(?=:)') || {
    echo "ERROR: No voices found. Run download-voices.sh first."
    exit 1
}

count=$(echo "$voices" | wc -l)
current=0

for voice in $voices; do
    current=$((current + 1))
    echo "[$current/$count] Voice: ${voice}"
    "${SAY_CMD}" -v "$voice" "$SAMPLE_TEXT" 2>/dev/null

    while true; do
        read -rp "  [ENTER=next | s=replay | f=favorite | q=quit] " choice
        case "$choice" in
            s|S)
                "${SAY_CMD}" -v "$voice" "$SAMPLE_TEXT" 2>/dev/null
                ;;
            f|F)
                echo ""
                echo "  ★ To use ${voice} as your default, add to your ~/.bashrc:"
                echo "    alias say='say -v ${voice}'"
                echo ""
                read -rp "  [ENTER=continue to next voice | q=quit] " next
                if [[ "$next" == "q" || "$next" == "Q" ]]; then
                    echo ""
                    echo "Done! Set your favorite voice with:"
                    echo "  alias say='say -v YOUR_VOICE'"
                    exit 0
                fi
                break
                ;;
            q|Q)
                echo ""
                echo "Done! Set your favorite voice with:"
                echo "  alias say='say -v YOUR_VOICE'"
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
done

echo ""
echo "All voices sampled! Set your favorite with:"
echo "  alias say='say -v YOUR_VOICE'"
