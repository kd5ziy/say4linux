# say4linux

A macOS-style `say` command for Linux/WSL2, powered by [piper-tts](https://github.com/rhasspy/piper).

## Overview

This project provides a drop-in `say` command that mimics the macOS text-to-speech CLI on Linux and WSL2 systems. It uses **piper-tts** for fast, local, offline speech synthesis with a variety of natural-sounding voices.

## Features

- macOS-compatible `say` command syntax
- Supports multiple English voices (US and UK)
- Adjustable speaking rate
- Pipe-friendly: `echo "hello" | say`
- Save output to WAV files
- Works great as a Claude Code hook for audio notifications

## Prerequisites

- Python 3
- PulseAudio (`paplay`) or ALSA (`aplay`) for audio playback
- [piper-tts](https://github.com/rhasspy/piper) installed in a virtualenv at `/opt/piper-tts`

## Installation

### 1. Install piper-tts

```bash
sudo python3 -m venv /opt/piper-tts
sudo /opt/piper-tts/bin/pip install piper-tts
```

### 2. Download voice models

```bash
cd /mnt/c/tts/models  # or your preferred model directory
bash GetAllUSUKModelVoices.sh
```

### 3. Install the say command

```bash
chmod +x say.py
ln -s "$(pwd)/say.py" ~/.local/bin/say
```

Make sure `~/.local/bin` is in your `PATH`.

## Usage

```bash
say "Hello world"
echo "Hello" | say
say -v en_US-amy-medium "Testing a specific voice"
say -v list                    # List available voices
say -o output.wav "Save to file"
say -r 1.5 "Speak faster"
```

## Claude Code Integration

This works well as a [Claude Code hook](https://docs.anthropic.com/en/docs/claude-code) for audio notifications. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "say 'Claude has finished'" }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "idle_prompt",
        "hooks": [
          { "type": "command", "command": "say 'Claude is waiting for input'" }
        ]
      }
    ]
  }
}
```

## Acknowledgments

This project is built on top of these open-source projects:

- **[piper](https://github.com/rhasspy/piper)** — A fast, local neural text-to-speech system by [Michael Hansen (rhasspy)](https://github.com/rhasspy). Piper is licensed under the MIT License.
- **[piper-voices](https://huggingface.co/rhasspy/piper-voices)** — Pre-trained voice models for piper, hosted on Hugging Face. Voice models have their own individual licenses; see the [piper-voices repository](https://huggingface.co/rhasspy/piper-voices) for details.
- **[piper-tts](https://pypi.org/project/piper-tts/)** — Python package wrapping the piper engine.

## License

MIT
