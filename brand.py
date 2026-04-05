"""Brand context: persist and inject identity into every Claude prompt."""
import json
from pathlib import Path

BRAND_FILE = Path(__file__).parent / "brand.json"

_DEFAULTS: dict = {"name": "", "audience": "", "tone": "", "style_notes": ""}


def load_brand() -> dict:
    if BRAND_FILE.exists():
        return {**_DEFAULTS, **json.loads(BRAND_FILE.read_text("utf-8"))}
    return _DEFAULTS.copy()


def save_brand(brand: dict) -> None:
    BRAND_FILE.write_text(json.dumps(brand, ensure_ascii=False, indent=2), "utf-8")


def brand_prefix(brand: dict | None = None) -> str:
    """Return a prompt prefix string from brand dict (or load from file if None)."""
    if brand is None:
        brand = load_brand()
    parts = []
    if brand.get("name"):
        parts.append(f"Brand: {brand['name']}")
    if brand.get("audience"):
        parts.append(f"Audience: {brand['audience']}")
    if brand.get("tone"):
        parts.append(f"Tone: {brand['tone']}")
    if brand.get("style_notes"):
        parts.append(f"Style notes: {brand['style_notes']}")
    if not parts:
        return ""
    return "Brand context (apply throughout):\n" + "\n".join(parts) + "\n\n"
