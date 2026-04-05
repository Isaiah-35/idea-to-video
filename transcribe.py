"""Transcribe WAV audio files to text with optional speaker labeling.

Priority order:
  1. WhisperX + pyannote diarization (if whisperx installed AND HF_TOKEN set)
       → audio-level speaker ID, no guesswork
  2. WhisperX without diarization → plain text → Claude label_speakers
       → pattern-based inference from conversational structure
  3. Whisper → plain text → Claude label_speakers (same fallback)

Speaker names are inputs to transcribe(), not a post-processing step.
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


def transcribe(
    file_path: Path,
    *,
    language: str | None = None,
    model_name: str = "base",
    output_dir: Path | None = None,
    device: str = "cpu",
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
) -> str:
    """Transcribe a single audio file and return the text.

    Args:
        file_path:      Path to the WAV file.
        language:       ISO language code ("en", "zh") or None for auto-detect.
        model_name:     Whisper model size ("tiny"…"large").
        output_dir:     Directory for .txt and .words.json output files.
        device:         "cpu", "cuda", or "mps".
        speaker_names:  ["Paul", "Sam"] — when provided, output is labeled as
                        [Paul]: ... [Sam]: ... Speaker labeling uses WhisperX
                        diarization if HF_TOKEN is set, otherwise Claude inference.
        speaker_hints:  Optional cues for Claude fallback labeling, e.g.
                        "Paul asks questions, Sam explains technical details."

    Returns:
        Transcript text. With speaker_names: prefixed as [Name]: per turn.
    """
    if _BACKEND == "whisperx":
        text, segments = _transcribe_whisperx(
            file_path, language=language, model_name=model_name, device=device,
            speaker_names=speaker_names, speaker_hints=speaker_hints,
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
    """Return (text, word_segments) — timestamps only, no speaker labeling."""
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
    speaker_names: list[str] | None = None,
    speaker_hints: str = "",
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

    if speaker_names:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                text = _diarize(audio, result, speaker_names, hf_token, device)
                return text, words
            except Exception as e:
                print(f"[transcribe] Diarization failed ({e}), falling back to Claude labeling")
        # No HF_TOKEN or diarization failed → Claude inference
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


# ── diarization (WhisperX + pyannote, requires HF_TOKEN) ──────────────────────

def _diarize(
    audio,
    result: dict,
    speaker_names: list[str],
    hf_token: str,
    device: str,
) -> str:
    """Run pyannote diarization and return labeled transcript text."""
    from whisperx.diarize import DiarizationPipeline

    diarize_model = DiarizationPipeline(use_auth_token=hf_token, device=device)
    diarize_segments = diarize_model(audio, num_speakers=len(speaker_names))
    result = whisperx.assign_word_speakers(diarize_segments, result)
    return _format_diarized_turns(result["segments"], speaker_names)


def _format_diarized_turns(segments: list[dict], speaker_names: list[str]) -> str:
    """Convert diarized segments into [Name]: turn-labeled text.

    Maps SPEAKER_0 → speaker_names[0], SPEAKER_1 → speaker_names[1], etc.
    in order of first appearance.
    """
    # Build speaker → name map in order of first appearance
    speaker_map: dict[str, str] = {}
    for seg in segments:
        spk = seg.get("speaker")
        if spk and spk not in speaker_map:
            idx = len(speaker_map)
            speaker_map[spk] = speaker_names[idx] if idx < len(speaker_names) else spk

    # Merge consecutive same-speaker segments into turns
    turns: list[tuple[str, str]] = []  # (name, text)
    for seg in segments:
        spk = seg.get("speaker", "")
        name = speaker_map.get(spk, spk)
        seg_text = seg.get("text", "").strip()
        if not seg_text:
            continue
        if turns and turns[-1][0] == name:
            turns[-1] = (name, turns[-1][1] + " " + seg_text)
        else:
            turns.append((name, seg_text))

    return "\n".join(f"[{name}]: {text}" for name, text in turns)


# ── Claude fallback labeling ───────────────────────────────────────────────────

def _claude_label(
    transcript: str,
    speaker_names: list[str],
    hints: str = "",
    model: str = "claude-sonnet-4-6",
) -> str:
    """Infer speaker turns from conversational patterns using Claude."""
    from anthropic import Anthropic

    a, b = speaker_names[0], speaker_names[1] if len(speaker_names) > 1 else "Speaker B"
    client = Anthropic()
    hint_block = f"\nHints to help identify speakers:\n{hints.strip()}\n" if hints.strip() else ""

    prompt = (
        f"You are given a raw transcript of a two-person conversation between "
        f"{a} and {b}. The transcript is one continuous block of text with no speaker labels.\n"
        f"{hint_block}\n"
        f"Your task: break the transcript into speaker turns and prefix each turn with "
        f"[{a}]: or [{b}]:.\n\n"
        f"Rules:\n"
        f"- Preserve every word exactly as-is — do NOT paraphrase, summarize, or add anything.\n"
        f"- Each new turn starts on a new line.\n"
        f"- Use [{a}]: and [{b}]: as the only prefixes — no timestamps, no parenthetical notes.\n"
        f"- If a passage is genuinely ambiguous, assign it to the most likely speaker.\n"
        f"- Return ONLY the labeled transcript — no preamble, no explanation.\n\n"
        f"Transcript:\n{transcript}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=8096,
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
    """Public API: label an already-transcribed text. Delegates to _claude_label."""
    return _claude_label(transcript, [speaker_a, speaker_b], hints=hints, model=model)


def is_labeled(transcript: str) -> bool:
    """Return True if transcript already has [Speaker]: turn labels."""
    return bool(re.search(r'^\[.+\]:', transcript, re.MULTILINE))


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
    parser.add_argument("--speaker-a", default=None, help="Name of first speaker")
    parser.add_argument("--speaker-b", default=None, help="Name of second speaker")
    parser.add_argument("--hints", default="", help="Hints to help identify speakers")
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

    speaker_names = None
    if args.speaker_a and args.speaker_b:
        speaker_names = [args.speaker_a, args.speaker_b]

    print(f"Transcribing {len(files)} file(s) with {_BACKEND}/{args.model}…")
    for f in files:
        print(f"\n--- {f.name} ---")
        text = transcribe(f, language=args.lang, model_name=args.model,
                          output_dir=args.output_dir, device=args.device,
                          speaker_names=speaker_names, speaker_hints=args.hints)
        print(text[:300] + ("…" if len(text) > 300 else ""))


if __name__ == "__main__":
    main()
