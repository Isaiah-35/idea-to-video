"""Generate high-quality TTS audio using Kokoro neural TTS."""
import argparse
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline


def generate(text: str, output: Path, lang: str = "en", voice: str | None = None) -> None:
    """Generate TTS for a single text block and write to output WAV."""
    lang_code = "z" if lang == "zh" else "a"
    if voice is None:
        voice = "zf_xiaobei" if lang == "zh" else "af_heart"

    pipeline = KPipeline(lang_code=lang_code)
    chunks = []
    for _, _, audio in pipeline(text, voice=voice):
        chunks.append(audio)
    combined = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    sf.write(str(output), combined, 24000)
    print(f"Saved: {output} ({len(combined)/24000:.1f}s)")


def generate_sections(
    sections: list[str],
    output: Path,
    lang: str = "en",
    voice: str | None = None,
) -> list[float]:
    """Generate TTS for each section, concatenate into a single WAV.

    Returns a list of durations (seconds), one per section, for timestamp-driven video cuts.
    The concatenated audio is written to *output*.
    """
    lang_code = "z" if lang == "zh" else "a"
    if voice is None:
        voice = "zf_xiaobei" if lang == "zh" else "af_heart"

    pipeline = KPipeline(lang_code=lang_code)
    all_chunks: list[np.ndarray] = []
    durations: list[float] = []

    for i, section in enumerate(sections):
        chunks = []
        for _, _, audio in pipeline(section.strip(), voice=voice):
            chunks.append(audio)
        section_audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
        dur = len(section_audio) / 24000
        durations.append(dur)
        all_chunks.append(section_audio)
        print(f"  Section {i+1}/{len(sections)}: {dur:.1f}s")

    combined = np.concatenate(all_chunks) if all_chunks else np.zeros(0, dtype=np.float32)
    sf.write(str(output), combined, 24000)
    total = sum(durations)
    print(f"Saved: {output} ({total:.1f}s total, {len(sections)} sections)")
    return durations


def main() -> None:
    parser = argparse.ArgumentParser(description="Kokoro neural TTS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str)
    group.add_argument("--file", type=Path)
    group.add_argument("--sections", type=Path, help="JSON file with list of text sections")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--voice", type=str, default=None)
    parser.add_argument("--durations-out", type=Path, default=None,
                        help="Write per-section durations (one float per line) to this file")
    args = parser.parse_args()

    if args.sections:
        import json
        sections = json.loads(args.sections.read_text("utf-8"))
        durations = generate_sections(sections, args.output, args.lang, args.voice)
        if args.durations_out:
            args.durations_out.write_text("\n".join(f"{d:.3f}" for d in durations), "utf-8")
            print(f"Durations saved: {args.durations_out}")
        return

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
