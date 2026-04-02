#!/usr/bin/env python3
"""Unit tests for say4linux."""
import os
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


if __name__ == "__main__":
    unittest.main()
