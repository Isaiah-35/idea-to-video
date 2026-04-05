"""Generate a TTS-ready script from topics using Claude."""
import argparse
import json
import sys
from pathlib import Path

from anthropic import Anthropic

from brand import brand_prefix

STYLES = ["conversational", "formal", "educational"]


def write_script(
    topics: list[dict],
    lang: str = "en",
    style: str = "conversational",
    brand: dict | None = None,
    extra_context: str = "",
) -> str:
    """Write a TTS-ready spoken script from a list of topic dicts. Returns full script."""
    client = Anthropic()
    ctx = (extra_context.strip() + "\n\n" if extra_context.strip() else "") + brand_prefix(brand)
    lang_note = "Write the script in Chinese." if lang == "zh" else "Write the script in English."
    topics_text = "\n".join(f"- {t['title']}: {t['summary']}" for t in topics)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": (
                f"{ctx}"
                f"Write a {style} script for a short video covering these topics. {lang_note}\n\n"
                "Requirements:\n"
                "- Plain spoken prose only — no headers, bullets, or markdown\n"
                "- 2-4 sentences per topic, paced naturally for TTS\n"
                "- Smooth transitions between topics\n"
                "- Total length: 1-3 minutes when spoken aloud\n\n"
                f"Topics:\n{topics_text}\n\n"
                "Return the script only, no other text."
            ),
        }],
    )

    return response.content[0].text.strip()


def write_script_sections(
    topics: list[dict],
    lang: str = "en",
    style: str = "conversational",
    brand: dict | None = None,
    extra_context: str = "",
) -> list[str]:
    """Write a TTS script split into one section per topic.

    Returns a list of strings (one per topic), suitable for per-slide audio generation.
    extra_context is prepended before brand_prefix in the prompt.
    """
    client = Anthropic()
    ctx = (extra_context.strip() + "\n\n" if extra_context.strip() else "") + brand_prefix(brand)
    lang_note = "Write the script in Chinese." if lang == "zh" else "Write the script in English."
    topics_text = "\n".join(f"- {t['title']}: {t['summary']}" for t in topics)
    n = len(topics)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": (
                f"{ctx}"
                f"Write a {style} script for a short video. {lang_note}\n\n"
                f"There are exactly {n} topics. Write exactly one spoken paragraph per topic.\n"
                "Requirements:\n"
                "- Plain spoken prose only — no headers, bullets, markdown, em-dashes, or rhetorical questions\n"
                "- EXACTLY 2-4 sentences per section — hard limit, no exceptions\n"
                "- Write as natural speech, not written content: avoid listicle phrasing, staccato conditionals, and performative hooks\n"
                "- Smooth transitions between sections\n\n"
                f"Topics:\n{topics_text}\n\n"
                f"Return a JSON array of exactly {n} strings — one string per topic section. "
                "No other text."
            ),
        }],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    sections = json.loads(text.strip())
    return [str(s).strip() for s in sections]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write TTS script from topics JSON")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topics", type=str, help="JSON string of topics")
    group.add_argument("--file", type=Path, help="JSON file of topics")
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--style", choices=STYLES, default="conversational")
    parser.add_argument("--sections", action="store_true", help="Output one section per topic (JSON array)")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    raw = args.file.read_text(encoding="utf-8") if args.file else args.topics
    topics = json.loads(raw)

    if args.sections:
        result = json.dumps(write_script_sections(topics, lang=args.lang, style=args.style),
                            ensure_ascii=False, indent=2)
    else:
        result = write_script(topics, lang=args.lang, style=args.style)

    if args.output:
        args.output.write_text(result, encoding="utf-8")
        print(f"Saved: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
