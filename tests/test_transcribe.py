"""Unit tests for transcribe.py"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from transcribe import transcribe


def test_transcribe_writes_txt_file(tmp_path, silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "  hello world  "}

    with patch("transcribe.whisper.load_model", return_value=mock_model):
        result = transcribe(silent_wav, output_dir=tmp_path)

    assert result == "hello world"
    out_file = tmp_path / f"{silent_wav.stem}.txt"
    assert out_file.exists()
    assert out_file.read_text() == "hello world"


def test_transcribe_passes_language(tmp_path, silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "你好"}

    with patch("transcribe.whisper.load_model", return_value=mock_model):
        transcribe(silent_wav, language="zh", output_dir=tmp_path)

    mock_model.transcribe.assert_called_once_with(
        str(silent_wav), language="zh", fp16=False
    )


def test_transcribe_default_output_dir(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(b"")  # dummy file

    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "test"}

    with patch("transcribe.whisper.load_model", return_value=mock_model):
        transcribe(wav)

    assert (tmp_path / "audio.txt").exists()


def test_transcribe_uses_requested_model(tmp_path, silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "x"}

    with patch("transcribe.whisper.load_model", return_value=mock_model) as mock_load:
        transcribe(silent_wav, model_name="small", output_dir=tmp_path)

    mock_load.assert_called_once_with("small")
