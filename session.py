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
