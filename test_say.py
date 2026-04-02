#!/usr/bin/env python3
"""Unit tests for say4linux."""
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure say.py is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import say


class TestFindPiper(unittest.TestCase):
    """Tests for find_piper()."""

    @patch("os.path.exists", return_value=True)
    def test_finds_venv_piper(self, mock_exists):
        result = say.find_piper()
        self.assertEqual(result, say.PIPER_BIN)

    @patch("os.path.exists", return_value=False)
    @patch("shutil.which", return_value="/usr/bin/piper")
    def test_falls_back_to_path(self, mock_which, mock_exists):
        result = say.find_piper()
        self.assertEqual(result, "/usr/bin/piper")

    @patch("os.path.exists", return_value=False)
    @patch("shutil.which", return_value=None)
    def test_returns_none_when_not_found(self, mock_which, mock_exists):
        result = say.find_piper()
        self.assertIsNone(result)


class TestListVoices(unittest.TestCase):
    """Tests for list_voices()."""

    @patch("say.MODEL_DIRS", ["/nonexistent/path"])
    def test_returns_empty_for_missing_dirs(self):
        voices = say.list_voices()
        self.assertEqual(voices, [])

    def test_returns_list_of_dicts(self):
        voices = say.list_voices()
        self.assertIsInstance(voices, list)
        if voices:
            self.assertIn("name", voices[0])
            self.assertIn("path", voices[0])
            self.assertIn("full_path", voices[0])

    def test_voice_names_are_strings(self):
        voices = say.list_voices()
        for v in voices:
            self.assertIsInstance(v["name"], str)
            self.assertIsInstance(v["path"], str)


class TestPrintVoices(unittest.TestCase):
    """Tests for print_voices()."""

    @patch("say.list_voices", return_value=[
        {"name": "en_US-amy-medium", "path": "en_US/amy/medium/en_US-amy-medium.onnx",
         "full_path": "/models/en_US/amy/medium/en_US-amy-medium.onnx"},
    ])
    def test_prints_voices(self, mock_list):
        with patch("builtins.print") as mock_print:
            say.print_voices()
            mock_print.assert_any_call("Available voices:")
            mock_print.assert_any_call("  en_US-amy-medium: en_US/amy/medium/en_US-amy-medium.onnx")

    @patch("say.list_voices", return_value=[])
    def test_prints_no_models_message(self, mock_list):
        with patch("builtins.print") as mock_print:
            say.print_voices()
            mock_print.assert_called_once_with(
                "No models found. Run download-voices.sh to get started.",
                file=sys.stderr
            )


class TestGetModelPath(unittest.TestCase):
    """Tests for get_model_path()."""

    def test_full_onnx_path_returned_directly(self):
        model, config = say.get_model_path("/path/to/voice.onnx")
        self.assertEqual(model, "/path/to/voice.onnx")
        self.assertEqual(config, "/path/to/voice.onnx.json")

    @patch("say.MODEL_DIRS", ["/nonexistent"])
    def test_returns_none_for_unknown_voice(self):
        model, config = say.get_model_path("nonexistent-voice-xyz")
        self.assertIsNone(model)
        self.assertIsNone(config)

    def test_finds_installed_voice(self):
        """If any voices are installed, we should be able to find one by filename stem."""
        voices = say.list_voices()
        if not voices:
            self.skipTest("No voices installed")
        # Extract voice name from the onnx filename (e.g. en_US-amy-medium from en_US-amy-medium.onnx)
        onnx_file = os.path.basename(voices[0]["full_path"])
        voice_name = onnx_file.replace(".onnx", "")
        model, config = say.get_model_path(voice_name)
        self.assertIsNotNone(model)
        self.assertTrue(model.endswith(".onnx"))
        self.assertTrue(config.endswith(".json"))


