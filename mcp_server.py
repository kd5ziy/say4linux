#!/usr/bin/env python3
"""
say4linux MCP Server — Exposes text-to-speech as MCP tools.

Tools:
  - say: Speak text aloud on the host machine
  - list_available_voices: List installed voice models
  - save_audio: Synthesize text to a WAV file

Setup:
  bash setup-mcp.sh
  # Then open this project in Claude Code — it auto-discovers .mcp.json

Or register globally:
  claude mcp add -s user say4linux ./mcp_venv/bin/python ./mcp_server.py
"""
import sys
import os

# Ensure say.py can be imported from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from say import list_voices, synthesize

mcp = FastMCP("say4linux")


@mcp.tool()
def say(text: str, voice: str = "en_US-amy-medium", rate: float = 1.0) -> str:
    """Speak text aloud using text-to-speech. Audio plays on the host machine.

    Args:
        text: The text to speak aloud
        voice: Voice model name (e.g. en_US-amy-medium, en_GB-alba-medium).
               Use list_available_voices to see installed voices.
        rate: Speaking rate from 0.5 (slow) to 2.0 (fast). Default 1.0.
    """
    result = synthesize(text, voice=voice, rate=rate)
    if result["status"] == "error":
        return f"Error: {result['error']}"
    if result.get("warning"):
        return f"Warning: {result['warning']}"
    return f"Spoke: {text[:100]}{'...' if len(text) > 100 else ''}"


@mcp.tool()
def list_available_voices() -> list[dict]:
    """List all installed text-to-speech voices.

    Returns voice names and paths. Voices follow the pattern
    LANG-SPEAKER-QUALITY (e.g. en_US-amy-medium, en_GB-alba-medium).

    Quality levels:
      - low: fastest synthesis, lower quality
      - medium: good balance (recommended)
      - high: best quality, slower synthesis
    """
    voices = list_voices()
    if not voices:
        return [{"error": "No voices installed. Run download-voices.sh to install voices."}]
    return voices


@mcp.tool()
def save_audio(
    text: str,
    output_path: str,
    voice: str = "en_US-amy-medium",
    rate: float = 1.0,
) -> str:
    """Synthesize text to a WAV audio file without playing it.

    Args:
        text: The text to synthesize
        output_path: File path where the WAV file should be saved
        voice: Voice model name (e.g. en_US-amy-medium)
        rate: Speaking rate from 0.5 (slow) to 2.0 (fast). Default 1.0.
    """
    result = synthesize(text, voice=voice, rate=rate, output=output_path)
    if result["status"] == "error":
        return f"Error: {result['error']}"
    return f"Audio saved to: {result['wav_path']}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
