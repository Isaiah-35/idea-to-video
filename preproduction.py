"""Pre-production context: per-video intent that shapes script structure and pacing."""
import json
from pathlib import Path

PP_FILE = Path(__file__).parent / "preproduction.json"

_DEFAULTS: dict = {"goal": "", "audience": "", "emotion": "", "cta": ""}


def load_preproduction() -> dict:
    if PP_FILE.exists():
        return {**_DEFAULTS, **json.loads(PP_FILE.read_text("utf-8"))}
    return _DEFAULTS.copy()


def save_preproduction(pp: dict) -> None:
    PP_FILE.write_text(json.dumps(pp, ensure_ascii=False, indent=2), "utf-8")


def preproduction_prefix(pp: dict | None = None) -> str:
    """Return a prompt prefix string from pre-production context (or load from file if None)."""
    if pp is None:
        pp = load_preproduction()
    parts = []
    if pp.get("goal"):
        parts.append(f"Goal: {pp['goal']}")
    if pp.get("audience"):
        parts.append(f"Audience: {pp['audience']}")
    if pp.get("emotion"):
        parts.append(f"Desired viewer emotion: {pp['emotion']}")
    if pp.get("cta"):
        parts.append(f"Call to action: {pp['cta']}")
    if not parts:
        return ""
    return "Video pre-production context:\n" + "\n".join(parts) + "\n\n"
