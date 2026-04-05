"""Integration tests: full pipeline from transcript to script (mocked LLM)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract_topics import extract_topics
from write_script import write_script


def _make_claude_mock(response_text: str):
    content = MagicMock()
    content.text = response_text
    message = MagicMock()
    message.content = [content]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def test_transcript_to_script_pipeline(sample_transcript, sample_topics, sample_script):
    """Topics extracted from transcript feed cleanly into write_script."""
    topics_json = json.dumps(sample_topics)

    with patch("extract_topics.Anthropic", return_value=_make_claude_mock(topics_json)):
        topics = extract_topics(sample_transcript, num_topics=2)

    with patch("write_script.Anthropic", return_value=_make_claude_mock(sample_script)):
        script = write_script(topics)

    assert isinstance(script, str)
    assert len(script) > 0


def test_pipeline_passes_lang_consistently(sample_transcript, sample_topics, sample_script):
    """Lang setting flows through both LLM calls."""
    topics_json = json.dumps(sample_topics)

    extract_mock = _make_claude_mock(topics_json)
    write_mock = _make_claude_mock(sample_script)

    with patch("extract_topics.Anthropic", return_value=extract_mock):
        topics = extract_topics(sample_transcript, lang="zh")

    with patch("write_script.Anthropic", return_value=write_mock):
        write_script(topics, lang="zh")

    extract_prompt = extract_mock.messages.create.call_args.kwargs["messages"][0]["content"]
    write_prompt = write_mock.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Chinese" in extract_prompt
    assert "Chinese" in write_prompt


def test_pipeline_topic_count_matches(sample_transcript):
    """Extracted topic count matches num_topics request."""
    topics_3 = [
        {"title": f"Topic {i}", "summary": "Summary.", "image_prompt": "img"}
        for i in range(3)
    ]
    mock_client = _make_claude_mock(json.dumps(topics_3))
    with patch("extract_topics.Anthropic", return_value=mock_client):
        result = extract_topics(sample_transcript, num_topics=3)
    assert len(result) == 3
