"""Transcribe WAV audio with optional speaker labeling.

Backend priority (auto-selected at import time):
  1. mlx      — Apple Silicon GPU + Neural Engine via mlx-whisper
                 ~10x faster than CPU on M-series; pip install mlx-whisper
  2. whisperx — CTranslate2 int8, all CPU cores; pyannote diarization on MPS
  3. whisper  — OpenAI reference implementation, CPU fallback

Speaker labeling:
  - WhisperX/MLX + pyannote diarization when HF_TOKEN is set (audio-level, accurate)
  - Claude inference fallback when HF_TOKEN is absent (pattern-based, no extra install)

Performance notes:
  - Models cached at module level — loaded once per process, instant on reuse.
  - Word alignment skipped by default (need_word_timestamps=False).
    Alignment runs at ~1× realtime on CPU; skipping it is the single biggest
    speedup for transcript-only use (tab 1 → topics → script flow).
  - CTranslate2 uses cpu_threads=0 (all cores); M3 Max = 14 threads.
  - Diarization runs on MPS (Apple Silicon GPU) when available.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# ── Backend detection ──────────────────────────────────────────────────────────

_mlx_whisper = None  # type: ignore
_whisperx = None     # type: ignore

try:
    import mlx_whisper as _mlx_whisper
    _BACKEND = "mlx"
except ImportError:
    try:
        import whisperx as _whisperx
        _BACKEND = "whisperx"
    except ImportError:
        _BACKEND = "whisper"

# Expose under canonical names for patching in tests
whisperx = _whisperx  # type: ignore

try:
    import whisper  # type: ignore  # always import for test patching
except ImportError:
    whisper = None  # type: ignore


# ── Device helpers ─────────────────────────────────────────────────────────────

def _torch_device() -> str:
    """MPS > CUDA > CPU — used for PyTorch models (alignment, diarization)."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


_TORCH_DEV = _torch_device()

# CTranslate2 ASR has no MPS support — always CPU; threading handles parallelism.
_CT2_DEV = "cpu"

# MLX model names on HuggingFace hub
_MLX_MODELS = {
    "tiny":   "mlx-community/whisper-tiny-mlx",
    "base":   "mlx-community/whisper-base-mlx",
    "small":  "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large":  "mlx-community/whisper-large-v3-mlx",
}


# ── Model cache (module-level — persists across Gradio calls) ─────────────────

_asr_cache:     dict = {}   # (model_name,) → whisperx model
_align_cache:   dict = {}   # lang → (align_model, metadata)
_diarize_cache: dict = {}   # hf_token[:8] → DiarizationPipeline


def _load_whisperx_model(model_name: str):
    if model_name not in _asr_cache:
        _asr_cache[model_name] = _whisperx.load_model(
            model_name, _CT2_DEV,
            compute_type="int8",
            # cpu_threads=0 → CTranslate2 uses all available cores (14 on M3 Max)
            # num_workers=2 → overlap I/O and compute for batched segments
        )
    return _asr_cache[model_name]


def _load_align_model(lang: str):
    if lang not in _align_cache:
        _align_cache[lang] = _whisperx.load_align_model(
            language_code=lang, device=_TORCH_DEV
        )
    return _align_cache[lang]


def _load_diarize_pipeline(hf_token: str):
    key = hf_token[:8]
    if key not in _diarize_cache:
        from whisperx.diarize import DiarizationPipeline
        _diarize_cache[key] = DiarizationPipeline(
            use_auth_token=hf_token, device=_TORCH_DEV
        )
    return _diarize_cache[key]


# ── Public API ─────────────────────────────────────────────────────────────────

