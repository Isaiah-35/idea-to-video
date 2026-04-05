"""Settings persistence: Claude model selection, Whisper backend, etc."""
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "settings.json"

_DEFAULTS: dict = {
    "claude_model": "claude-sonnet-4-6",
    "whisper_backend": "whisper",
}


def load_settings() -> dict:
    """Load settings from settings.json, merging with defaults."""
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text("utf-8"))
            return {**_DEFAULTS, **data}
        except Exception:
            pass
    return _DEFAULTS.copy()


def save_settings(s: dict) -> None:
    """Persist settings dict to settings.json."""
    SETTINGS_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), "utf-8")
