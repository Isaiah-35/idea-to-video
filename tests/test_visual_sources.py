"""Tests for visual_sources.py — Phase 3.5."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import visual_sources


# ── fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_SCENES = [
    {
        "title": "Sleep and Memory",
        "image_prompt": "Person sleeping peacefully brain activity visualization",
        "duration_s": 3.0,
    },
    {
        "title": "Exercise and Brain",
        "image_prompt": "Person running outdoors with brain visualization",
        "duration_s": 4.0,
    },
]


# ── test_generate_kenburns_creates_mp4 ────────────────────────────────────────

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_generate_kenburns_creates_mp4(tmp_path):
    """Ken Burns backend should produce a valid MP4 file for a single scene."""
    scene = SAMPLE_SCENES[0]
    result_path = visual_sources._kenburns_single(scene, 0, tmp_path, overwrite=True)
    out = Path(result_path)
    assert out.exists(), "Output MP4 not created"
    assert out.suffix == ".mp4"
    assert out.stat().st_size > 1000, "Output file is suspiciously small"


# ── test_acquire_visuals_pillow_fallback ──────────────────────────────────────

def test_acquire_visuals_pillow_fallback(tmp_path, monkeypatch):
    """Without API keys, pillow backend should be used and produce image files."""
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("FAL_KEY", raising=False)

    # Mock _auto_backend to return "pillow" directly
    monkeypatch.setattr(visual_sources, "_auto_backend", lambda: "pillow")

    result = visual_sources.acquire_visuals(
        [SAMPLE_SCENES[0]], tmp_path, backend="auto", overwrite=True
    )
    assert len(result) == 1
    assert result[0].get("visual_type") == "image"
    assert result[0].get("visual_path") is not None
    assert Path(result[0]["visual_path"]).exists()


# ── test_acquire_visuals_kenburns ─────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_acquire_visuals_kenburns(tmp_path):
    """Ken Burns backend should produce video files for all scenes."""
    result = visual_sources.acquire_visuals(
        SAMPLE_SCENES, tmp_path, backend="kenburns", overwrite=True
    )
    assert len(result) == len(SAMPLE_SCENES)
    for scene in result:
        assert scene.get("visual_type") == "video"
        assert scene.get("visual_path") is not None
        out = Path(scene["visual_path"])
        assert out.exists(), f"Expected output at {out}"
        assert out.suffix == ".mp4"
        assert out.stat().st_size > 1000


# ── test_acquire_visuals_pexels_fallback_on_empty_results ────────────────────

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_acquire_visuals_pexels_fallback_on_empty_results(tmp_path, monkeypatch):
    """When Pexels returns 0 results, should fall back to kenburns."""
    monkeypatch.setenv("PEXELS_API_KEY", "dummy_key")

    # Patch urlopen to return empty video list
    import urllib.request

    class _FakeResponse:
        def __init__(self):
            self._data = json.dumps({"videos": []}).encode()

        def read(self):
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse())

    result = visual_sources._acquire_pexels([SAMPLE_SCENES[0]], tmp_path, overwrite=True)
    assert len(result) == 1
    assert result[0].get("visual_type") == "video"
    # Should have fallen back to kenburns → .mp4
    out = Path(result[0]["visual_path"])
    assert out.suffix == ".mp4"
    assert out.exists()


# ── test_extract_keywords_removes_stop_words ─────────────────────────────────

def test_extract_keywords_removes_stop_words():
    """_extract_keywords should strip common stop words and return at most max_words."""
    prompt = "A person running in the park with a dog"
    result = visual_sources._extract_keywords(prompt, max_words=4)
    words = result.split()
    assert "a" not in words
    assert "in" not in words
    assert "the" not in words
    assert "with" not in words
    assert len(words) <= 4
    assert len(words) > 0


def test_extract_keywords_handles_empty():
    result = visual_sources._extract_keywords("", max_words=4)
    assert result == ""


def test_extract_keywords_max_words():
    prompt = "bright colorful vibrant abstract digital neon futuristic cityscape"
    result = visual_sources._extract_keywords(prompt, max_words=3)
    assert len(result.split()) <= 3


# ── test_detect_available_backends_no_keys ───────────────────────────────────

def test_detect_available_backends_no_keys(monkeypatch):
    """When no API keys are set, only kenburns and pillow should be available."""
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("FAL_KEY", raising=False)

    backends = visual_sources.detect_available_backends()
    assert backends["kenburns"] is True
    assert backends["pillow"] is True
    assert backends["pexels"] is False
    assert backends["fal"] is False


# ── test_detect_available_backends_pexels_set ────────────────────────────────

def test_detect_available_backends_pexels_set(monkeypatch):
    """When PEXELS_API_KEY is set, pexels should show as available."""
    monkeypatch.setenv("PEXELS_API_KEY", "test_key_12345")
    monkeypatch.delenv("FAL_KEY", raising=False)

    backends = visual_sources.detect_available_backends()
    assert backends["pexels"] is True
    assert backends["kenburns"] is True
    assert backends["pillow"] is True
    # fal still absent
    assert backends["fal"] is False


# ── test_assemble_video_image_mode ───────────────────────────────────────────

def test_assemble_video_image_mode(tmp_path):
    """Image mode should call make_video.sh via subprocess."""
    import assemble_video

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output = tmp_path / "output.mp4"

    # Create a tiny fake JPG image for each scene
    from PIL import Image
    img_path = tmp_path / "img.jpg"
    Image.new("RGB", (100, 100), color=(0, 128, 255)).save(str(img_path))

    scenes = [
        {"visual_path": str(img_path), "visual_type": "image", "duration_s": 2.0},
    ]

    # Mock subprocess.run so we don't need ffmpeg for this test
    fake_output = tmp_path / "fake_output.mp4"
    fake_output.write_bytes(b"\x00" * 5000)  # > 1000 bytes to pass size check

    with patch("assemble_video.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        # Make the output file appear to exist after the call
        with patch("assemble_video.Path") as mock_path_cls:
            # We'll test via _assemble_image_slideshow directly
            pass

    # Simpler approach: just check _assemble_image_slideshow calls subprocess.run
    call_args_list = []

    def mock_run_capture(cmd, **kwargs):
        call_args_list.append(cmd)
        # write a fake mp4 to the output path argument
        for arg in cmd:
            if str(arg).endswith(".mp4"):
                p = Path(arg)
                p.write_bytes(b"\x00" * 5000)
        return MagicMock(returncode=0, stdout="done", stderr="")

    with patch("assemble_video.subprocess.run", side_effect=mock_run_capture):
        result = assemble_video._assemble_image_slideshow(audio, scenes, output)

    # subprocess.run was called at least once (the make_video.sh call)
    assert len(call_args_list) >= 1
    # the first call should invoke bash + make_video.sh
    assert any("make_video.sh" in str(a) for cmd in call_args_list for a in cmd)
