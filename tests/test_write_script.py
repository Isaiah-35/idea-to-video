"""Unit tests for write_script.py"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from write_script import write_script, STYLES


def _mock_claude(response_text: str):
    content = MagicMock()
    content.text = f"  {response_text}  "  # extra whitespace to test strip()
    message = MagicMock()
    message.content = [content]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def test_write_script_returns_string(sample_topics, sample_script):
    mock_client = _mock_claude(sample_script)
    with patch("write_script.Anthropic", return_value=mock_client):
        result = write_script(sample_topics)
    assert isinstance(result, str)
    assert len(result) > 0


def test_write_script_strips_whitespace(sample_topics, sample_script):
    mock_client = _mock_claude(sample_script)
    with patch("write_script.Anthropic", return_value=mock_client):
        result = write_script(sample_topics)
    assert result == result.strip()


def test_write_script_passes_style(sample_topics, sample_script):
    mock_client = _mock_claude(sample_script)
    with patch("write_script.Anthropic", return_value=mock_client):
        write_script(sample_topics, style="formal")
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "formal" in prompt


def test_write_script_zh_lang(sample_topics, sample_script):
    mock_client = _mock_claude(sample_script)
    with patch("write_script.Anthropic", return_value=mock_client):
        write_script(sample_topics, lang="zh")
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Chinese" in prompt


def test_write_script_includes_topic_titles(sample_topics, sample_script):
    mock_client = _mock_claude(sample_script)
    with patch("write_script.Anthropic", return_value=mock_client):
        write_script(sample_topics)
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    for topic in sample_topics:
        assert topic["title"] in prompt


def test_styles_list_not_empty():
    assert len(STYLES) > 0
    assert "conversational" in STYLES
