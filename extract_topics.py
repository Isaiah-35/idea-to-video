"""Extract key topics from a transcript using Claude."""
import argparse
import json
import re
import sys
from pathlib import Path

from anthropic import Anthropic

from brand import brand_prefix


def _is_conversation(transcript: str) -> bool:
    """Return True if transcript has [Speaker]: turn labels."""
    return bool(re.search(r'^\[.+\]:', transcript, re.MULTILINE))


def _speaker_names(transcript: str) -> list[str]:
    """Extract unique speaker names from [Name]: labels, in order of appearance."""
    seen: list[str] = []
    for name in re.findall(r'^\[(.+?)\]:', transcript, re.MULTILINE):
        if name not in seen:
            seen.append(name)
    return seen


def extract_topics(
    transcript: str,
    num_topics: int = 5,
    lang: str = "en",
    brand: dict | None = None,
    extra_context: str = "",
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    """Extract topics from transcript.

    Returns list of {title, summary, image_prompt}.
    When the transcript has [Speaker]: labels (from label_speakers), the prompt
    switches to conversation mode: summaries preserve who said what.
    extra_context is prepended before brand_prefix in the prompt.
    """
    client = Anthropic()
    lang_note = "Respond in Chinese." if lang == "zh" else "Respond in English."
    ctx = (extra_context.strip() + "\n\n" if extra_context.strip() else "") + brand_prefix(brand)

    conversation = _is_conversation(transcript)

    if conversation:
        names = _speaker_names(transcript)
        speakers_str = " and ".join(names) if names else "the speakers"
        task = (
            f"The following is a labeled conversation between {speakers_str}. "
            f"Extract {num_topics} key topics discussed. {lang_note}\n\n"
            "For each topic, the summary must preserve who said what — "
            "attribute insights, questions, and positions to the correct speaker by name. "
            "Do not flatten the conversation into a single voice.\n\n"
            "Return a JSON array only — no other text. Each element:\n"
            '{"title": str, "summary": str (2-3 sentences, speaker-attributed), '
            '"image_prompt": str (visual description for image search/generation), '
            '"speakers": [list of speaker names who contributed to this topic]}\n\n'
            "IMPORTANT: Summarize faithfully. Do not add conclusions, rhetorical framing, "
            "or concepts not explicitly present in the transcript.\n\n"
            f"Transcript:\n{transcript}"
        )
    else:
        task = (
            f"Extract {num_topics} key topics from this transcript. {lang_note}\n\n"
            "Return a JSON array only — no other text. Each element:\n"
            '{"title": str, "summary": str (2-3 sentences for script writing), '
            '"image_prompt": str (visual description for image search/generation)}\n\n'
            "IMPORTANT: Summarize faithfully. Do not add conclusions, rhetorical framing, "
            "or concepts not explicitly present in the transcript.\n\n"
            f"Transcript:\n{transcript}"
        )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": f"{ctx}{task}"}],
    )

    return _parse_json(response.content[0].text)


def _parse_json(text: str) -> list[dict]:
    """Parse JSON from Claude response, stripping markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]          # drop opening fence line
        text = text.rsplit("```", 1)[0]         # drop closing fence
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Surface a clear message if Claude truncated the response (max_tokens hit)
        raise ValueError(
            f"Claude returned malformed JSON (likely truncated — response was {len(text)} chars): {e}"
        ) from e


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
