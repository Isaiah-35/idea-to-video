"""Convert text to spoken English audio using pyttsx3 (offline TTS)."""

import argparse
import sys
from pathlib import Path

import pyttsx3


def text_to_speech(
    text: str,
    *,
    output_file: Path | None = None,
    rate: int = 160,
    volume: float = 0.9,
) -> None:
    """Speak text or save to audio file."""
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    # Select an English voice
    voices = engine.getProperty("voices")
    for voice in voices:
        if "en" in voice.languages[0] if voice.languages else "en" in voice.id.lower():
            engine.setProperty("voice", voice.id)
            break

    if output_file:
        engine.save_to_file(text, str(output_file))
        engine.runAndWait()
        print(f"Saved audio: {output_file}")
    else:
        engine.say(text)
        engine.runAndWait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert text to spoken English")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to speak")
    group.add_argument("--file", type=Path, help="Text file to speak")
    parser.add_argument("--output", type=Path, default=None, help="Save to audio file (WAV/MP3)")
    parser.add_argument("--rate", type=int, default=160, help="Speech rate (default: 160 wpm)")
    parser.add_argument("--volume", type=float, default=0.9, help="Volume 0.0-1.0 (default: 0.9)")
    args = parser.parse_args()

    if args.file:
        if not args.file.exists():
            print(f"Error: {args.file} not found", file=sys.stderr)
            sys.exit(1)
        text = args.file.read_text(encoding="utf-8").strip()
    else:
        text = args.text

    if not text:
        print("Error: empty text", file=sys.stderr)
        sys.exit(1)

    text_to_speech(text, output_file=args.output, rate=args.rate, volume=args.volume)


if __name__ == "__main__":
    main()
