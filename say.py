#!/usr/bin/env python3
"""
WSL2 TTS wrapper using piper-tts - mimics macOS 'say' command
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

def find_piper():
    """Locate piper binary - check venv first, then PATH"""
    # Check venv location
    if os.path.exists(PIPER_BIN):
        return PIPER_BIN
    
    # Fallback to PATH
    piper = shutil.which("piper")
    if piper:
        return piper
    
    print("ERROR: 'piper' not found.", file=sys.stderr)
    print(f"Expected at: {PIPER_BIN}", file=sys.stderr)
    print("Install: sudo python3 -m venv /opt/piper-tts && sudo /opt/piper-tts/bin/pip install piper-tts", file=sys.stderr)
    sys.exit(1)

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
    """List available voice models"""
    base = "/mnt/c/tts/models"
    if not os.path.exists(base):
        print(f"No models found at {base}", file=sys.stderr)
        return
    
    print("Available voices:")
    for root, dirs, files in os.walk(base):
        for f in files:
            if f.endswith(".onnx") and not f.endswith(".json"):
                rel = os.path.relpath(os.path.join(root, f), base)
                # Extract voice name from path
                parts = rel.split(os.sep)
                if len(parts) >= 3:
                    voice_name = f"{parts[0]}-{parts[1]}-{parts[2]}"
                    print(f"  {voice_name}: {rel}")

def get_model_path(voice_name):
    """Convert voice name to model path"""
    base = "/mnt/c/tts/models"
    
    # If full path provided
    if voice_name.endswith(".onnx"):
        return voice_name, voice_name + ".json"
    
    # Try to find by voice name (e.g., "en_US-amy-medium")
    for root, dirs, files in os.walk(base):
        for f in files:
            if f.endswith(".onnx") and not f.endswith(".json"):
                if voice_name in f or voice_name in root:
                    model = os.path.join(root, f)
                    config = model + ".json"
                    if os.path.exists(config):
                        return model, config
    
    return None, None

def main():
    parser = argparse.ArgumentParser(
        description="Text-to-speech using piper-tts (WSL2)",
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
    parser.add_argument('-r', '--rate', type=float, default=1.0,
                        help='Speaking rate (0.5-2.0, default: 1.0)')
    parser.add_argument('--keep', action='store_true',
                        help='Keep temporary WAV file for debugging')
    
    args = parser.parse_args()
    
    # Handle --voice list
    if args.voice == 'list':
        list_voices()
        sys.exit(0)
    
    # Get piper binary
    piper = find_piper()
    
    # Get text to speak
    text = get_text(args)
    if not text:
        sys.exit(0)
    
    # Find model files
    model, config = get_model_path(args.voice)
    if not model or not os.path.exists(model):
        print(f"ERROR: Voice '{args.voice}' not found", file=sys.stderr)
        print("Run 'say -v list' to see available voices", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if args.output:
        wav = args.output
        cleanup = False
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav = tmp.name
        tmp.close()
        cleanup = not args.keep
    
    try:
        # Build piper command
        cmd = [piper, "--model", model, "--config", config, "--output_file", wav]
        
        # Add speaking rate if not default
        if args.rate != 1.0:
            cmd.extend(["--length_scale", str(1.0 / args.rate)])
        
        # Run piper with text via stdin (more reliable than -t for long text)
        result = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True
        )
        
        if result.returncode != 0:
            print(f"ERROR: piper failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        # Play audio if not saving to file
        if not args.output:
            # Try paplay first (PulseAudio), then fallback to aplay (ALSA)
            player = shutil.which("paplay") or shutil.which("aplay")
            if player:
                subprocess.run([player, wav], check=False, 
                             stderr=subprocess.DEVNULL)
            else:
                print("WARNING: No audio player found (paplay/aplay)", 
                      file=sys.stderr)
                print(f"Audio saved to: {wav}", file=sys.stderr)
                cleanup = False
        else:
            print(f"Audio saved to: {wav}")
    
    finally:
        # Cleanup temp file
        if cleanup and os.path.exists(wav):
            os.unlink(wav)

if __name__ == "__main__":
    main()
