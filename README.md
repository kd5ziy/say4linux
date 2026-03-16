# say4linux

A macOS-style `say` command for Linux/WSL2, powered by [piper-tts](https://github.com/rhasspy/piper). Fast, local, offline text-to-speech with natural-sounding voices.

## Quick Start

```bash
git clone https://github.com/kd5ziy/say4linux.git
cd say4linux
bash install.sh
say "Hello from say4linux"
```

That's it! The installer handles everything: piper-tts, a default voice model, and PATH setup.

## What You Get

- **`say`** — drop-in replacement for the macOS `say` command
- **`install.sh`** — automated installer (piper-tts + default voice + symlink)
- **`download-voices.sh`** — download additional US/UK English voices
- **`sample-voices.sh`** — interactive voice sampler to find your favorite
- **`uninstall.sh`** — clean removal

## Detailed Setup Guide

### Prerequisites

| Requirement | Why | Install |
|---|---|---|
| Python 3.7+ | Runs say.py | `sudo apt install python3 python3-venv` |
| wget | Downloads voice models | `sudo apt install wget` |
| PulseAudio **or** ALSA | Plays audio | `sudo apt install pulseaudio-utils` or `sudo apt install alsa-utils` |

On WSL2, PulseAudio is typically available if you're running WSLg (Windows 11). For older setups, see [WSL2 Audio Setup](#wsl2-audio-setup) below.

### Step-by-Step Manual Installation

If you prefer to install manually instead of using `install.sh`:

**1. Install piper-tts**

```bash
sudo python3 -m venv /opt/piper-tts
sudo /opt/piper-tts/bin/pip install --upgrade pip
sudo /opt/piper-tts/bin/pip install piper-tts
```

**2. Download a voice model**

```bash
# Download just the default voice (en_US-amy-medium)
bash download-voices.sh en_US/amy/medium

# Or download all US voices
bash download-voices.sh --us

# Or download everything (US + UK, all qualities)
bash download-voices.sh --all
```

**3. Install the say command**

```bash
mkdir -p ~/.local/bin
cp say.py ~/.local/share/say4linux/say.py
chmod +x ~/.local/share/say4linux/say.py
ln -sf ~/.local/share/say4linux/say.py ~/.local/bin/say
```

**4. Ensure ~/.local/bin is in your PATH**

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="${HOME}/.local/bin:${PATH}"
```

Then reload: `source ~/.bashrc`

## Usage

```bash
# Basic usage
say "Hello world"

# Pipe text in
echo "The build succeeded" | say

# Choose a voice
say -v en_US-amy-medium "Amy speaking"
say -v en_GB-alba-medium "British voice"

# List installed voices
say -v list

# Save to WAV file instead of playing
say -o greeting.wav "Hello world"

# Adjust speaking rate (0.5 = slow, 2.0 = fast)
say -r 1.5 "Speaking faster"
say -r 0.7 "Speaking slower"
```

## Voice Models

Voices follow the naming pattern: `LANG-SPEAKER-QUALITY`

| Quality | Size | Best for |
|---|---|---|
| `low` | ~15 MB | Fastest, lower quality |
| `medium` | ~60 MB | Good balance (recommended) |
| `high` | ~100 MB | Best quality, slower |

### Choosing a voice

Not sure which voice you like? Use the interactive voice sampler:

```bash
bash sample-voices.sh
```

It plays each installed voice one at a time. You can replay, mark favorites, and skip. When you find one you like, set it as your default:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias say='say -v en_GB-alba-medium'
```

### Managing voices

```bash
# See what's available to download
bash download-voices.sh --list

# Download specific voice
bash download-voices.sh en_US/ryan/high

# Download all US voices
bash download-voices.sh --us

# Download all UK voices
bash download-voices.sh --uk

# Download everything
bash download-voices.sh --all
```

### Custom model directory

Set `SAY4LINUX_MODELS` to use a different location:

```bash
export SAY4LINUX_MODELS="/path/to/my/models"
```

The command searches for models in this order:
1. `$SAY4LINUX_MODELS` (if set)
2. `~/.local/share/say4linux/models`
3. `/mnt/c/tts/models` (WSL2 legacy path)

## Claude Code Integration

`say` works perfectly as a [Claude Code](https://claude.com/claude-code) hook for audio notifications while coding.

### Hooks Setup

Copy `examples/claude-hooks.json` into your Claude settings, or add hooks manually to `~/.claude/settings.json`:

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
      },
      {
        "matcher": "permission_prompt",
        "hooks": [
          { "type": "command", "command": "say 'Claude needs permission'" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "say 'Command complete'" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "say 'Agent task complete'" }
        ]
      }
    ],
    "TaskCompleted": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "say 'Task completed'" }
        ]
      }
    ]
  }
}
```

Available hook events: `Stop`, `Notification`, `PostToolUse`, `PreToolUse`, `SubagentStop`, `TaskCompleted`, `SessionStart`, `SessionEnd`, and more. See the full example in [`examples/claude-hooks.json`](examples/claude-hooks.json).

### Skills (Slash Commands)

This repo includes two Claude Code skills in `.claude/skills/`:

| Command | Description |
|---|---|
| `/list-voices` | List all installed voices, grouped by language and quality |
| `/say-test [voice] [text]` | Test a specific voice with sample text |

To use these skills, clone this repo and open it with Claude Code — the skills are picked up automatically from `.claude/skills/`.

```bash
# Inside Claude Code:
/list-voices
/say-test en_GB-alba-medium "Testing the British voice"
```

## WSL2 Audio Setup

On **Windows 11** with WSLg, audio should work out of the box via PulseAudio.

On **Windows 10** or older WSL2 setups, you need to forward audio to Windows:

1. Install [PulseAudio for Windows](https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/)
2. In WSL2, configure PulseAudio to connect to the Windows host:
   ```bash
   export PULSE_SERVER=tcp:$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
   ```
   Add that line to your `~/.bashrc` for persistence.

## Troubleshooting

| Problem | Solution |
|---|---|
| `say: command not found` | Ensure `~/.local/bin` is in your PATH |
| `ERROR: 'piper' not found` | Run `install.sh` or install piper-tts manually |
| `ERROR: Voice not found` | Run `say -v list` to check installed voices; use `download-voices.sh` to get more |
| No sound on WSL2 | Check `paplay --version`; see [WSL2 Audio Setup](#wsl2-audio-setup) |
| Audio choppy/distorted | Try a `low` quality model or check PulseAudio config |

## Uninstalling

```bash
bash uninstall.sh
```

This removes the `say` symlink and optionally the model files. piper-tts at `/opt/piper-tts` is left in place (remove manually with `sudo rm -rf /opt/piper-tts`).

## Acknowledgments

This project is built on these open-source projects:

- **[piper](https://github.com/rhasspy/piper)** — A fast, local neural text-to-speech system by [Michael Hansen (rhasspy)](https://github.com/rhasspy). Licensed under the MIT License.
- **[piper-voices](https://huggingface.co/rhasspy/piper-voices)** — Pre-trained voice models for piper, hosted on Hugging Face. Individual voice models have their own licenses; see the [piper-voices repository](https://huggingface.co/rhasspy/piper-voices) for details.
- **[piper-tts](https://pypi.org/project/piper-tts/)** — Python package wrapping the piper engine.

## License

MIT
