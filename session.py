"""Session persistence: auto-save and restore full pipeline state."""
import json
from datetime import datetime
from pathlib import Path

SESSION_DIR = Path.home() / ".idea-to-video" / "sessions"


def save_session(state: dict) -> Path:
    """Write pipeline state to SESSION_DIR/YYYYMMDD-HHMMSS.json. Returns path."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = SESSION_DIR / f"{ts}.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(path: Path) -> dict:
    """Load and return a single session file as dict."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_latest_session() -> dict | None:
    """Return the most recent session dict, or None if no sessions exist."""
    if not SESSION_DIR.exists():
        return None
    files = sorted(SESSION_DIR.glob("*.json"), reverse=True)
    if not files:
        return None
    try:
        return load_session(files[0])
    except Exception:
        return None


def list_sessions() -> list[Path]:
    """Return session files sorted newest-first."""
    if not SESSION_DIR.exists():
        return []
    return sorted(SESSION_DIR.glob("*.json"), reverse=True)


def build_scene_graph(
    topics: list[dict],
    sections: list[str],
    image_paths: list[str | None] | None = None,
    durations: list[float] | None = None,
) -> list[dict]:
    """Zip topics + sections into scene dicts.

    Args:
        topics: list of topic dicts (title, summary, image_prompt).
        sections: list of spoken-text strings, one per topic.
        image_paths: optional list of file paths (or None per scene).
        durations: optional list of TTS durations in seconds (or None per scene).

    Returns:
        List of scene dicts:
            {"index": int, "title": str, "spoken_text": str,
             "image_prompt": str, "image_path": str|None, "duration_s": float|None}

    Raises:
        ValueError: if topics and sections have different lengths, or if
            image_paths/durations are provided with a different length.
    """
    if len(topics) != len(sections):
        raise ValueError(
            f"topics ({len(topics)}) and sections ({len(sections)}) must have the same length"
        )
    if image_paths is not None and len(image_paths) != len(topics):
        raise ValueError(
            f"image_paths ({len(image_paths)}) must match topics ({len(topics)})"
        )
    if durations is not None and len(durations) != len(topics):
        raise ValueError(
            f"durations ({len(durations)}) must match topics ({len(topics)})"
        )

    scenes = []
    for i, (topic, section) in enumerate(zip(topics, sections)):
        scenes.append({
            "index": i,
            "title": topic.get("title", ""),
            "spoken_text": section,
            "image_prompt": topic.get("image_prompt", ""),
            "image_path": image_paths[i] if image_paths else None,
            "duration_s": durations[i] if durations else None,
        })
    return scenes
