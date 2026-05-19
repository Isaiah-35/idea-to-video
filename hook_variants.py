"""Generate 3 opening hook variants (Curiosity / Empathy / Authority) via Claude."""
import argparse
import json
import sys
from pathlib import Path

from anthropic import Anthropic

from brand import brand_prefix


def _parse_json(text: str) -> list[dict]:
    """Parse JSON from Claude response, stripping markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


def generate_hook_variants(
    topics: list[dict],
    lang: str = "en",
    brand: dict | None = None,
    extra_context: str = "",
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    """Generate 3 opening hook variants for a video.

    Returns list of exactly 3 dicts:
        [{"label": "Curiosity", "hook": str},
         {"label": "Empathy",   "hook": str},
         {"label": "Authority", "hook": str}]

    Each hook is 1-3 sentences of plain spoken prose that opens the video.
    """
    client = Anthropic()
    ctx = (extra_context.strip() + "\n\n" if extra_context.strip() else "") + brand_prefix(brand)
    lang_note = "Write in Chinese." if lang == "zh" else "Write in English."
    topic_summary = "; ".join(t.get("title", "") for t in topics)

    prompt = (
        f"{ctx}"
        f"I'm creating a short video covering these topics: {topic_summary}.\n\n"
        f"Write 3 distinct opening hooks for this video. {lang_note}\n\n"
        "Each hook is 1-3 sentences of plain spoken prose — no headers, no markdown.\n"
        "The three hooks must use exactly these rhetorical stances:\n"
        '1. "Curiosity" — open with an intriguing question or surprising fact\n'
        '2. "Empathy" — open by naming a pain the viewer already feels\n'
        '3. "Authority" — open with a confident, direct statement of stakes or expertise\n\n'
        'Return a JSON array of exactly 3 objects with keys "label" and "hook".\n'
        'Labels must be exactly: "Curiosity", "Empathy", "Authority" in that order.\n'
        "No other text."
    )

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    variants = _parse_json(response.content[0].text)
    # Validate / normalise
    expected_labels = ["Curiosity", "Empathy", "Authority"]
    if len(variants) != 3:
        raise ValueError(f"Expected 3 hook variants, got {len(variants)}")
    for item, label in zip(variants, expected_labels):
        item["label"] = label  # enforce exact labels in case Claude diverged
    return variants


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 3 opening hook variants")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topics", type=str, help="JSON string of topics")
    group.add_argument("--file", type=Path, help="JSON file of topics")
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    raw = args.file.read_text("utf-8") if args.file else args.topics
    topics = json.loads(raw)

    variants = generate_hook_variants(topics, lang=args.lang)
    out = json.dumps(variants, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(out, "utf-8")
        print(f"Saved: {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()
