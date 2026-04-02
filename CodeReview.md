# Code Review

## High Priority

1. **[FIXED]** Validate `rate` before building the Piper command.
   Files: `say.py:99-136`, `mcp_server.py:30-44`, `mcp_server.py:66-83`, `test_say.py`
   Problem: `synthesize()` does `1.0 / rate` with no guard. A value of `0` raises `ZeroDivisionError`, and negative values produce invalid `--length_scale` arguments. This affects both the CLI and the MCP server.
   Change: Reject non-positive rates in `synthesize()` or at argument parsing time, return a normal user-facing error, and add tests for `0`, negative, and out-of-range values.
   **Resolution:** Added `rate <= 0 or rate > 10` validation at the top of `synthesize()` returning an error dict. Added `valid_rate()` argparse type function in `main()` for CLI-side validation. Added 4 new unit tests: `test_rate_zero_returns_error`, `test_rate_negative_returns_error`, `test_rate_too_high_returns_error`, `test_rate_valid_edges_accepted`. Added 2 CLI tests: `test_invalid_rate_zero`, `test_invalid_rate_negative`.

2. **[FIXED]** Restore or remove the broken `--keep` behavior.
   Files: `say.py:120-151`, `say.py:173-195`, `README.md`
   Problem: `--keep` is still exposed in the CLI, but playback mode always deletes the temp WAV because `cleanup` is hard-coded to `True` and the flag is never passed into `synthesize()`.
   Change: Either thread a `keep` option into `synthesize()` and honor it, or remove the flag from the CLI and docs. Add a regression test for the chosen behavior.
   **Resolution:** Added `keep=False` parameter to `synthesize()`. When `keep=True` and no `output` specified, `cleanup` is set to `False` and `wav_path` is included in the return dict. Threaded `args.keep` through from `main()`. Added `elif args.keep` output message in `main()`. Added integration test `test_keep_flag_preserves_temp_wav` and CLI test `test_keep_flag_prints_path`.

3. **[FIXED]** Make MCP tool failures fail as tool errors instead of successful strings.
   Files: `mcp_server.py:39-44`, `mcp_server.py:80-83`
   Problem: the MCP tools return strings like `Error: ...` on failure, which means clients see a successful tool call with an error-looking payload. That is poor ergonomics for agents and programmatic consumers.
   Change: raise proper exceptions or use the MCP framework's error mechanism so failures propagate as actual tool errors. Add MCP-level tests for success and failure cases.
   **Resolution:** Imported `ToolError` from `mcp.server.fastmcp.exceptions`. All error paths now `raise ToolError(message)` instead of returning error strings. Added `TestMCPTools` test class with 6 tests covering success and failure for `say`, `list_available_voices`, and `save_audio`.

## Medium Priority

4. **[FIXED]** Stop returning absolute host paths from `list_available_voices`.
   Files: `say.py:49-66`, `mcp_server.py:47-62`
   Problem: the MCP response currently exposes `full_path` values from the local machine. Clients only need a stable voice identifier and perhaps the relative model path.
   Change: keep `full_path` internal to the Python module and return only public metadata from the MCP server.
   **Resolution:** `list_available_voices()` now returns `[{"name": v["name"], "path": v["path"]} for v in voices]`, stripping `full_path`. The `list_voices()` function in say.py is unchanged (internal callers may need full_path). Added test `test_list_voices_strips_full_path` verifying `full_path` is absent from MCP responses.

5. **[FIXED]** Repair or remove `GetAllUSUKModelVoices.sh`.
   Files: `GetAllUSUKModelVoices.sh:1-89`
   Problem: the file contains the script body twice, with the first copy running straight into a second pasted copy on line 45. Even if it is not part of the main flow, the checked-in helper is clearly malformed and hard to trust.
   Change: delete it if obsolete, or replace it with a single clean implementation and document its intended usage.
   **Resolution:** Deleted via `git rm`. The `download-voices.sh` script fully covers the same functionality with proper argument handling and help text.

6. **[FIXED]** Fix the `/say-test` skill so it matches its own contract.
   Files: `.claude/skills/say-test/SKILL.md:14-24`
   Problem: the skill text says the voice argument is optional and remaining words become sample text, but the command is just `say -v "$0" "$1"`. That drops most of the text, passes an empty voice when none is provided, and conflicts with `disable-model-invocation: true` plus the instruction to explain results afterward.
   Change: rewrite the command so defaults and argument handling actually work, and make the metadata consistent with the desired post-run behavior.
   **Resolution:** Rewrote the skill to instruct Claude to parse `$ARGUMENTS` — detect voice names by pattern (contains `en_US` or `en_GB`), default to `en_US-amy-medium`, default text to a sample sentence. Removed `disable-model-invocation: true` since the skill needs Claude to interpret arguments and explain results.

## Low Priority

7. **[FIXED]** Fix README inaccuracies and setup drift.
   Files: `README.md:61-68`, `README.md:226-232`
   Problem: the manual install snippet copies into `~/.local/share/say4linux/` without creating that directory first, and the skills section says the repo includes two skills while listing three.
   Change: add the missing `mkdir -p ~/.local/share/say4linux` step and update the skill count text.
   **Resolution:** Changed `mkdir -p ~/.local/bin` to `mkdir -p ~/.local/bin ~/.local/share/say4linux`. Changed "two" to "three" in the skills section text.

8. **[FIXED]** Expand test coverage beyond the happy path and direct function calls.
   Files: `test_say.py`, `mcp_server.py`, shell scripts
   Problem: the current test suite passes, but it does not exercise `main()`, MCP tool behavior, CLI argument validation, or shell-script flows. That is how the `--keep` regression slipped through.
   Change: add focused tests for the CLI entry point, MCP tool error handling, and any script behavior that the project expects users to rely on.
   **Resolution:** Added `TestMain` (5 tests: list voices, bad voice, no text, invalid rates via subprocess), `TestMainIntegration` (2 tests: output to file, keep flag via subprocess), and `TestMCPTools` (6 tests: success/failure for all 3 MCP tools, full_path stripping). Total test count went from 26 to 44, all passing.
