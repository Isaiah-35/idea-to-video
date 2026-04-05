"""Transcribe WAV audio files to text.

Prefers WhisperX (word-level timestamps, speaker diarization) when available.
Falls back to openai-whisper transparently.
"""
import argparse
import json
import sys
from pathlib import Path

# Try WhisperX first; fall back to standard whisper
try:
    import whisperx
    _BACKEND = "whisperx"
except ImportError:
    whisperx = None  # type: ignore
    _BACKEND = "whisper"

# Always import whisper so tests can patch `transcribe.whisper.load_model`
try:
    import whisper  # type: ignore
except ImportError:
    whisper = None  # type: ignore


def transcribe(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    output_dir: Path | None = None,
    device: str = "cpu",
) -> str:
    """Transcribe a single audio file and return the text.

    Writes a .txt transcript to output_dir (or alongside the file).
    When WhisperX is available, also writes a .words.json with word/segment timestamps.
    """
    if _BACKEND == "whisperx":
        text, segments = _transcribe_whisperx(file_path, language=language,
                                               model_name=model_name, device=device)
    else:
        text, segments = _transcribe_whisper(file_path, language=language, model_name=model_name)

    out_dir = output_dir or file_path.parent
    out_file = out_dir / f"{file_path.stem}.txt"
    out_file.write_text(text, encoding="utf-8")
    print(f"Saved: {out_file}")

    if segments:
        words_file = out_dir / f"{file_path.stem}.words.json"
        words_file.write_text(json.dumps(segments, ensure_ascii=False, indent=2), "utf-8")
        print(f"Saved word timestamps: {words_file}")

    return text


def transcribe_with_timestamps(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    device: str = "cpu",
) -> tuple[str, list[dict]]:
    """Return (text, word_segments).

    word_segments is a list of {word, start, end} dicts.
    With plain whisper, these are segment-level granularity (not word-level).
    """
    if _BACKEND == "whisperx":
        return _transcribe_whisperx(file_path, language=language,
                                     model_name=model_name, device=device)
    return _transcribe_whisper(file_path, language=language, model_name=model_name)


# ── backend implementations ────────────────────────────────────────────────────

def _transcribe_whisperx(
    file_path: Path,
    language: str | None,
    model_name: str,
    device: str,
) -> tuple[str, list[dict]]:
    model = whisperx.load_model(model_name, device, compute_type="int8")
    audio = whisperx.load_audio(str(file_path))
    result = model.transcribe(audio, language=language)

    lang = result.get("language", language or "en")
    try:
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(result["segments"], align_model, metadata, audio, device)
        words = [
            {"word": w["word"], "start": w["start"], "end": w["end"]}
            for seg in result["segments"]
            for w in seg.get("words", [])
            if "start" in w
        ]
    except Exception:
        words = []

    text = " ".join(seg["text"].strip() for seg in result["segments"]).strip()
    return text, words


def _transcribe_whisper(
    file_path: Path,
    language: str | None,
    model_name: str,
) -> tuple[str, list[dict]]:
    model = whisper.load_model(model_name)
    result = model.transcribe(str(file_path), language=language, fp16=False)
    text: str = result["text"].strip()

    # Segment-level timestamps (word-level requires WhisperX)
    segments = [
        {"word": seg["text"].strip(), "start": seg["start"], "end": seg["end"]}
        for seg in result.get("segments", [])
    ]
    return text, segments


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Transcribe WAV files to text (backend: {_BACKEND})"
    )
    parser.add_argument("input", type=Path,
                        help="WAV file or directory containing WAV files")
    parser.add_argument("--lang", choices=["en", "zh"], default=None)
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "mps"])
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

    print(f"Transcribing {len(files)} file(s) with {_BACKEND}/{args.model}…")
    for f in files:
        print(f"\n--- {f.name} ---")
        text = transcribe(f, language=args.lang, model_name=args.model,
                          output_dir=args.output_dir, device=args.device)
        print(text[:200] + ("…" if len(text) > 200 else ""))


if __name__ == "__main__":
    main()
