# say4linux

macOS-style `say` command for Linux/WSL2, powered by piper-tts. Fast, local, offline text-to-speech.

## Project Structure

- `say.py` — Core TTS engine (voice listing, model lookup, synthesis, playback)
- `mcp_server.py` — MCP server exposing TTS as tools (say, list_available_voices, save_audio)
- `install.sh` — Automated installer (piper-tts + default voice + symlink)
- `setup-mcp.sh` — MCP server setup (creates mcp_venv, installs mcp SDK)
- `download-voices.sh` — Download US/UK English voice models from HuggingFace
- `sample-voices.sh` — Interactive voice sampler
- `uninstall.sh` — Clean removal
- `test_say.py` — Unit tests (mocked) + integration tests (real piper synthesis)
- `.mcp.json` — MCP server registration for Claude Code auto-discovery
- `.claude/skills/` — Claude Code slash commands (/say, /list-voices, /say-test)

## Key Architecture

`say.py` exposes importable functions used by both the CLI and MCP server:
- `find_piper()` — Returns piper binary path or None
- `list_voices()` — Returns list of dicts with name/path/full_path
- `get_model_path(voice_name)` — Returns (model_path, config_path) tuple
- `synthesize(text, voice, rate, output)` — Core synthesis, returns status dict
- `print_voices()` — CLI wrapper that prints list_voices() output
- `main()` — CLI entry point

The MCP server (`mcp_server.py`) imports from `say.py` directly — no duplication.

## Development

### Running tests

```bash
# All tests (unit + integration)
python3 -m pytest test_say.py -v

# Unit tests only (mocked, fast)
python3 -m pytest test_say.py -v -k "not Integration"

# Integration tests only (requires piper + voices installed)
python3 -m pytest test_say.py -v -k "Integration"
```

### Key paths

- Piper venv: `/opt/piper-tts`
- Voice models: `~/.local/share/say4linux/models/` (or `$SAY4LINUX_MODELS`)
- MCP venv: `./mcp_venv/` (gitignored, created by setup-mcp.sh)
- Install location: `~/.local/share/say4linux/say.py` with symlink at `~/.local/bin/say`

### Voice naming

Voices follow `LANG-SPEAKER-QUALITY` (e.g. `en_US-amy-medium`). Directory structure under models/ is `LANG/SPEAKER/QUALITY/`. Some model dirs have an extra `en/` parent directory — `get_model_path()` handles this via substring matching.
