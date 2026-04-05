"""Integration tests for make_video.sh (requires ffmpeg on PATH)."""
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

SCRIPT = Path(__file__).parent.parent / "make_video.sh"


@pytest.fixture
def audio_5s(tmp_path):
    """5-second silent WAV file."""
    import soundfile as sf
    path = tmp_path / "audio.wav"
    sf.write(str(path), np.zeros(5 * 24000, dtype=np.float32), 24000)
    return path


@pytest.fixture
def image_dir(tmp_path):
    """Directory with 3 minimal JPEGs."""
    from PIL import Image
    d = tmp_path / "imgs"
    d.mkdir()
    for i in range(1, 4):
        Image.new("RGB", (320, 240), color=(i * 60, 100, 150)).save(str(d / f"img{i:03d}.jpg"))
    return d


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_make_video_produces_mp4(tmp_path, audio_5s, image_dir):
    out = tmp_path / "output.mp4"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(image_dir), str(audio_5s), str(out)],
        capture_output=True, text=True,
    )
    assert out.exists(), f"No output file.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert out.stat().st_size > 1000


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_make_video_fails_gracefully_no_images(tmp_path, audio_5s):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    out = tmp_path / "output.mp4"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(empty_dir), str(audio_5s), str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "No images" in result.stdout or "No images" in result.stderr


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_make_video_fails_gracefully_bad_audio(tmp_path, image_dir):
    bad_audio = tmp_path / "bad.wav"
    bad_audio.write_text("not audio")
    out = tmp_path / "output.mp4"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(image_dir), str(bad_audio), str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
