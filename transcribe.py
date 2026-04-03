"""Transcribe WAV audio files to text using local Whisper model."""

import argparse
import sys
from pathlib import Path

import whisper


def transcribe(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    output_dir: Path | None = None,
) -> str:
    """Transcribe a single WAV file and return the text."""
    model = whisper.load_model(model_name)
    result = model.transcribe(
        str(file_path),
        language=language,
        fp16=False,
    )
    text: str = result["text"].strip()

    out_dir = output_dir or file_path.parent
    out_file = out_dir / f"{file_path.stem}.txt"
    out_file.write_text(text, encoding="utf-8")
    print(f"Saved: {out_file}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe WAV files to text")
    parser.add_argument(
        "input",
        type=Path,
        help="WAV file or directory containing WAV files",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "zh"],
        default=None,
        help="Language: en (English, default auto-detect) or zh (Chinese)",
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for transcripts (default: same as input)",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    if input_path.is_file():
        files = [input_path]
    else:
        files = sorted(input_path.glob("*.WAV")) + sorted(input_path.glob("*.wav"))

    if not files:
        print("No WAV files found", file=sys.stderr)
        sys.exit(1)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Transcribing {len(files)} file(s) with model '{args.model}'...")
    for f in files:
        print(f"\n--- {f.name} ---")
        text = transcribe(
            f,
            language=args.lang,
            model_name=args.model,
            output_dir=args.output_dir,
        )
        print(text[:200] + ("..." if len(text) > 200 else ""))


if __name__ == "__main__":
    main()