def transcribe(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    output_dir: Path | None = None,
    device: str | None = None,          # None = auto
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
    need_word_timestamps: bool = False,
) -> str:
    """Transcribe audio and return labeled text.

    Args:
        file_path:            WAV file to transcribe.
        language:             "en" / "zh" / None (auto-detect).
        model_name:           "tiny" / "base" / "small" / "medium" / "large".
        output_dir:           Where to write .txt and .words.json.
        device:               Ignored — device is auto-selected per model type.
        speaker_names:        ["Paul", "Sam"] → [Paul]: / [Sam]: prefix per turn.
        speaker_hints:        Hints for Claude fallback, e.g. "Paul asks questions."
        need_word_timestamps: True only for video sync (adds alignment pass).

    Returns:
        Transcript string. Speaker-labeled if speaker_names provided.
    """
    if _BACKEND == "mlx":
        text, segments = _transcribe_mlx(
            file_path, language=language, model_name=model_name,
            speaker_names=speaker_names, speaker_hints=speaker_hints,
            need_word_timestamps=need_word_timestamps,
        )
    elif _BACKEND == "whisperx":
        text, segments = _transcribe_whisperx(
            file_path, language=language, model_name=model_name,
            speaker_names=speaker_names, speaker_hints=speaker_hints,
            need_word_timestamps=need_word_timestamps,
        )
    else:
        text, segments = _transcribe_whisper(file_path, language=language,
                                             model_name=model_name)
        if speaker_names and not is_labeled(text):
            text = _claude_label(text, speaker_names, speaker_hints)

    out_dir = output_dir or file_path.parent
    (out_dir / f"{file_path.stem}.txt").write_text(text, encoding="utf-8")
    print(f"[{_BACKEND}] Saved: {out_dir / file_path.stem}.txt")

    if segments:
        (out_dir / f"{file_path.stem}.words.json").write_text(
            json.dumps(segments, ensure_ascii=False, indent=2), "utf-8"
        )

    return text


def transcribe_with_timestamps(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    device: str | None = None,
) -> tuple[str, list[dict]]:
    """Return (text, word_segments) with word-level timestamps (for video sync)."""
    if _BACKEND == "mlx":
        return _transcribe_mlx(file_path, language=language, model_name=model_name,
                               need_word_timestamps=True)
    if _BACKEND == "whisperx":
        return _transcribe_whisperx(file_path, language=language, model_name=model_name,
                                    need_word_timestamps=True)
    return _transcribe_whisper(file_path, language=language, model_name=model_name)


# ── MLX backend (Apple Silicon GPU + Neural Engine) ───────────────────────────

def _transcribe_mlx(
    file_path: Path,
    language: str | None,
    model_name: str,
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
    need_word_timestamps: bool = False,
) -> tuple[str, list[dict]]:
    hub_name = _MLX_MODELS.get(model_name, _MLX_MODELS["base"])
    result = _mlx_whisper.transcribe(
        str(file_path),
        path_or_hf_repo=hub_name,
        language=language,
        word_timestamps=need_word_timestamps,
        verbose=False,
    )

    segments = result.get("segments", [])
    text = " ".join(s["text"].strip() for s in segments).strip()

    words: list[dict] = []
    if need_word_timestamps:
        words = [
            {"word": w["word"], "start": w["start"], "end": w["end"]}
            for s in segments
            for w in s.get("words", [])
            if "start" in w
        ]

    if speaker_names:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                # MLX segments are compatible with WhisperX diarization
                text = _diarize_segments(segments, speaker_names, hf_token,
                                         str(file_path))
                return text, words
            except Exception as e:
                print(f"[transcribe] MLX diarization failed ({e}), using Claude")
        text = _claude_label(text, speaker_names, speaker_hints)

    return text, words


# ── WhisperX backend (CTranslate2 int8, all CPU cores) ────────────────────────

def _transcribe_whisperx(
    file_path: Path,
    language: str | None,
    model_name: str,
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
    need_word_timestamps: bool = False,
) -> tuple[str, list[dict]]:
    model = _load_whisperx_model(model_name)
    audio = _whisperx.load_audio(str(file_path))
    result = model.transcribe(audio, language=language)
    lang = result.get("language", language or "en")

    words: list[dict] = []
    if need_word_timestamps or (speaker_names and os.environ.get("HF_TOKEN")):
        try:
            align_model, metadata = _load_align_model(lang)
            result = _whisperx.align(
                result["segments"], align_model, metadata, audio, _TORCH_DEV
            )
            words = [
                {"word": w["word"], "start": w["start"], "end": w["end"]}
                for seg in result["segments"]
                for w in seg.get("words", [])
                if "start" in w
            ]
        except Exception as e:
            print(f"[transcribe] Alignment skipped: {e}")

    text = " ".join(s["text"].strip() for s in result["segments"]).strip()

    if speaker_names:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                text = _diarize_segments(result["segments"], speaker_names,
                                         hf_token, str(file_path))
                return text, words
            except Exception as e:
                print(f"[transcribe] Diarization failed ({e}), using Claude")
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
        {"word": s["text"].strip(), "start": s["start"], "end": s["end"]}
        for s in result.get("segments", [])
    ]
    return text, segments


