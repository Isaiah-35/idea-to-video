"""Unit tests for kokoro_tts.py"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from kokoro_tts import generate


def _mock_pipeline(audio_array=None):
    """Return (MockKPipeline class, mock instance). KPipeline(lang_code=x) → instance."""
    if audio_array is None:
        audio_array = np.zeros(24000, dtype=np.float32)
    instance = MagicMock()
    instance.return_value = [("", "", audio_array)]
    klass = MagicMock(return_value=instance)
    return klass, instance


def test_generate_creates_wav_file(tmp_path):
    out = tmp_path / "out.wav"
    klass, _ = _mock_pipeline()
    with patch("kokoro_tts.KPipeline", klass):
        generate("Hello world", out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_generate_default_en_voice(tmp_path):
    out = tmp_path / "out.wav"
    klass, instance = _mock_pipeline()
    with patch("kokoro_tts.KPipeline", klass):
        generate("Hello", out, lang="en")
    klass.assert_called_once_with(lang_code="a")
    instance.assert_called_once_with("Hello", voice="af_heart")


def test_generate_default_zh_voice(tmp_path):
    out = tmp_path / "out.wav"
    klass, instance = _mock_pipeline()
    with patch("kokoro_tts.KPipeline", klass):
        generate("你好", out, lang="zh")
    klass.assert_called_once_with(lang_code="z")
    instance.assert_called_once_with("你好", voice="zf_xiaobei")


def test_generate_custom_voice(tmp_path):
    out = tmp_path / "out.wav"
    klass, instance = _mock_pipeline()
    with patch("kokoro_tts.KPipeline", klass):
        generate("Hello", out, lang="en", voice="am_adam")
    instance.assert_called_once_with("Hello", voice="am_adam")


def test_generate_concatenates_chunks(tmp_path):
    out = tmp_path / "out.wav"
    chunk1 = np.ones(12000, dtype=np.float32)
    chunk2 = np.ones(12000, dtype=np.float32)
    instance = MagicMock()
    instance.return_value = [("", "", chunk1), ("", "", chunk2)]
    klass = MagicMock(return_value=instance)
    with patch("kokoro_tts.KPipeline", klass):
        with patch("kokoro_tts.sf.write") as mock_write:
            generate("Hello world", out)
    written_array = mock_write.call_args[0][1]
    assert len(written_array) == 24000
