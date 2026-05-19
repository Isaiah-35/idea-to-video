"""Unit tests for extract_topics.py"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract_topics import extract_topics, _parse_json


def _mock_claude(response_text: str):
    """Build a mock Anthropic client that returns response_text."""
    content = MagicMock()
    content.text = response_text
    message = MagicMock()
    message.content = [content]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def test_extract_topics_returns_list(sample_transcript, sample_topics):
    mock_client = _mock_claude(json.dumps(sample_topics))
    with patch("extract_topics.Anthropic", return_value=mock_client):
        result = extract_topics(sample_transcript)
    assert isinstance(result, list)
    assert len(result) == len(sample_topics)


def test_extract_topics_fields(sample_transcript, sample_topics):
    mock_client = _mock_claude(json.dumps(sample_topics))
    with patch("extract_topics.Anthropic", return_value=mock_client):
        result = extract_topics(sample_transcript)
    for topic in result:
        assert "title" in topic
        assert "summary" in topic
        assert "image_prompt" in topic


def test_extract_topics_passes_num_topics(sample_transcript, sample_topics):
    mock_client = _mock_claude(json.dumps(sample_topics[:1]))
    with patch("extract_topics.Anthropic", return_value=mock_client):
        extract_topics(sample_transcript, num_topics=1)
    call_args = mock_client.messages.create.call_args
    prompt = call_args.kwargs["messages"][0]["content"]
    assert "1" in prompt


def test_extract_topics_zh_lang(sample_transcript, sample_topics):
    mock_client = _mock_claude(json.dumps(sample_topics))
    with patch("extract_topics.Anthropic", return_value=mock_client):
        extract_topics(sample_transcript, lang="zh")
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Chinese" in prompt


def test_extract_topics_invalid_json_raises(sample_transcript):
    mock_client = _mock_claude("not valid json at all")
    with patch("extract_topics.Anthropic", return_value=mock_client):
        with pytest.raises(ValueError):
            extract_topics(sample_transcript)


# ── _parse_json (fence-stripping) ─────────────────────────────────────────────

def test_parse_json_plain(sample_topics):
    raw = json.dumps(sample_topics)
    assert _parse_json(raw) == sample_topics


def test_parse_json_with_json_fence(sample_topics):
    """Claude's actual response format — code fence must be stripped."""
    raw = f"```json\n{json.dumps(sample_topics)}\n```"
    assert _parse_json(raw) == sample_topics


def test_parse_json_with_plain_fence(sample_topics):
    raw = f"```\n{json.dumps(sample_topics)}\n```"
    assert _parse_json(raw) == sample_topics


def test_parse_json_with_extra_whitespace(sample_topics):
    raw = f"  ```json\n{json.dumps(sample_topics)}\n```  "
    assert _parse_json(raw.strip()) == sample_topics


def test_extract_topics_handles_fenced_response(sample_transcript, sample_topics):
    """Realistic mock: Claude returns JSON wrapped in a markdown code fence."""
    fenced = f"```json\n{json.dumps(sample_topics)}\n```"
    mock_client = _mock_claude(fenced)
    with patch("extract_topics.Anthropic", return_value=mock_client):
        result = extract_topics(sample_transcript)
    assert result == sample_topics