# ── Diarization (pyannote on MPS) ──────────────────────────────────────────────

def _diarize_segments(
    segments: list[dict],
    speaker_names: list[str],
    hf_token: str,
    audio_path: str,
) -> str:
    """Run pyannote diarization on MPS and return [Name]: labeled turns."""
    import numpy as np

    pipeline = _load_diarize_pipeline(hf_token)
    audio = _whisperx.load_audio(audio_path) if _whisperx else None

    if audio is None:
        # MLX path: load audio via soundfile
        import soundfile as sf
        data, sr = sf.read(audio_path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        import numpy as np
        audio = data.astype(np.float32)

    diarize_segs = pipeline(audio, num_speakers=len(speaker_names))

    # Use WhisperX's assign_word_speakers regardless of transcription backend
    if _whisperx:
        result_with_speakers = _whisperx.assign_word_speakers(
            diarize_segs, {"segments": segments}
        )
        return _format_turns(result_with_speakers["segments"], speaker_names)

    return _format_turns(segments, speaker_names)


def _format_turns(segments: list[dict], speaker_names: list[str]) -> str:
    speaker_map: dict[str, str] = {}
    for seg in segments:
        spk = seg.get("speaker")
        if spk and spk not in speaker_map:
            speaker_map[spk] = speaker_names[len(speaker_map)] \
                if len(speaker_map) < len(speaker_names) else spk

    turns: list[tuple[str, str]] = []
    for seg in segments:
        name = speaker_map.get(seg.get("speaker", ""), seg.get("speaker", "?"))
        txt = seg.get("text", "").strip()
        if not txt:
            continue
        if turns and turns[-1][0] == name:
            turns[-1] = (name, turns[-1][1] + " " + txt)
        else:
            turns.append((name, txt))

    return "\n".join(f"[{n}]: {t}" for n, t in turns)


# ── Claude fallback ────────────────────────────────────────────────────────────

def _claude_label(
    transcript: str,
    speaker_names: list[str],
    hints: str = "",
    model: str = "claude-sonnet-4-6",
) -> str:
    from anthropic import Anthropic
    a = speaker_names[0]
    b = speaker_names[1] if len(speaker_names) > 1 else "Speaker B"
    hint_block = f"\nHints:\n{hints.strip()}\n" if hints.strip() else ""
    prompt = (
        f"Raw transcript of a two-person conversation between {a} and {b}. "
        f"No speaker labels.\n{hint_block}\n"
        f"Break into turns. Prefix each with [{a}]: or [{b}]:. "
        f"Preserve every word exactly. Each turn on a new line. "
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
        description=f"Transcribe WAV — backend: {_BACKEND} | torch: {_TORCH_DEV}"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--lang", choices=["en", "zh"], default=None)
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--speaker-a", default=None)
    parser.add_argument("--speaker-b", default=None)
    parser.add_argument("--hints", default="")
    parser.add_argument("--word-timestamps", action="store_true")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    files = [args.input] if args.input.is_file() else (
        sorted(args.input.glob("*.WAV")) + sorted(args.input.glob("*.wav"))
    )
    if not files:
        print("No WAV files found", file=sys.stderr)
        sys.exit(1)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    speaker_names = [args.speaker_a, args.speaker_b] \
        if args.speaker_a and args.speaker_b else None

    print(f"Backend: {_BACKEND} | ASR: {_CT2_DEV} | Torch: {_TORCH_DEV}")

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
