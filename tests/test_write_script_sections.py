"""Unit tests for write_script_sections."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from write_script import write_script_sections


def _mock_claude(sections: list[str]):
    content = MagicMock()
    content.text = json.dumps(sections)
    message = MagicMock()
    message.content = [content]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def test_sections_count_matches_topics(sample_topics):
    mock_client = _mock_claude(["Section one.", "Section two."])
    with patch("write_script.Anthropic", return_value=mock_client):
        result = write_script_sections(sample_topics[:2])
    assert len(result) == 2


def test_sections_are_strings(sample_topics):
    mock_client = _mock_claude(["First section.", "Second section."])
    with patch("write_script.Anthropic", return_value=mock_client):
        result = write_script_sections(sample_topics[:2])
    for s in result:
        assert isinstance(s, str)


def test_sections_strips_whitespace(sample_topics):
    mock_client = _mock_claude(["  Section one.  ", "  Section two.  "])
    with patch("write_script.Anthropic", return_value=mock_client):
        result = write_script_sections(sample_topics[:2])
    for s in result:
        assert s == s.strip()


def test_sections_handles_fenced_json(sample_topics):
    sections = ["Section one.", "Section two."]
    content = MagicMock()
    content.text = f"```json\n{json.dumps(sections)}\n```"
    message = MagicMock()
    message.content = [content]
    client = MagicMock()
    client.messages.create.return_value = message
    with patch("write_script.Anthropic", return_value=client):
        result = write_script_sections(sample_topics[:2])
    assert result == sections


def test_sections_prompt_includes_topic_count(sample_topics):
    mock_client = _mock_claude(["S1.", "S2."])
    with patch("write_script.Anthropic", return_value=mock_client):
        write_script_sections(sample_topics[:2])
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "2" in prompt


def test_sections_brand_prefix_injected(sample_topics):
    brand = {"name": "TestBrand", "audience": "", "tone": "", "style_notes": ""}
    mock_client = _mock_claude(["S1.", "S2."])
    with patch("write_script.Anthropic", return_value=mock_client):
        write_script_sections(sample_topics[:2], brand=brand)
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "TestBrand" in prompt
