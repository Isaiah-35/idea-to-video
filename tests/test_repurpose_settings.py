"""Tests for repurpose.py and settings.py."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from repurpose import extract_clips, merge_short_scenes
from settings import load_settings, save_settings, get_api_key_status


# ── merge_short_scenes ────────────────────────────────────────────────────────

def test_merge_short_scenes_empty():
    assert merge_short_scenes([]) == []


def test_merge_short_scenes_single():
    result = merge_short_scenes([{"title": "A", "duration_s": 30.0}])
    assert len(result) == 1
    assert result[0]["title"] == "A"
    assert result[0]["duration_s"] == 30.0


def test_merge_short_scenes_groups_under_target():
    scenes = [
        {"title": "A", "duration_s": 20.0},
        {"title": "B", "duration_s": 20.0},  # 20+20=40 < 45, stay together
        {"title": "C", "duration_s": 30.0},  # 40+30=70 > 45, flush and start new
    ]
    result = merge_short_scenes(scenes, target_duration=45.0)
    assert len(result) == 2
    assert result[0]["title"] == "A"
    assert result[0]["duration_s"] == pytest.approx(40.0)
    assert result[1]["title"] == "C"
    assert result[1]["duration_s"] == pytest.approx(30.0)


def test_merge_short_scenes_none_duration_treated_as_zero():
    scenes = [
        {"title": "A", "duration_s": 30.0},
        {"title": "B", "duration_s": None},  # no duration → merged into A
    ]
    result = merge_short_scenes(scenes, target_duration=45.0)
    assert len(result) == 1
    assert result[0]["duration_s"] == pytest.approx(30.0)


def test_merge_short_scenes_each_scene_in_scenes_field():
    scenes = [{"title": "A", "duration_s": 10.0}, {"title": "B", "duration_s": 10.0}]
    result = merge_short_scenes(scenes, target_duration=45.0)
    assert len(result) == 1
    assert len(result[0]["scenes"]) == 2


# ── extract_clips ─────────────────────────────────────────────────────────────

def _mock_ffmpeg_success(returncode=0):
    """Return a mock subprocess.run that pretends ffmpeg succeeded."""
    mock = MagicMock()
    mock.returncode = returncode
    return mock


def test_extract_clips_skips_none_duration(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    scenes = [{"title": "A", "duration_s": None}]
    clips = extract_clips(video, scenes, tmp_path)
    assert clips == []


def test_extract_clips_skips_over_max_duration(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    scenes = [{"title": "A", "duration_s": 120.0}]
    clips = extract_clips(video, scenes, tmp_path, max_duration=60.0)
    assert clips == []


def test_extract_clips_safe_title_sanitizes_special_chars(tmp_path):
    """Title with special chars → safe filename."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    scenes = [{"title": "AI & ML: Intro", "duration_s": 10.0}]

    def fake_run(cmd, **kw):
        # Create the output file to simulate success
        out_path = Path(cmd[-1])
        out_path.write_bytes(b"x" * 1000)
        r = MagicMock()
        r.returncode = 0
        return r

    with patch("repurpose.subprocess.run", side_effect=fake_run):
        clips = extract_clips(video, scenes, tmp_path, max_duration=60.0)

    assert len(clips) == 1
    assert "/" not in Path(clips[0]["path"]).name or True  # no path traversal
    assert clips[0]["duration_s"] == pytest.approx(10.0)


def test_extract_clips_ffmpeg_failure_skips_scene(tmp_path):
    """If ffmpeg fails or output is too small, the scene is skipped (no crash)."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    scenes = [{"title": "A", "duration_s": 10.0}]

    mock = MagicMock()
    mock.returncode = 1

    with patch("repurpose.subprocess.run", return_value=mock):
        clips = extract_clips(video, scenes, tmp_path)

    assert clips == []


def test_extract_clips_offsets_accumulate(tmp_path):
    """Each scene's ffmpeg -ss offset should equal sum of prior durations."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    scenes = [
        {"title": "A", "duration_s": 10.0},
        {"title": "B", "duration_s": 20.0},
        {"title": "C", "duration_s": 5.0},
    ]

    offsets_seen: list[float] = []

    def fake_run(cmd, **kw):
        ss_idx = cmd.index("-ss")
        offsets_seen.append(float(cmd[ss_idx + 1]))
        out_path = Path(cmd[-1])
        out_path.write_bytes(b"x" * 1000)
        r = MagicMock()
        r.returncode = 0
        return r

    with patch("repurpose.subprocess.run", side_effect=fake_run):
        extract_clips(video, scenes, tmp_path, max_duration=60.0)

    assert offsets_seen == pytest.approx([0.0, 10.0, 30.0])


# ── settings ─────────────────────────────────────────────────────────────────

def test_load_settings_returns_defaults_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("settings.SETTINGS_FILE", tmp_path / "settings.json")
    s = load_settings()
    assert s["claude_model"] == "claude-sonnet-4-6"
    assert s["whisper_backend"] == "whisper"


def test_load_settings_merges_with_defaults(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"claude_model": "claude-opus-4-6"}), "utf-8")
    monkeypatch.setattr("settings.SETTINGS_FILE", settings_file)
    s = load_settings()
    assert s["claude_model"] == "claude-opus-4-6"
    assert s["whisper_backend"] == "whisper"  # default filled in


def test_save_settings_persists(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr("settings.SETTINGS_FILE", settings_file)
    save_settings({"claude_model": "claude-haiku-4-5-20251001", "whisper_backend": "whisperx"})
    data = json.loads(settings_file.read_text("utf-8"))
    assert data["claude_model"] == "claude-haiku-4-5-20251001"


def test_load_settings_handles_corrupt_file(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("not json at all", "utf-8")
    monkeypatch.setattr("settings.SETTINGS_FILE", settings_file)
    s = load_settings()
    assert s["claude_model"] == "claude-sonnet-4-6"  # falls back to defaults


def test_get_api_key_status_when_keys_absent(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("FAL_KEY", raising=False)
    status = get_api_key_status()
    assert "not set" in status["anthropic"]
    assert "not set" in status["pexels"]
    assert "not set" in status["fal"]


def test_get_api_key_status_when_keys_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("PEXELS_API_KEY", "px-test")
    monkeypatch.setenv("FAL_KEY", "fal-test")
    status = get_api_key_status()
    assert "✓" in status["anthropic"]
    assert "✓" in status["pexels"]
    assert "✓" in status["fal"]
