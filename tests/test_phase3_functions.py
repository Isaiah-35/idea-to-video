"""Phase 3 & 4 functional tests — generate_images, hook_variants, session, app handlers."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app as _app
from generate_images import generate_images
from hook_variants import generate_hook_variants
from session import build_scene_graph

_EMPTY_BRAND = ("", "", "", "")


# ── generate_images ───────────────────────────────────────────────────────────

SAMPLE_SCENES = [
    {"title": "Introduction", "image_prompt": "A bright opening scene"},
    {"title": "Main Point",   "image_prompt": "A focused diagram on a desk"},
]


def test_generate_images_pillow_creates_files(tmp_path):
    result = generate_images(SAMPLE_SCENES, tmp_path, backend="pillow", overwrite=True)
    assert len(result) == 2
    for scene in result:
        p = Path(scene["image_path"])
        assert p.exists(), f"Expected {p} to exist"
        assert p.stat().st_size > 1000


def test_generate_images_correct_size(tmp_path):
    from PIL import Image
    result = generate_images(SAMPLE_SCENES[:1], tmp_path, backend="pillow", overwrite=True)
    img = Image.open(result[0]["image_path"])
    assert img.size == (1920, 1080)


def test_generate_images_returns_image_path_key(tmp_path):
    result = generate_images(SAMPLE_SCENES, tmp_path, backend="pillow", overwrite=True)
    for scene in result:
        assert "image_path" in scene
        assert scene["image_path"].endswith(".jpg")


def test_generate_images_overwrite_false_skips(tmp_path):
    # First call
    result1 = generate_images(SAMPLE_SCENES[:1], tmp_path, backend="pillow", overwrite=True)
    mtime1 = Path(result1[0]["image_path"]).stat().st_mtime

    import time
    time.sleep(0.05)

    # Second call with overwrite=False should not regenerate
    result2 = generate_images(SAMPLE_SCENES[:1], tmp_path, backend="pillow", overwrite=False)
    mtime2 = Path(result2[0]["image_path"]).stat().st_mtime
    assert mtime1 == mtime2, "File should not be regenerated when overwrite=False"


def test_generate_images_auto_backend_without_key_uses_pillow(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = generate_images(SAMPLE_SCENES[:1], tmp_path, backend="auto", overwrite=True)
    assert len(result) == 1
    assert Path(result[0]["image_path"]).exists()


def test_generate_images_progress_callback(tmp_path):
    calls = []
    generate_images(SAMPLE_SCENES, tmp_path, backend="pillow", overwrite=True,
                    progress_callback=lambda i, t: calls.append((i, t)))
    assert calls == [(1, 2), (2, 2)]


# ── hook_variants ─────────────────────────────────────────────────────────────

SAMPLE_HOOK_RESPONSE = json.dumps([
    {"label": "Curiosity",  "hook": "Did you know most people do this wrong every day?"},
    {"label": "Empathy",    "hook": "You've felt that frustration when nothing seems to work."},
    {"label": "Authority",  "hook": "After analyzing 500 cases, the pattern is clear."},
])


def test_generate_hook_variants_returns_3(sample_topics):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=SAMPLE_HOOK_RESPONSE)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("hook_variants.Anthropic", return_value=mock_client):
        variants = generate_hook_variants(sample_topics)

    assert len(variants) == 3


def test_generate_hook_variants_all_labels_present(sample_topics):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=SAMPLE_HOOK_RESPONSE)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("hook_variants.Anthropic", return_value=mock_client):
        variants = generate_hook_variants(sample_topics)

    labels = [v["label"] for v in variants]
    assert labels == ["Curiosity", "Empathy", "Authority"]


def test_generate_hook_variants_fence_stripped(sample_topics):
    fenced = "```json\n" + SAMPLE_HOOK_RESPONSE + "\n```"
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=fenced)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("hook_variants.Anthropic", return_value=mock_client):
        variants = generate_hook_variants(sample_topics)

    assert len(variants) == 3
    assert variants[0]["hook"] == "Did you know most people do this wrong every day?"


def test_generate_hook_variants_enforces_labels(sample_topics):
    """Even if Claude returns different label casing, output labels are canonical."""
    bad_labels = json.dumps([
        {"label": "curiosity hook", "hook": "A"},
        {"label": "empathy hook",   "hook": "B"},
        {"label": "authority hook", "hook": "C"},
    ])
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=bad_labels)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("hook_variants.Anthropic", return_value=mock_client):
        variants = generate_hook_variants(sample_topics)

    assert [v["label"] for v in variants] == ["Curiosity", "Empathy", "Authority"]


# ── session.build_scene_graph ─────────────────────────────────────────────────

def test_build_scene_graph_correct_length(sample_topics):
    sections = ["Section one.", "Section two."]
    scenes = build_scene_graph(sample_topics, sections)
    assert len(scenes) == 2


def test_build_scene_graph_correct_fields(sample_topics):
    sections = ["Section one.", "Section two."]
    scenes = build_scene_graph(sample_topics, sections)
    assert scenes[0]["index"] == 0
    assert scenes[0]["title"] == "Sleep and Memory"
    assert scenes[0]["spoken_text"] == "Section one."
    assert "image_prompt" in scenes[0]
    assert scenes[0]["image_path"] is None
    assert scenes[0]["duration_s"] is None


def test_build_scene_graph_with_optional_fields(sample_topics):
    sections = ["S1.", "S2."]
    paths = ["/tmp/img1.jpg", "/tmp/img2.jpg"]
    durations = [12.5, 9.0]
    scenes = build_scene_graph(sample_topics, sections, image_paths=paths, durations=durations)
    assert scenes[0]["image_path"] == "/tmp/img1.jpg"
    assert scenes[1]["duration_s"] == 9.0


def test_build_scene_graph_mismatched_raises(sample_topics):
    with pytest.raises(ValueError, match="same length"):
        build_scene_graph(sample_topics, ["only one section"])


def test_build_scene_graph_mismatched_image_paths_raises(sample_topics):
    sections = ["S1.", "S2."]
    with pytest.raises(ValueError):
        build_scene_graph(sample_topics, sections, image_paths=["/a.jpg"])


# ── App handler: run_write_script still returns 3-tuple ───────────────────────

def test_run_write_script_returns_3_values(sample_topics_json):
    sections = ["Section one.", "Section two."]
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(sections))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("write_script.Anthropic", return_value=mock_client):
        result = _app.run_write_script(
            sample_topics_json, "en", "conversational", *_EMPTY_BRAND)

    assert isinstance(result, tuple)
    assert len(result) == 3, f"run_write_script should return 3 values, got {len(result)}"


# ── App handler: run_generate_hooks ──────────────────────────────────────────

def test_run_generate_hooks_empty_topics():
    radio_update, hooks_json, status = _app.run_generate_hooks(
        "[]", "en", *_EMPTY_BRAND)
    assert "No topics" in status


def test_run_generate_hooks_invalid_json():
    radio_update, hooks_json, status = _app.run_generate_hooks(
        "not json", "en", *_EMPTY_BRAND)
    assert "Invalid" in status or "Error" in status


def test_run_generate_hooks_returns_3_choices(sample_topics_json):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=SAMPLE_HOOK_RESPONSE)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("hook_variants.Anthropic", return_value=mock_client):
        radio_update, hooks_json, status = _app.run_generate_hooks(
            sample_topics_json, "en", *_EMPTY_BRAND)

    assert "generated" in status.lower()
    variants = json.loads(hooks_json)
    assert len(variants) == 3


# ── App handler: run_select_hook prepends hook ────────────────────────────────

def test_run_select_hook_prepends_hook():
    hooks_json = json.dumps([
        {"label": "Curiosity", "hook": "Amazing opener."},
        {"label": "Empathy",   "hook": "You feel it too."},
        {"label": "Authority", "hook": "The data is clear."},
    ])
    current_sections = ["Body section one.", "Body section two."]
    current_full = "\n\n".join(current_sections)

    new_full, new_sections_json = _app.run_select_hook(
        "Curiosity: Amazing opener.",
        hooks_json,
        current_full,
        json.dumps(current_sections),
    )
    assert new_full.startswith("Amazing opener.")
    sections = json.loads(new_sections_json)
    assert sections[0].startswith("Amazing opener.")
    assert len(sections) == 2


def test_run_select_hook_no_selection_returns_unchanged():
    hooks_json = "[]"
    full = "Original script."
    sections = json.dumps(["Original script."])
    new_full, new_sec = _app.run_select_hook(None, hooks_json, full, sections)
    assert new_full == full
    assert new_sec == sections
