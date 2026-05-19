"""Functional tests: app handler functions called directly (no browser)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import app functions without launching Gradio
import app as _app

_EMPTY_BRAND = ("", "", "", "")   # b_name, b_aud, b_tone, b_style
_EMPTY_PP    = ("", "", "", "")   # pp_goal, pp_aud, pp_emo, pp_cta


# ── run_transcribe ────────────────────────────────────────────────────────────

def test_run_transcribe_no_audio():
    result = _app.run_transcribe(None, "auto", "base", "", "", "", False)
    assert "Record or upload" in result


def test_run_transcribe_with_file(silent_wav):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "hello world", "segments": []}
    with patch("transcribe._BACKEND", "whisper"), \
         patch("transcribe.whisper.load_model", return_value=mock_model):
        result = _app.run_transcribe(str(silent_wav), "auto", "base", "", "", "", False)
    assert result == "hello world"


# ── run_extract_topics ────────────────────────────────────────────────────────

def test_run_extract_topics_empty_transcript():
    display, json_out = _app.run_extract_topics("", 5, "en", *_EMPTY_BRAND)
    assert "Paste" in display
    assert json_out == "[]"


def test_run_extract_topics_returns_display_and_json(sample_transcript, sample_topics):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(sample_topics))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("extract_topics.Anthropic", return_value=mock_client):
        display, json_out = _app.run_extract_topics(sample_transcript, 2, "en", *_EMPTY_BRAND)

    assert "Sleep and Memory" in display
    parsed = json.loads(json_out)
    assert len(parsed) == len(sample_topics)


# ── run_write_script ──────────────────────────────────────────────────────────

def test_run_write_script_invalid_json():
    full_script, sections_json, storyboard = _app.run_write_script("not json", "en", "conversational", *_EMPTY_BRAND)
    assert "Invalid" in full_script


def test_run_write_script_empty_list():
    full_script, sections_json, storyboard = _app.run_write_script("[]", "en", "conversational", *_EMPTY_BRAND)
    assert "No topics" in full_script


def test_run_write_script_success(sample_topics_json, sample_topics):
    sections = ["Section one.", "Section two."]
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(sections))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("write_script.Anthropic", return_value=mock_client):
        full_script, sections_json, storyboard = _app.run_write_script(
            sample_topics_json, "en", "conversational", *_EMPTY_BRAND)

    assert "Section one." in full_script
    assert "Section two." in full_script
    parsed = json.loads(sections_json)
    assert len(parsed) == 2
    assert "Slide 1" in storyboard  # storyboard HTML contains slide headers


# ── run_kokoro ────────────────────────────────────────────────────────────────

def test_run_kokoro_empty_text():
    audio, durations, info = _app.run_kokoro("", "[]", "en", "af_heart")
    assert audio is None
    assert "Enter" in info


def test_run_kokoro_generates_file():
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = [("", "", np.zeros(24000, dtype=np.float32))]
    with patch("kokoro_tts.KPipeline", return_value=mock_pipeline):
        audio_path, durations_path, info = _app.run_kokoro("Hello world", "[]", "en", "af_heart")
    assert audio_path is not None
    assert Path(audio_path).exists()
    assert "KB" in info


def test_run_kokoro_uses_sections():
    """When sections JSON is provided, generate_sections is called."""
    sections = ["Hello world.", "Goodbye world."]
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = [("", "", np.zeros(12000, dtype=np.float32))]
    with patch("kokoro_tts.KPipeline", return_value=mock_pipeline):
        audio_path, durations_path, info = _app.run_kokoro(
            "\n\n".join(sections), json.dumps(sections), "en", "af_heart"
        )
    assert audio_path is not None
    assert durations_path is not None
    assert "sections" in info


# ── run_make_video ────────────────────────────────────────────────────────────

def test_run_make_video_no_audio(tiny_jpg):
    video, log = _app.run_make_video(None, None, [str(tiny_jpg)], "[]")
    assert video is None
    assert "audio" in log.lower()


def test_run_make_video_no_images_no_topics(silent_wav):
    video, log = _app.run_make_video(str(silent_wav), None, [], "[]")
    assert video is None
    assert "image" in log.lower() or "topics" in log.lower()