class TestSynthesize(unittest.TestCase):
    """Tests for synthesize()."""

    @patch("say.find_piper", return_value=None)
    def test_error_when_piper_missing(self, mock_find):
        result = say.synthesize("hello")
        self.assertEqual(result["status"], "error")
        self.assertIn("piper", result["error"])

    @patch("say.find_piper", return_value="/usr/bin/piper")
    @patch("say.get_model_path", return_value=(None, None))
    def test_error_when_voice_not_found(self, mock_model, mock_piper):
        result = say.synthesize("hello", voice="nonexistent-voice")
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["error"])

    def test_rate_zero_returns_error(self):
        result = say.synthesize("hello", rate=0)
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid rate", result["error"])

    def test_rate_negative_returns_error(self):
        result = say.synthesize("hello", rate=-1)
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid rate", result["error"])

    def test_rate_too_high_returns_error(self):
        result = say.synthesize("hello", rate=11)
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid rate", result["error"])

    def test_rate_valid_edges_accepted(self):
        """Rates 0.1 and 10.0 should pass validation (may fail later without piper)."""
        for rate in [0.1, 0.5, 2.0, 10.0]:
            result = say.synthesize("hello", rate=rate)
            # Should get past rate validation — error will be about piper or voice, not rate
            if result["status"] == "error":
                self.assertNotIn("Invalid rate", result["error"])

    @patch("say.find_piper", return_value="/usr/bin/piper")
    @patch("say.get_model_path", return_value=("/models/voice.onnx", "/models/voice.onnx.json"))
    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_synthesize_to_file(self, mock_run, mock_exists, mock_model, mock_piper):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        try:
            result = say.synthesize("hello", output=output_path)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["wav_path"], output_path)
            # Verify piper was called with correct args
            cmd = mock_run.call_args[0][0]
            self.assertIn("--model", cmd)
            self.assertIn("--output_file", cmd)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("say.find_piper", return_value="/usr/bin/piper")
    @patch("say.get_model_path", return_value=("/models/voice.onnx", "/models/voice.onnx.json"))
    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_synthesize_with_rate(self, mock_run, mock_exists, mock_model, mock_piper):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        try:
            say.synthesize("hello", rate=2.0, output=output_path)
            cmd = mock_run.call_args[0][0]
            self.assertIn("--length_scale", cmd)
            scale_idx = cmd.index("--length_scale")
            self.assertEqual(cmd[scale_idx + 1], str(1.0 / 2.0))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("say.find_piper", return_value="/usr/bin/piper")
    @patch("say.get_model_path", return_value=("/models/voice.onnx", "/models/voice.onnx.json"))
    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_piper_failure_returns_error(self, mock_run, mock_exists, mock_model, mock_piper):
        mock_run.return_value = MagicMock(returncode=1, stderr="some piper error")
        result = say.synthesize("hello", output="/tmp/test.wav")
        self.assertEqual(result["status"], "error")
        self.assertIn("piper failed", result["error"])

    @patch("say.find_piper", return_value="/usr/bin/piper")
    @patch("say.get_model_path", return_value=("/models/voice.onnx", "/models/voice.onnx.json"))
    @patch("os.path.exists", return_value=True)
    @patch("shutil.which", return_value="/usr/bin/paplay")
    @patch("subprocess.run")
    def test_synthesize_plays_audio(self, mock_run, mock_which, mock_exists, mock_model, mock_piper):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = say.synthesize("hello")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result.get("played"))
        # Should have been called twice: once for piper, once for player
        self.assertEqual(mock_run.call_count, 2)

    @patch("say.find_piper", return_value="/usr/bin/piper")
    @patch("say.get_model_path", return_value=("/models/voice.onnx", "/models/voice.onnx.json"))
    @patch("os.path.exists", return_value=True)
    @patch("shutil.which", return_value=None)
    @patch("subprocess.run")
    def test_warning_when_no_player(self, mock_run, mock_which, mock_exists, mock_model, mock_piper):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = say.synthesize("hello")
        self.assertEqual(result["status"], "ok")
        self.assertIn("warning", result)
        self.assertIn("No audio player", result["warning"])


class TestGetText(unittest.TestCase):
    """Tests for get_text()."""

    def test_text_from_args(self):
        args = MagicMock()
        args.text = ["hello", "world"]
        result = say.get_text(args)
        self.assertEqual(result, "hello world")

    def test_exits_when_no_text_and_tty(self):
        args = MagicMock()
        args.text = []
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with self.assertRaises(SystemExit):
                say.get_text(args)


def piper_available():
    """Check if piper is installed and at least one voice exists."""
    return say.find_piper() is not None and len(say.list_voices()) > 0


