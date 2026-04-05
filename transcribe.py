"""Transcribe WAV audio files to text with optional speaker labeling.

Priority order:
  1. WhisperX + pyannote diarization (if whisperx installed AND HF_TOKEN set)
       → audio-level speaker ID, no guesswork
  2. WhisperX without diarization → plain text → Claude label_speakers
       → pattern-based inference from conversational structure
  3. Whisper → plain text → Claude label_speakers (same fallback)

Speaker names are inputs to transcribe(), not a post-processing step.

Performance notes:
  - Models are cached at module level — only loaded once per process.
  - Device auto-selects: MPS (Apple Silicon) > CUDA > CPU.
  - Word alignment is skipped unless need_word_timestamps=True; diarization
    runs at segment level which is fast and accurate enough for transcripts.
"""
import argparse
import json
import os
import re
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


# ── Device auto-selection ──────────────────────────────────────────────────────

def _best_device() -> str:
    """Return the fastest available device: mps > cuda > cpu."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


# CTranslate2 (WhisperX ASR) does not support MPS — always use cpu for it.
# PyTorch models (alignment, diarization) do support MPS.
_CT2_DEVICE = "cpu"
_TORCH_DEVICE = _best_device()


# ── Model cache (module-level — persists across Gradio calls) ─────────────────

_asr_cache: dict[tuple, object] = {}    # (model_name, compute_type) → model
_align_cache: dict[str, tuple] = {}     # lang → (align_model, metadata)
_diarize_cache: dict[str, object] = {}  # hf_token[:8] → DiarizationPipeline


def _load_asr_model(model_name: str):
    key = (model_name, "int8")
    if key not in _asr_cache:
        _asr_cache[key] = whisperx.load_model(
            model_name, _CT2_DEVICE, compute_type="int8"
        )
    return _asr_cache[key]


def _load_align_model(lang: str):
    if lang not in _align_cache:
        _align_cache[lang] = whisperx.load_align_model(
            language_code=lang, device=_TORCH_DEVICE
        )
    return _align_cache[lang]


def _load_diarize_pipeline(hf_token: str):
    cache_key = hf_token[:8]
    if cache_key not in _diarize_cache:
        from whisperx.diarize import DiarizationPipeline
        _diarize_cache[cache_key] = DiarizationPipeline(
            use_auth_token=hf_token, device=_TORCH_DEVICE
        )
    return _diarize_cache[cache_key]


# ── Public API ─────────────────────────────────────────────────────────────────

def transcribe(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    output_dir: Path | None = None,
    device: str | None = None,         # None = auto (recommended)
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
    need_word_timestamps: bool = False,
) -> str:
    """Transcribe a single audio file and return the text.

    Args:
        file_path:            Path to the WAV file.
        language:             ISO language code or None for auto-detect.
        model_name:           Whisper model size ("tiny"…"large").
        output_dir:           Directory for .txt / .words.json output.
        device:               "cpu" / "cuda" / "mps" / None (auto-select).
        speaker_names:        ["Paul", "Sam"] → output labeled as [Paul]: …
        speaker_hints:        Hints for Claude fallback labeling.
        need_word_timestamps: Set True only when downstream stages need
                              per-word timing (video sync). Skipping this
                              saves significant time for transcript-only use.

    Returns:
        Transcript text. With speaker_names: [Name]: prefixed per turn.
    """
    if _BACKEND == "whisperx":
        text, segments = _transcribe_whisperx(
            file_path,
            language=language,
            model_name=model_name,
            speaker_names=speaker_names,
            speaker_hints=speaker_hints,
            need_word_timestamps=need_word_timestamps,
        )
    else:
        text, segments = _transcribe_whisper(
            file_path, language=language, model_name=model_name,
        )
        if speaker_names and not is_labeled(text):
            text = _claude_label(text, speaker_names, speaker_hints)

    out_dir = output_dir or file_path.parent
    out_file = out_dir / f"{file_path.stem}.txt"
    out_file.write_text(text, encoding="utf-8")
    print(f"Saved: {out_file}")

    if segments:
        words_file = out_dir / f"{file_path.stem}.words.json"
        words_file.write_text(
            json.dumps(segments, ensure_ascii=False, indent=2), "utf-8"
        )
        print(f"Saved word timestamps: {words_file}")

    return text


def transcribe_with_timestamps(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    device: str | None = None,
) -> tuple[str, list[dict]]:
    """Return (text, word_segments) with word-level timestamps."""
    if _BACKEND == "whisperx":
        return _transcribe_whisperx(
            file_path, language=language, model_name=model_name,
            need_word_timestamps=True,
        )
    return _transcribe_whisper(file_path, language=language, model_name=model_name)


# ── WhisperX backend ───────────────────────────────────────────────────────────

def _transcribe_whisperx(
    file_path: Path,
    language: str | None,
    model_name: str,
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
    need_word_timestamps: bool = False,
) -> tuple[str, list[dict]]:
    model = _load_asr_model(model_name)
    audio = whisperx.load_audio(str(file_path))
    result = model.transcribe(audio, language=language)
    lang = result.get("language", language or "en")

    words: list[dict] = []

    if need_word_timestamps or (speaker_names and os.environ.get("HF_TOKEN")):
        # Alignment needed: word timestamps OR accurate word-level diarization
        try:
            align_model, metadata = _load_align_model(lang)
            result = whisperx.align(
                result["segments"], align_model, metadata, audio, _TORCH_DEVICE
            )
            words = [
                {"word": w["word"], "start": w["start"], "end": w["end"]}
                for seg in result["segments"]
                for w in seg.get("words", [])
                if "start" in w
            ]
        except Exception as e:
            print(f"[transcribe] Alignment skipped: {e}")

    text = " ".join(seg["text"].strip() for seg in result["segments"]).strip()

    if speaker_names:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                text = _diarize(audio, result, speaker_names, hf_token)
                return text, words
            except Exception as e:
                print(f"[transcribe] Diarization failed ({e}), falling back to Claude")
        text = _claude_label(text, speaker_names, speaker_hints)

    return text, words


def _transcribe_whisper(
    file_path: Path,
    language: str | None,
    model_name: str,
) -> tuple[str, list[dict]]:
    model = whisper.load_model(model_name)
    result = model.transcribe(str(file_path), language=language, fp16=False)
    text: str = result["text"].strip()
    segments = [
        {"word": seg["text"].strip(), "start": seg["start"], "end": seg["end"]}
        for seg in result.get("segments", [])
    ]
    return text, segments


# ── Diarization ────────────────────────────────────────────────────────────────

def _diarize(audio, result: dict, speaker_names: list[str], hf_token: str) -> str:
    pipeline = _load_diarize_pipeline(hf_token)
    diarize_segments = pipeline(audio, num_speakers=len(speaker_names))
    result = whisperx.assign_word_speakers(diarize_segments, result)
    return _format_diarized_turns(result["segments"], speaker_names)


def _format_diarized_turns(segments: list[dict], speaker_names: list[str]) -> str:
    speaker_map: dict[str, str] = {}
    for seg in segments:
        spk = seg.get("speaker")
        if spk and spk not in speaker_map:
            idx = len(speaker_map)
            speaker_map[spk] = speaker_names[idx] if idx < len(speaker_names) else spk

    turns: list[tuple[str, str]] = []
    for seg in segments:
        name = speaker_map.get(seg.get("speaker", ""), seg.get("speaker", "?"))
        seg_text = seg.get("text", "").strip()
        if not seg_text:
            continue
        if turns and turns[-1][0] == name:
            turns[-1] = (name, turns[-1][1] + " " + seg_text)
        else:
            turns.append((name, seg_text))

    return "\n".join(f"[{name}]: {text}" for name, text in turns)


# ── Claude fallback ────────────────────────────────────────────────────────────

def _claude_label(
    transcript: str,
    speaker_names: list[str],
    hints: str = "",
    model: str = "claude-sonnet-4-6",
) -> str:
    from anthropic import Anthropic
    a, b = speaker_names[0], speaker_names[1] if len(speaker_names) > 1 else "Speaker B"
    client = Anthropic()
    hint_block = f"\nHints:\n{hints.strip()}\n" if hints.strip() else ""
    prompt = (
        f"Raw transcript of a two-person conversation between {a} and {b}. "
        f"No speaker labels.\n{hint_block}\n"
        f"Break into turns, prefix each with [{a}]: or [{b}]:.\n"
        f"Rules: preserve every word exactly. Each turn on a new line. "
        f"Return ONLY the labeled transcript.\n\nTranscript:\n{transcript}"
    )
    response = Anthropic().messages.create(
        model=model, max_tokens=8096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ── Public helpers ─────────────────────────────────────────────────────────────

def label_speakers(
    transcript: str,
    speaker_a: str = "Speaker A",
    speaker_b: str = "Speaker B",
    hints: str = "",
    model: str = "claude-sonnet-4-6",
) -> str:
    return _claude_label(transcript, [speaker_a, speaker_b], hints=hints, model=model)


def is_labeled(transcript: str) -> bool:
    return bool(re.search(r'^\[.+\]:', transcript, re.MULTILINE))


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Transcribe WAV files (backend: {_BACKEND}, torch device: {_TORCH_DEVICE})"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--lang", choices=["en", "zh"], default=None)
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--speaker-a", default=None)
    parser.add_argument("--speaker-b", default=None)
    parser.add_argument("--hints", default="")
    parser.add_argument("--word-timestamps", action="store_true",
                        help="Run word alignment (slower, needed for video sync)")
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    files = [input_path] if input_path.is_file() else (
        sorted(input_path.glob("*.WAV")) + sorted(input_path.glob("*.wav"))
    )
    if not files:
        print("No WAV files found", file=sys.stderr)
        sys.exit(1)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    speaker_names = [args.speaker_a, args.speaker_b] if args.speaker_a and args.speaker_b else None
    print(f"Backend: {_BACKEND} | ASR device: {_CT2_DEVICE} | Torch device: {_TORCH_DEVICE}")

    for f in files:
        print(f"\n--- {f.name} ---")
        text = transcribe(
            f, language=args.lang, model_name=args.model,
            output_dir=args.output_dir,
            speaker_names=speaker_names, speaker_hints=args.hints,
            need_word_timestamps=args.word_timestamps,
        )
        print(text[:300] + ("…" if len(text) > 300 else ""))


if __name__ == "__main__":
    main()
