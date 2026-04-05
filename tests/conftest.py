"""Shared fixtures for the test suite."""
import json
import numpy as np
import pytest


SAMPLE_TRANSCRIPT = (
    "Today we discussed three main ideas: the importance of sleep for memory consolidation, "
    "how exercise changes brain chemistry, and why social connection is a biological need."
)

SAMPLE_TOPICS = [
    {
        "title": "Sleep and Memory",
        "summary": "Sleep is essential for consolidating memories formed during the day.",
        "image_prompt": "Person sleeping peacefully, brain activity visualization",
    },
    {
        "title": "Exercise and Brain Chemistry",
        "summary": "Physical exercise releases dopamine and serotonin, improving mood and cognition.",
        "image_prompt": "Person running outdoors, brain with chemical symbols",
    },
]

SAMPLE_SCRIPT = (
    "Good sleep isn't a luxury — it's when your brain sorts and stores everything you learned. "
    "Exercise rewires your brain chemistry in ways no pill can replicate. "
    "And humans aren't wired to be alone: connection is as biological as hunger."
)


@pytest.fixture
def sample_transcript():
    return SAMPLE_TRANSCRIPT


@pytest.fixture
def sample_topics():
    return SAMPLE_TOPICS


@pytest.fixture
def sample_topics_json():
    return json.dumps(SAMPLE_TOPICS, indent=2)


@pytest.fixture
def sample_script():
    return SAMPLE_SCRIPT


@pytest.fixture
def silent_wav(tmp_path):
    """Write a 1-second silent WAV and return its path."""
    import soundfile as sf
    path = tmp_path / "silent.wav"
    sf.write(str(path), np.zeros(24000, dtype=np.float32), 24000)
    return path


@pytest.fixture
def tiny_jpg(tmp_path):
    """Write a minimal JPEG (1×1 red pixel) and return its path."""
    from PIL import Image
    path = tmp_path / "img001.jpg"
    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(str(path))
    return path