@unittest.skipUnless(piper_available(), "piper not installed or no voices available")
class TestSynthesizeIntegration(unittest.TestCase):
    """Integration tests that run real piper synthesis and produce actual audio."""

    def setUp(self):
        self.output_dir = tempfile.mkdtemp(prefix="say4linux_test_")
        voices = say.list_voices()
        # Pick the first voice by its onnx filename stem (matches get_model_path logic)
        onnx = os.path.basename(voices[0]["full_path"])
        self.voice = onnx.replace(".onnx", "")

    def tearDown(self):
        import shutil as _shutil
        _shutil.rmtree(self.output_dir, ignore_errors=True)

    def _wav_path(self, name):
        return os.path.join(self.output_dir, name)

    def test_synthesize_creates_wav_file(self):
        wav = self._wav_path("basic.wav")
        result = say.synthesize("Hello from say4linux integration test.", voice=self.voice, output=wav)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.exists(wav), "WAV file was not created")
        self.assertGreater(os.path.getsize(wav), 1000, "WAV file is suspiciously small")

    def test_synthesize_wav_has_valid_header(self):
        wav = self._wav_path("header.wav")
        say.synthesize("Testing WAV header.", voice=self.voice, output=wav)
        with open(wav, "rb") as f:
            header = f.read(4)
        self.assertEqual(header, b"RIFF", "File does not have a valid WAV/RIFF header")

    def test_synthesize_with_slow_rate(self):
        wav_normal = self._wav_path("normal.wav")
        wav_slow = self._wav_path("slow.wav")
        text = "Rate comparison test."
        say.synthesize(text, voice=self.voice, rate=1.0, output=wav_normal)
        say.synthesize(text, voice=self.voice, rate=0.5, output=wav_slow)
        # Slower rate should produce a larger (longer) WAV file
        normal_size = os.path.getsize(wav_normal)
        slow_size = os.path.getsize(wav_slow)
        self.assertGreater(slow_size, normal_size, "Slow rate should produce longer audio")

    def test_synthesize_with_fast_rate(self):
        wav_normal = self._wav_path("normal2.wav")
        wav_fast = self._wav_path("fast.wav")
        text = "Rate comparison test."
        say.synthesize(text, voice=self.voice, rate=1.0, output=wav_normal)
        say.synthesize(text, voice=self.voice, rate=2.0, output=wav_fast)
        normal_size = os.path.getsize(wav_normal)
        fast_size = os.path.getsize(wav_fast)
        self.assertLess(fast_size, normal_size, "Fast rate should produce shorter audio")

    def test_synthesize_long_text(self):
        wav = self._wav_path("long.wav")
        long_text = "This is a longer sentence to test that piper can handle more than just a few words. " * 3
        result = say.synthesize(long_text, voice=self.voice, output=wav)
        self.assertEqual(result["status"], "ok")
        self.assertGreater(os.path.getsize(wav), 5000, "Long text should produce substantial audio")

    def test_synthesize_bad_voice_returns_error(self):
        wav = self._wav_path("bad_voice.wav")
        result = say.synthesize("hello", voice="totally_fake_voice_xyz", output=wav)
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["error"])
        self.assertFalse(os.path.exists(wav) and os.path.getsize(wav) > 0)

    def test_keep_flag_preserves_temp_wav(self):
        result = say.synthesize(
            "Keep flag test.", voice=self.voice, keep=True
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("wav_path", result)
        self.assertTrue(os.path.exists(result["wav_path"]), "WAV should still exist with keep=True")
        # Clean up manually
        os.unlink(result["wav_path"])


class TestMain(unittest.TestCase):
    """Tests for main() via subprocess — validates CLI arg handling."""

    def _run_say(self, *args):
        """Run say.py as a subprocess and return (returncode, stdout, stderr)."""
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "say.py")] + list(args),
            capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout, result.stderr

    def test_list_voices(self):
        rc, stdout, stderr = self._run_say("-v", "list")
        self.assertEqual(rc, 0)
        # Should print voice names or "No models found"
        self.assertTrue("voices" in stdout.lower() or "no models" in stderr.lower())

    def test_bad_voice_exits_with_error(self):
        rc, stdout, stderr = self._run_say("-v", "totally_fake_xyz", "hello")
        self.assertNotEqual(rc, 0)
        self.assertIn("not found", stderr.lower())

    def test_no_text_no_tty_exits_cleanly(self):
        """When stdin is not a tty and empty (subprocess), exits 0 with no output."""
        rc, stdout, stderr = self._run_say()
        self.assertEqual(rc, 0)

    def test_invalid_rate_zero(self):
        rc, stdout, stderr = self._run_say("-r", "0", "hello")
        self.assertNotEqual(rc, 0)
        self.assertIn("rate", stderr.lower())

    def test_invalid_rate_negative(self):
        rc, stdout, stderr = self._run_say("-r", "-1", "hello")
        self.assertNotEqual(rc, 0)
        self.assertIn("rate", stderr.lower())


