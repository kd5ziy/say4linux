# helper: download one voice if it exists
dl() {
  local lang="$1"   # en_US or en_GB
  local spk="$2"    # speaker folder name
  local q="$3"      # low|medium|high
  local base="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/${lang}/${spk}/${q}"
  local onnx="en_${lang}-${spk}-${q}.onnx"
  local json="en_${lang}-${spk}-${q}.onnx.json"
  mkdir -p "${lang}/${spk}/${q}"
  echo "-> ${lang}/${spk}/${q}"
  # .onnx (model)
  if wget -q --show-progress -O "${lang}/${spk}/${q}/${onnx}" "${base}/${onnx}?download=1"; then
    # .json (config)
    wget -q --show-progress -O "${lang}/${spk}/${q}/${json}" "${base}/${json}?download=1" || {
      echo "   (no JSON found; removing model)"
      rm -f "${lang}/${spk}/${q}/${onnx}"
    }
  else
    echo "   (model not found, skipping)"
    rmdir -p --ignore-fail-on-non-empty "${lang}/${spk}/${q}" 2>/dev/null || true
  fi
}

# speakers currently listed in the repo
EN_US_SPK=(
  amy arctic bryce danny hfc_female hfc_male joe john
  lessac libritts_r ljspeech ryan
)
EN_GB_SPK=(
  alan alba aru cori jenny_dioco northern_english_male semaine southern_english_female
)

QUALS=(low medium high)

# Download en_US voices
for s in "${EN_US_SPK[@]}"; do
  for q in "${QUALS[@]}"; do dl "en_US" "$s" "$q"; done
done

# Download en_GB voices
for s in "${EN_GB_SPK[@]}"; do
  for q in "${QUALS[@]}"; do dl "en_GB" "$s" "$q"; done
done

echo "Done. Models under /mnt/c/tts/models/"# helper: download one voice if it exists
dl() {
  local lang="$1"   # en_US or en_GB
  local spk="$2"    # speaker folder name
  local q="$3"      # low|medium|high
  local base="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/${lang}/${spk}/${q}"
  local onnx="en_${lang}-${spk}-${q}.onnx"
  local json="en_${lang}-${spk}-${q}.onnx.json"
  mkdir -p "${lang}/${spk}/${q}"
  echo "-> ${lang}/${spk}/${q}"
  # .onnx (model)
  if wget -q --show-progress -O "${lang}/${spk}/${q}/${onnx}" "${base}/${onnx}"; then
    # .json (config)
    wget -q --show-progress -O "${lang}/${spk}/${q}/${json}" "${base}/${json}" || {
      echo "   (no JSON found; removing model)"
      rm -f "${lang}/${spk}/${q}/${onnx}"
    }
  else
    echo "   (model not found, skipping)"
    rmdir -p --ignore-fail-on-non-empty "${lang}/${spk}/${q}" 2>/dev/null || true
  fi
}

# speakers currently listed in the repo
EN_US_SPK=(
  amy arctic bryce danny hfc_female hfc_male joe john
  lessac libritts_r ljspeech ryan
)
EN_GB_SPK=(
  alan alba aru cori jenny_dioco northern_english_male semaine southern_english_female
)

QUALS=(low medium high)

# Download en_US voices
for s in "${EN_US_SPK[@]}"; do
  for q in "${QUALS[@]}"; do dl "en_US" "$s" "$q"; done
done

# Download en_GB voices
for s in "${EN_GB_SPK[@]}"; do
  for q in "${QUALS[@]}"; do dl "en_GB" "$s" "$q"; done
done

echo "Done. Models under /mnt/c/tts/models/"
