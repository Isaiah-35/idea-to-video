"""Unit tests for transcribe.py"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from transcribe import transcribe


# All tests force the whisper backend so they don't require a real audio file
# or a real WhisperX model. WhisperX integration is tested separately.
_WHISPER_BACKEND = "transcribe._BACKEND"


def test_transcribe_writes_txt_file(tmp_path, silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "  hello world  ", "segments": []}

    with patch(_WHISPER_BACKEND, "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model):
        result = transcribe(silent_wav, output_dir=tmp_path)

    assert result == "hello world"
    out_file = tmp_path / f"{silent_wav.stem}.txt"
    assert out_file.exists()
    assert out_file.read_text() == "hello world"


def test_transcribe_passes_language(tmp_path, silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "你好", "segments": []}

    with patch(_WHISPER_BACKEND, "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model):
        transcribe(silent_wav, language="zh", output_dir=tmp_path)

    mock_model.transcribe.assert_called_once_with(
        str(silent_wav), language="zh", fp16=False
    )


def test_transcribe_default_output_dir(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(b"")

    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "test", "segments": []}

    with patch(_WHISPER_BACKEND, "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model):
        transcribe(wav)

    assert (tmp_path / "audio.txt").exists()


def test_transcribe_uses_requested_model(tmp_path, silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "x", "segments": []}

    with patch(_WHISPER_BACKEND, "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model) as mock_load:
        transcribe(silent_wav, model_name="small", output_dir=tmp_path)

    mock_load.assert_called_once_with("small")


def test_transcribe_speaker_names_triggers_claude_label(tmp_path, silent_wav):
    """When speaker names given and no HF_TOKEN, Claude labeling is called."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Hello how are you I am fine", "segments": []}

    labeled = "[Paul]: Hello how are you\n[Sam]: I am fine"

    with patch(_WHISPER_BACKEND, "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model), \
         patch("transcribe._claude_label", return_value=labeled) as mock_label, \
         patch.dict("os.environ", {}, clear=False):
        # Ensure HF_TOKEN is absent so diarization path is skipped
        import os; os.environ.pop("HF_TOKEN", None)
        result = transcribe(silent_wav, output_dir=tmp_path,
                            speaker_names=["Paul", "Sam"], speaker_hints="Paul asks questions")

    mock_label.assert_called_once()
    assert "[Paul]:" in result
    assert "[Sam]:" in result


def test_transcribe_no_speaker_names_skips_labeling(tmp_path, silent_wav):
    """Without speaker names, plain text is returned unchanged."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "plain text here", "segments": []}

    with patch(_WHISPER_BACKEND, "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model), \
         patch("transcribe._claude_label") as mock_label:
        result = transcribe(silent_wav, output_dir=tmp_path)

    mock_label.assert_not_called()
    assert result == "plain text here"