@unittest.skipUnless(piper_available(), "piper not installed or no voices available")
class TestMainIntegration(unittest.TestCase):
    """Integration tests for main() that produce real audio."""

    def _run_say(self, *args):
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "say.py")] + list(args),
            capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout, result.stderr

    def test_output_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav = f.name
        try:
            rc, stdout, stderr = self._run_say("-o", wav, "Output test")
            self.assertEqual(rc, 0)
            self.assertIn("Audio saved to", stdout)
            self.assertGreater(os.path.getsize(wav), 100)
        finally:
            if os.path.exists(wav):
                os.unlink(wav)

    def test_keep_flag_prints_path(self):
        rc, stdout, stderr = self._run_say("--keep", "Keep test")
        self.assertEqual(rc, 0)
        self.assertIn("Audio saved to", stdout)


class TestMCPTools(unittest.TestCase):
    """Tests for MCP server tool functions."""

    @classmethod
    def setUpClass(cls):
        # Import MCP tools — add mcp_venv to path if needed, skip if unavailable
        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
            venv_site = os.path.join(project_dir, "mcp_venv", "lib")
            if os.path.isdir(venv_site):
                # Find the python3.x site-packages dir inside the venv
                for d in os.listdir(venv_site):
                    sp = os.path.join(venv_site, d, "site-packages")
                    if os.path.isdir(sp) and sp not in sys.path:
                        sys.path.insert(0, sp)
            if project_dir not in sys.path:
                sys.path.insert(0, project_dir)
            from mcp_server import say as mcp_say, list_available_voices, save_audio
            from mcp.server.fastmcp.exceptions import ToolError
            cls.mcp_say = staticmethod(mcp_say)
            cls.list_available_voices = staticmethod(list_available_voices)
            cls.save_audio = staticmethod(save_audio)
            cls.ToolError = ToolError
        except ImportError:
            raise unittest.SkipTest("mcp package not installed — run setup-mcp.sh")

    @patch("mcp_server.synthesize", return_value={"status": "error", "error": "Voice 'bad' not found"})
    def test_say_raises_tool_error_on_failure(self, mock_synth):
        with self.assertRaises(self.ToolError):
            self.mcp_say("hello", voice="bad")

    @patch("mcp_server.synthesize", return_value={"status": "ok", "played": True})
    def test_say_returns_spoke_on_success(self, mock_synth):
        result = self.mcp_say("hello world")
        self.assertIn("Spoke", result)

    @patch("mcp_server.list_voices", return_value=[])
    def test_list_voices_raises_on_empty(self, mock_list):
        with self.assertRaises(self.ToolError):
            self.list_available_voices()

    @patch("mcp_server.list_voices", return_value=[
        {"name": "en_US-amy-medium", "path": "en_US/amy/medium/voice.onnx",
         "full_path": "/secret/path/voice.onnx"},
    ])
    def test_list_voices_strips_full_path(self, mock_list):
        result = self.list_available_voices()
        self.assertEqual(len(result), 1)
        self.assertIn("name", result[0])
        self.assertIn("path", result[0])
        self.assertNotIn("full_path", result[0])

    @patch("mcp_server.synthesize", return_value={"status": "error", "error": "piper failed"})
    def test_save_audio_raises_tool_error_on_failure(self, mock_synth):
        with self.assertRaises(self.ToolError):
            self.save_audio("hello", "/tmp/test.wav")

    @patch("mcp_server.synthesize", return_value={"status": "ok", "wav_path": "/tmp/out.wav"})
    def test_save_audio_returns_path_on_success(self, mock_synth):
        result = self.save_audio("hello", "/tmp/out.wav")
        self.assertIn("/tmp/out.wav", result)


if __name__ == "__main__":
    unittest.main()
