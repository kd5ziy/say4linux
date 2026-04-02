# Code Review

## Remaining Tasks

1. Align the rate validation bounds with the documented behavior.
   Files: `say.py`, `mcp_server.py`, `test_say.py`
   Problem: the code accepts values below `0.1` because it only rejects `<= 0`, but the error text and tests describe the valid range as `0.1` to `10.0`.
   Change: either reject rates below `0.1`, or update the code comments, CLI help text, MCP docstrings, and tests to match the intended lower bound.

2. Add shell-script coverage if script reliability matters for this repo.
   Files: `install.sh`, `download-voices.sh`, `setup-mcp.sh`, `sample-voices.sh`, `uninstall.sh`
   Problem: the earlier review item about broader coverage is only partially complete. The test suite now covers CLI and MCP behavior, but not the shell scripts users run directly.
   Change: add lightweight validation or smoke tests for the maintained scripts, or explicitly decide that script testing is out of scope.
