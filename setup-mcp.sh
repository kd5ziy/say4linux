#!/usr/bin/env bash
# Setup script for the say4linux MCP server.
# Creates a virtual environment and installs the MCP SDK.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/mcp_venv"

echo "=== say4linux MCP Server Setup ==="

# Create venv if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
    echo "[*] Creating virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
else
    echo "[*] Virtual environment already exists at ${VENV_DIR}"
fi

# Install/upgrade mcp package
echo "[*] Installing MCP SDK..."
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet "mcp[cli]"

echo ""
echo "[OK] MCP server is ready!"
echo ""
echo "=== How to use ==="
echo ""
echo "With Claude Code (project-local — auto-detected from .mcp.json):"
echo "  cd ${SCRIPT_DIR} && claude"
echo ""
echo "With Claude Code (global — works from any project):"
echo "  claude mcp add -s user say4linux ${VENV_DIR}/bin/python ${SCRIPT_DIR}/mcp_server.py"
echo ""
echo "With Claude Desktop (add to claude_desktop_config.json):"
echo "  {\"mcpServers\": {\"say4linux\": {\"command\": \"${VENV_DIR}/bin/python\", \"args\": [\"${SCRIPT_DIR}/mcp_server.py\"]}}}"
echo ""
echo "Test the server directly:"
echo "  ${VENV_DIR}/bin/python ${SCRIPT_DIR}/mcp_server.py"
