# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A modular Python/Bash pipeline that converts recorded audio into short videos:

```
Audio (WAV) → [transcribe.py] → Text → [kokoro_tts.py] → Audio Track
                                                              + Images
                                                    → [make_video.sh] → MP4
```

The pipeline stages are intentionally decoupled — each script runs independently via CLI.

## UI (component tester)

```bash
.venv/bin/python3 app.py   # opens http://127.0.0.1:7860
```

Four tabs — one per pipeline stage. Each tab imports the corresponding module directly and runs the function in-process (no subprocess overhead for Python components; `make_video.sh` is called via `subprocess`).

## Setup

kokoro requires Python <3.13, so use the bundled venv:

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
# System dep: ffmpeg (for make_video.sh)
```

## Running the Pipeline

**Step 1 — Transcribe audio:**
```bash
python3 transcribe.py recording.wav --lang zh --output-dir output/ [--model base|tiny|small|medium|large]
```

**Step 2 — Generate TTS audio:**
```bash
python3 kokoro_tts.py --file script.txt --output audio.wav --lang en [--voice af_heart|am_adam]
# Fallback (lower quality): python3 speak.py --file script.txt --output audio.wav
```

**Step 3 — Assemble video:**
```bash
bash make_video.sh ./topic_folder/ audio.wav output.mp4
# topic_folder must contain img*.jpg files numbered sequentially
```

## Architecture

| File | Role |
|------|------|
| `transcribe.py` | Whisper-based speech-to-text; auto-detects or targets `en`/`zh` |
| `kokoro_tts.py` | Kokoro neural TTS → 24kHz WAV; primary TTS engine |
| `speak.py` | pyttsx3 fallback TTS; offline but lower quality |
| `make_video.sh` | ffmpeg slideshow assembler; scales images to 1920×1080, adds fade transitions, encodes H.264/AAC |

**Key behaviors:**
- `make_video.sh` distributes audio duration evenly across images, applies 1s fade in/out per slide, validates output file size after encoding
- Kokoro default voices: English → `af_heart`, Chinese → `zf_xiaobei`
- Whisper runs fully locally (no cloud)

## Language Support

Both `transcribe.py` and `kokoro_tts.py` support `--lang en` and `--lang zh`. Chinese TTS depends on `pypinyin`, `cn2an`, and `jieba` for text normalization.
