"""Generate high-quality TTS audio using Kokoro neural TTS."""
import argparse
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline


def generate(text: str, output: Path, lang: str = "en", voice: str | None = None) -> None:
    lang_code = "z" if lang == "zh" else "a"
    if voice is None:
        voice = "zf_xiaobei" if lang == "zh" else "af_heart"

    pipeline = KPipeline(lang_code=lang_code)
    chunks = []
    for _, _, audio in pipeline(text, voice=voice):
        chunks.append(audio)
    combined = np.concatenate(chunks)
    sf.write(str(output), combined, 24000)
    print(f"Saved: {output} ({len(combined)/24000:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kokoro neural TTS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str)
    group.add_argument("--file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--voice", type=str, default=None)
    args = parser.parse_args()

    if args.file:
        text = args.file.read_text(encoding="utf-8").strip()
    else:
        text = args.text

    if not text:
        print("Error: empty text", file=sys.stderr)
        sys.exit(1)

    generate(text, args.output, args.lang, args.voice)


if __name__ == "__main__":
    main()
