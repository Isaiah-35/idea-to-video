"""Extract key topics from a transcript using Claude."""
import argparse
import json
import sys
from pathlib import Path

from anthropic import Anthropic

from brand import brand_prefix


def extract_topics(
    transcript: str,
    num_topics: int = 5,
    lang: str = "en",
    brand: dict | None = None,
) -> list[dict]:
    """Extract topics from transcript.

    Returns list of {title, summary, image_prompt}.
    """
    client = Anthropic()
    lang_note = "Respond in Chinese." if lang == "zh" else "Respond in English."
    ctx = brand_prefix(brand)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"{ctx}"
                f"Extract {num_topics} key topics from this transcript. {lang_note}\n\n"
                "Return a JSON array only — no other text. Each element:\n"
                '{"title": str, "summary": str (2-3 sentences for script writing), '
                '"image_prompt": str (visual description for image search/generation)}\n\n'
                "IMPORTANT: Summarize faithfully. Do not add conclusions, rhetorical framing, "
                "or concepts not explicitly present in the transcript.\n\n"
                f"Transcript:\n{transcript}"
            ),
        }],
    )

    return _parse_json(response.content[0].text)


def _parse_json(text: str) -> list[dict]:
    """Parse JSON from Claude response, stripping markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]          # drop opening fence line
        text = text.rsplit("```", 1)[0]         # drop closing fence
    return json.loads(text.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract topics from a transcript")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str)
    group.add_argument("--file", type=Path)
    parser.add_argument("--num-topics", type=int, default=5)
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    text = args.file.read_text(encoding="utf-8").strip() if args.file else args.text
    if not text:
        print("Error: empty text", file=sys.stderr)
        sys.exit(1)

    topics = extract_topics(text, num_topics=args.num_topics, lang=args.lang)
    out = json.dumps(topics, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"Saved: {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()
