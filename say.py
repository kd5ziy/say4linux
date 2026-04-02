#!/usr/bin/env python3
"""
say4linux — macOS-style 'say' command for Linux/WSL2, powered by piper-tts.
https://github.com/kd5ziy/say4linux
"""
import os
import sys
import subprocess
import shutil
import tempfile
import argparse

# Path to the virtual environment
VENV_PATH = "/opt/piper-tts"
PIPER_BIN = os.path.join(VENV_PATH, "bin", "piper")

# Model search paths (checked in order)
MODEL_DIRS = [
    os.environ.get("SAY4LINUX_MODELS", ""),
    os.path.expanduser("~/.local/share/say4linux/models"),
    "/mnt/c/tts/models",
]
MODEL_DIRS = [d for d in MODEL_DIRS if d]

def find_piper():
    """Locate piper binary - check venv first, then PATH. Returns None if not found."""
    # Check venv location
    if os.path.exists(PIPER_BIN):
        return PIPER_BIN

    # Fallback to PATH
    piper = shutil.which("piper")
    if piper:
        return piper

    return None

def get_text(args):
    """Get text from arguments or stdin"""
    if args.text:
        return " ".join(args.text)
    elif not sys.stdin.isatty():
        return sys.stdin.read().strip()
    else:
        print("ERROR: No text provided", file=sys.stderr)
        print("Usage: say 'text' or echo 'text' | say", file=sys.stderr)
        sys.exit(1)

def list_voices():
    """Return available voice models as a list of dicts from all model directories."""
    voices = []
    for base in MODEL_DIRS:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                if f.endswith(".onnx") and not f.endswith(".json"):
                    rel = os.path.relpath(os.path.join(root, f), base)
                    parts = rel.split(os.sep)
                    voice_name = f"{parts[0]}-{parts[1]}-{parts[2]}" if len(parts) >= 3 else f
                    voices.append({
                        "name": voice_name,
                        "path": rel,
                        "full_path": os.path.join(root, f),
                    })
    return voices


def print_voices():
    """Print available voices to stdout (CLI use)."""
    voices = list_voices()
    if voices:
        print("Available voices:")
        for v in voices:
            print(f"  {v['name']}: {v['path']}")
    else:
        print("No models found. Run download-voices.sh to get started.", file=sys.stderr)

def get_model_path(voice_name):
    """Convert voice name to model path, searching all model directories"""
    # If full path provided
    if voice_name.endswith(".onnx"):
        return voice_name, voice_name + ".json"

    for base in MODEL_DIRS:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                if f.endswith(".onnx") and not f.endswith(".json"):
                    if voice_name in f or voice_name in root:
                        model = os.path.join(root, f)
                        config = model + ".json"
                        if os.path.exists(config):
                            return model, config

    return None, None

def synthesize(text, voice="en_US-amy-medium", rate=1.0, output=None, keep=False):
    """Synthesize text to speech. Plays audio or saves to file.

    Args:
        text: Text to speak
        voice: Voice model name (e.g. en_US-amy-medium)
        rate: Speaking rate (0.5-2.0, default 1.0)
        output: Output WAV path. If None, plays audio on host.
        keep: If True and no output specified, keep the temp WAV file.

    Returns:
        dict with 'status' ('ok' or 'error'), and optionally
        'wav_path', 'played', 'warning', or 'error' message.
    """
    if rate <= 0 or rate > 10:
        return {"status": "error", "error": f"Invalid rate {rate}: must be between 0.1 and 10.0"}

    piper = find_piper()
    if not piper:
        return {"status": "error", "error": "'piper' not found. Run install.sh or install piper-tts."}

    model, config = get_model_path(voice)
    if not model or not os.path.exists(model):
        return {"status": "error", "error": f"Voice '{voice}' not found"}

    if output:
        wav = output
        cleanup = False
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav = tmp.name
        tmp.close()
        cleanup = not keep

    try:
        cmd = [piper, "--model", model, "--config", config, "--output_file", wav]
        if rate != 1.0:
            cmd.extend(["--length_scale", str(1.0 / rate)])

        result = subprocess.run(cmd, input=text, text=True, capture_output=True)
        if result.returncode != 0:
            return {"status": "error", "error": f"piper failed: {result.stderr}"}

        if output:
            return {"status": "ok", "wav_path": wav}

        # Play audio
        player = shutil.which("paplay") or shutil.which("aplay")
        if player:
            subprocess.run([player, wav], check=False, stderr=subprocess.DEVNULL)
            result = {"status": "ok", "played": True}
            if keep:
                result["wav_path"] = wav
            return result
        else:
            cleanup = False
            return {"status": "ok", "wav_path": wav, "warning": "No audio player found (paplay/aplay)"}
    finally:
        if cleanup and os.path.exists(wav):
            os.unlink(wav)


def main():
    parser = argparse.ArgumentParser(
        description="Text-to-speech using piper-tts (Linux/WSL2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  say "Hello world"
  echo "Hello" | say
  say -v en_US-amy-medium "Testing voice"
  say -v list
  say -o output.wav "Save to file"
        """
    )
    parser.add_argument('text', nargs='*', help='Text to speak')
    parser.add_argument('-v', '--voice', default='en_US-amy-medium',
                        help='Voice model name or "list" to show available voices')
    parser.add_argument('-o', '--output', help='Output WAV file (skip playback)')
    def valid_rate(value):
        f = float(value)
        if f <= 0 or f > 10:
            raise argparse.ArgumentTypeError(f"rate must be between 0.1 and 10.0, got {value}")
        return f
    parser.add_argument('-r', '--rate', type=valid_rate, default=1.0,
                        help='Speaking rate (0.5-2.0, default: 1.0)')
    parser.add_argument('--keep', action='store_true',
                        help='Keep temporary WAV file for debugging')

    args = parser.parse_args()

    # Handle --voice list
    if args.voice == 'list':
        print_voices()
        sys.exit(0)

    # Verify piper exists (for CLI error messaging)
    if not find_piper():
        print("ERROR: 'piper' not found.", file=sys.stderr)
        print(f"Expected at: {PIPER_BIN}", file=sys.stderr)
        print("Install: sudo python3 -m venv /opt/piper-tts && sudo /opt/piper-tts/bin/pip install piper-tts", file=sys.stderr)
        sys.exit(1)

    # Get text to speak
    text = get_text(args)
    if not text:
        sys.exit(0)

    result = synthesize(text, voice=args.voice, rate=args.rate, output=args.output, keep=args.keep)

    if result["status"] == "error":
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if "not found" in result["error"] and "Voice" in result["error"]:
            print("Run 'say -v list' to see available voices", file=sys.stderr)
        sys.exit(1)

    if args.output:
        print(f"Audio saved to: {result.get('wav_path', args.output)}")
    elif result.get("warning"):
        print(f"WARNING: {result['warning']}", file=sys.stderr)
        if result.get("wav_path"):
            print(f"Audio saved to: {result['wav_path']}", file=sys.stderr)
    elif args.keep and result.get("wav_path"):
        print(f"Audio saved to: {result['wav_path']}")

if __name__ == "__main__":
    main()
