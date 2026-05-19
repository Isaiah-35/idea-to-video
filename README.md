# idea-to-video

Turn a recorded conversation into a polished short video — without touching a script or a timeline.

```
Record yourself talking → pipeline → shareable MP4
```

No editing software. No pre-written script. No credit walls. Every stage runs locally.

---

## Quick Start

```bash
# 1. Setup (Python 3.12, macOS)
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install ffmpeg

# 2. Set your API key
export ANTHROPIC_API_KEY=sk-...

# 3. Open the UI
.venv/bin/python3 app.py   # → http://127.0.0.1:7860
```

Or run each stage from the CLI — see [Pipeline CLI](#pipeline-cli) below.

---

## Features

### Conversation-First Transcription

You talk. The pipeline listens — even when you switch languages mid-sentence.

Record yourself in Voice Memos, pick the file from the in-app dropdown, click Transcribe.
Get back a clean transcript that handles 80/20 Chinese-English code-switching without
mangling the English insertions. No drag-and-drop, no audio prep, no language flag — pick
`auto` and the right model does the right thing.

<details>
<summary>Technical innovation</summary>

**Four-backend ASR chain** auto-selects the best available:

1. **SenseVoice-Small** (default) — FunASR's multilingual model. Detects language *per
   utterance*, so short English words inside Chinese audio transcribe correctly. Whisper
   locks one language per 30-second window and mangles code-switching; SenseVoice does
   not. Runs at ~15× realtime on CPU.
2. **MLX-Whisper** — Apple Silicon GPU + Neural Engine via `mlx-whisper`, used when word
   timestamps or pyannote diarization are requested (paths SenseVoice can't serve).
3. **WhisperX** — CTranslate2 int8, all CPU cores, for older installs.
4. **Vanilla Whisper** — CPU fallback of last resort.

**VAD chaining** is required for long audio: SenseVoice alone only processes one ~30s
window. `fsmn-vad` splits the input into utterance-sized chunks first, then SenseVoice
transcribes each. A 19-minute file takes ~80s wall time (≈15× realtime).

**Claude cleanup pass** (default on, toggleable per-call) fixes residual ASR mis-reads —
English technical jargon misheard as Chinese homophones (`Cco` → `Claude Code`, `colre` →
`code`), Chinese phrases corrupted by adjacent English. Preserves every semantic unit,
never paraphrases. Falls back to raw transcript on API failure.

**Mac Voice Memos picker** reads your iCloud-synced `CloudRecordings.db` directly to
populate a dropdown of recent recordings — no drag-and-drop. One click loads the `.m4a`
into the audio component; the SenseVoice backend handles `.m4a` natively via ffmpeg.

**Speaker labeling** uses pyannote diarization when `HF_TOKEN` is set (requires accepting
the gated model terms at huggingface.co/pyannote/speaker-diarization-community-1), with
a Claude inference fallback. Both paths degrade gracefully on failure — the transcribe
call returns unlabeled text rather than crashing.

</details>

<details>
<summary>Implementation</summary>

- Module: [`transcribe.py`](transcribe.py)
- Public API: `transcribe(audio_path, language, model_name, output_dir, speaker_names, speaker_hints)`,
  `transcribe_with_timestamps(...)`, `clean_transcript(text, lang, model)`
- Backends: `_transcribe_sensevoice()`, `_transcribe_mlx()`, `_transcribe_whisperx()`, `_transcribe_whisper()`
- Voice Memos picker: `list_voice_memos()` in [`app.py`](app.py); reads
  `~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/CloudRecordings.db`
  in read-only URI mode so the live Voice Memos process is never locked.
- Override default backend: `SENSEVOICE_DISABLE=1` skips SenseVoice and falls through to MLX.
- Gradio allow-list: `demo.launch(allowed_paths=[VOICE_MEMOS_DIR])` so the picker can hand
  paths outside the project tree to `gr.Audio`.
- Research notes: [`RESEARCH_TRANSCRIPTION.md`](RESEARCH_TRANSCRIPTION.md)

```bash
python3 transcribe.py recording.wav --lang zh --output-dir output/ --model base
```

</details>

---

### AI Topic Extraction

From transcript to structure — automatically.

The pipeline reads your transcript and pulls out the distinct ideas you covered, giving each
one a title, a one-sentence summary, and a visual prompt. What took a content editor 30 minutes
is done in seconds. You get a structured outline of your own thinking, ready to build on.

<details>
<summary>Technical innovation</summary>

Claude-powered extraction via `claude-sonnet-4-6`. The prompt injects brand context
(tone, audience) and pre-production intent (goal, CTA, desired emotion) so the extracted
topics reflect *your* framing, not a generic summary. Handles `json.JSONDecodeError` from
truncated responses by raising with a clean message; strips markdown code fences before
parsing. `max_tokens` is set high enough to prevent truncation on long transcripts.

</details>

<details>
<summary>Implementation</summary>

- Module: [`extract_topics.py`](extract_topics.py)
- Public API: `extract_topics(transcript, num_topics, lang, brand, extra_context, model)`
- Returns: `[{"title": str, "summary": str, "image_prompt": str}, ...]`
- Internal: `_parse_json(text)` — strips code fences before JSON parse
- Tests: [`tests/test_extract_topics.py`](tests/test_extract_topics.py)

```bash
python3 extract_topics.py --transcript transcript.txt --num-topics 5 --lang en
```

</details>

---

### Opening Hook Variants

Three ways to open the same video — pick the one that fits your audience.

Every video lives or dies on its first five seconds. Instead of agonizing over the opening,
you get three ready-to-speak options: one that opens with a surprising question, one that names
a pain your audience already feels, and one that leads with confident authority. Choose one,
record it, done.

<details>
<summary>Technical innovation</summary>

Claude generates the three hooks simultaneously in a single prompt call, constrained to
exactly the rhetorical stances: **Curiosity** (intriguing question or surprising fact),
**Empathy** (naming the viewer's existing pain), **Authority** (confident statement of
stakes or expertise). Brand context is injected so tone matches the channel. Output is
validated — if Claude returns the wrong count or labels, the error surfaces clearly.

</details>

<details>
<summary>Implementation</summary>

- Module: [`hook_variants.py`](hook_variants.py)
- Public API: `generate_hook_variants(topics, lang, brand, extra_context, model)`
- Returns: `[{"label": "Curiosity"|"Empathy"|"Authority", "hook": str}, ...]`
- Tests: [`tests/test_phase3_functions.py`](tests/test_phase3_functions.py)

```bash
python3 hook_variants.py --file topics.json --lang en
```

</details>

---

### Script Writing

From outline to full, ready-to-record script in one step.

The pipeline expands your extracted topics into a complete script — either as a single
flowing document or as per-section chunks, one per slide. The script reflects your brand voice
and the specific goal you set for the video (educate, sell, inspire). You can edit it before
recording, or send it straight to TTS.

<details>
<summary>Technical innovation</summary>

Two modes: `write_script()` for a single connected script, `write_script_sections()` for
per-topic sections (required for synchronized per-slide TTS audio). Section mode is what
the pipeline uses internally — each section becomes a separate audio file timed exactly to
its slide. Style variants (conversational / formal / storytelling) are prompt-level controls,
not post-processing. Brand prefix and pre-production context both inject into the prompt.

</details>

<details>
<summary>Implementation</summary>

- Module: [`write_script.py`](write_script.py)
- Public API: `write_script(topics, style, lang, brand, extra_context, model)`, `write_script_sections(...)`
- Style options: `STYLES` dict — conversational, formal, storytelling
- Tests: [`tests/test_write_script.py`](tests/test_write_script.py), [`tests/test_write_script_sections.py`](tests/test_write_script_sections.py)

```bash
python3 write_script.py --file topics.json --style conversational --lang en
```

</details>

---

### Neural TTS (English + Chinese)

Human-quality voice audio, entirely local.

Your script becomes a WAV file that sounds like a real presenter — not a robot reading text.
Supports both English and Chinese natively. No cloud TTS fees, no API latency, no per-character
billing. The audio output drives the video timing: each section's audio length determines how
long its slide stays on screen.

<details>
<summary>Technical innovation</summary>

Primary engine: **Kokoro** neural TTS at 24kHz. Supports multiple voice personas per language
(English: `af_heart`, `af_bella`, `am_adam`; Chinese: `zf_xiaobei`, `zf_xiaoni`). Chinese
text normalization uses `pypinyin`, `cn2an`, and `jieba` before synthesis. Fallback engine:
`speak.py` via pyttsx3 (fully offline, lower quality). Section mode generates one audio file
per topic section, returns durations used to sync slides.

</details>

<details>
<summary>Implementation</summary>

- Module: [`kokoro_tts.py`](kokoro_tts.py) — primary
- Module: [`speak.py`](speak.py) — pyttsx3 fallback
- Public API: `generate(text, output_path, lang, voice)`, `generate_sections(sections, output_dir, lang, voice)`
- Tests: [`tests/test_kokoro_tts.py`](tests/test_kokoro_tts.py)

```bash
python3 kokoro_tts.py --file script.txt --output audio.wav --lang en --voice af_heart
python3 kokoro_tts.py --file script.txt --output audio.wav --lang zh --voice zf_xiaobei
```

</details>

---

### Visual Fallback Chain

Always gets a visual — best quality your setup supports.

Every scene gets a visual automatically. If you have an AI video API key, you get AI-generated
video clips. If you have a stock photo key, you get relevant stock footage. If you have
neither, you get a smooth Ken Burns zoom animation on a generated title card. The pipeline
never stalls waiting for a service you don't have configured.

<details>
<summary>Technical innovation</summary>

Four backends in priority order, selected by `_auto_backend()` based on which env vars are set:

1. **fal.ai** (`FAL_KEY`) — Wan 2.1 text-to-video at 480p, 81 frames, 16fps via `fal-ai/wan-t2v`
2. **Pexels** (`PEXELS_API_KEY`) — stock video via Pexels API, SD quality, with Ken Burns fallback per-scene on miss
3. **Ken Burns** — ffmpeg `zoompan` filter on Pillow-generated title cards (1920×1080, `scale=8000:-1` → `z='min(zoom+0.0015,1.5)'`)
4. **Pillow** — static JPEG title card (always available)

All backends share a common interface: accept `scenes: list[dict]`, return scenes with `visual_path` and `visual_type` set. Progress callback fires per-scene for live UI updates.

</details>

<details>
<summary>Implementation</summary>

- Module: [`visual_sources.py`](visual_sources.py)
- Module: [`generate_images.py`](generate_images.py) — Pillow card renderer + optional DALL-E 3
- Public API: `acquire_visuals(scenes, output_dir, backend, overwrite, progress_callback)`, `detect_available_backends()`
- Env vars: `FAL_KEY`, `PEXELS_API_KEY`, `ANTHROPIC_API_KEY` (for DALL-E 3 via OpenAI API)
- Tests: [`tests/test_visual_sources.py`](tests/test_visual_sources.py)

```bash
python3 visual_sources.py --scenes scenes.json --output-dir visuals/ --backend auto
```

</details>

---

### Video Assembly

Slides and audio merge into a single MP4 — frame-perfect.

Audio durations set the pace. Each slide stays on screen for exactly as long as its section
takes to say. The assembler handles both image slideshows and video clip sequences,
auto-detecting which mode to use based on what the visual pipeline produced.

<details>
<summary>Technical innovation</summary>

Smart dispatch in `assemble()`: if any visual is type `"video"`, routes to
`_assemble_video_clips()` (trim each clip to `duration_s`, concat, mux audio); if all
are images, routes to `_assemble_image_slideshow()` (same ffmpeg slideshow path as
`make_video.sh` but Python-native). Clip trimming uses `-ss` / `-t` seek for frame accuracy.
Output is H.264/AAC MP4 at 1920×1080, CRF 23.

</details>

<details>
<summary>Implementation</summary>

- Module: [`assemble_video.py`](assemble_video.py) — Python (current)
- Script: [`make_video.sh`](make_video.sh) — shell fallback (legacy)
- Public API: `assemble(audio_path, visuals, output_path, fade_duration)`, `assemble_from_files(audio, images, output)`
- Tests: [`tests/test_make_video.py`](tests/test_make_video.py)

```bash
python3 assemble_video.py --audio audio.wav --scenes scenes.json --output video.mp4
# Legacy:
bash make_video.sh ./topic_folder audio.wav video.mp4
```

</details>

---

### Repurpose: One Video → Many Clips

A finished video is a content library.

After the video is assembled, the pipeline can slice it back into per-scene clips —
each clip matches one topic, titled and ready to post as a standalone short. A 10-minute
explainer becomes 6 shorts in one step. Short scenes can be merged to hit a minimum
duration threshold.

<details>
<summary>Technical innovation</summary>

`extract_clips()` accumulates per-scene offsets by summing `duration_s` values, then
calls ffmpeg with `-ss` / `-t` for each clip. Titles are sanitized to safe filenames
(`re.sub(r'[^a-zA-Z0-9_\- ]', '', title)`). Clips below `min_size_bytes` (500 bytes)
are skipped (catches silent ffmpeg failures). `merge_short_scenes()` groups scenes
under a `target_duration` threshold before slicing.

</details>

<details>
<summary>Implementation</summary>

- Module: [`repurpose.py`](repurpose.py)
- Public API: `extract_clips(video_path, scenes, output_dir, max_duration)`, `merge_short_scenes(scenes, target_duration)`
- Tests: [`tests/test_repurpose_settings.py`](tests/test_repurpose_settings.py)

```bash
python3 repurpose.py --video output.mp4 --scenes scenes.json --output-dir clips/
```

</details>

---

### Brand + Pre-Production Context

Every video sounds like you — consistently.

Set your brand voice once (channel name, target audience, tone, style notes). Set per-video
intent (goal, CTA, desired emotion). Every Claude call — topic extraction, script writing,
hook generation — injects this context automatically. The pipeline produces content in your
voice without you having to re-explain it every time.

<details>
<summary>Technical innovation</summary>

Two separate context layers, both stored as JSON and injected as prompt prefixes:

- **Brand** ([`brand.py`](brand.py)) — channel-level identity, persistent across projects. `brand_prefix(brand)` returns a formatted string injected at the top of every Claude prompt.
- **Pre-production** ([`preproduction.py`](preproduction.py)) — per-video intent (goal, audience, emotion, CTA). `preproduction_prefix(pp)` injects just before the task instruction.

Separation matters: brand is "who you are," pre-production is "what this specific video needs to accomplish."

</details>

<details>
<summary>Implementation</summary>

- Module: [`brand.py`](brand.py) — `load_brand()`, `save_brand()`, `brand_prefix(brand)`
- Module: [`preproduction.py`](preproduction.py) — `load_preproduction()`, `save_preproduction()`, `preproduction_prefix(pp)`
- Config files: [`brand.json`](brand.json), [`preproduction.json`](preproduction.json)
- Tests: [`tests/test_brand.py`](tests/test_brand.py)

</details>

---

### Session Persistence

Pick up where you left off.

Every pipeline run is automatically saved. Close the UI, reopen it, and your transcript,
topics, script, and scenes are still there. Sessions are stored in `~/.idea-to-video/sessions/`
with timestamps — load any past run from the UI.

<details>
<summary>Technical innovation</summary>

`build_scene_graph()` zips topics + TTS sections + image paths + durations into structured
scene dicts used by every downstream stage (visual acquisition, video assembly, repurpose).
Sessions serialize the full pipeline state as JSON. `load_latest_session()` returns the
most recent, making cold-start resume a single call.

</details>

<details>
<summary>Implementation</summary>

- Module: [`session.py`](session.py)
- Public API: `save_session(state)`, `load_latest_session()`, `list_sessions()`, `build_scene_graph(topics, sections, image_paths, durations)`
- Storage: `~/.idea-to-video/sessions/YYYYMMDD-HHMMSS.json`
- Tests: [`tests/test_pipeline.py`](tests/test_pipeline.py)

</details>

---

## Architecture

```
Audio input
    │
    ▼
transcribe.py          → raw transcript
    │
    ▼
extract_topics.py      → topics[]          ← brand.py + preproduction.py (context)
    │
    ├──▶ hook_variants.py  → 3 opening hooks
    │
    ▼
write_script.py        → script sections[]
    │
    ▼
kokoro_tts.py          → audio files[]  (durations[])
    │
    ├──▶ session.py  ──▶  build_scene_graph()  →  scenes[]
    │                                                  │
    │                                                  ▼
    │                                         visual_sources.py
    │                                         (fal → pexels → kenburns → pillow)
    │                                                  │ generate_images.py
    │                                                  ▼
    └──────────────────────────────────────▶ assemble_video.py  →  MP4
                                                       │
                                                       ▼
                                               repurpose.py  →  clips[]
```

### Module Reference

| Module | Role | Tests |
|--------|------|-------|
| [`transcribe.py`](transcribe.py) | Audio → text (Whisper/WhisperX) | [`test_transcribe.py`](tests/test_transcribe.py) |
| [`extract_topics.py`](extract_topics.py) | Transcript → structured topics | [`test_extract_topics.py`](tests/test_extract_topics.py) |
| [`write_script.py`](write_script.py) | Topics → script / sections | [`test_write_script.py`](tests/test_write_script.py) |
| [`hook_variants.py`](hook_variants.py) | Topics → 3 opening hooks | [`test_phase3_functions.py`](tests/test_phase3_functions.py) |
| [`kokoro_tts.py`](kokoro_tts.py) | Text → WAV (Kokoro neural TTS) | [`test_kokoro_tts.py`](tests/test_kokoro_tts.py) |
| [`speak.py`](speak.py) | Text → spoken audio (pyttsx3 fallback) | — |
| [`generate_images.py`](generate_images.py) | Scenes → JPEGs (Pillow / DALL-E 3) | [`test_phase3_functions.py`](tests/test_phase3_functions.py) |
| [`visual_sources.py`](visual_sources.py) | Scenes → visuals (fal / Pexels / Ken Burns / Pillow) | [`test_visual_sources.py`](tests/test_visual_sources.py) |
| [`assemble_video.py`](assemble_video.py) | Audio + visuals → MP4 | [`test_make_video.py`](tests/test_make_video.py) |
| [`repurpose.py`](repurpose.py) | Video → per-scene clips | [`test_repurpose_settings.py`](tests/test_repurpose_settings.py) |
| [`brand.py`](brand.py) | Brand identity → prompt prefix | [`test_brand.py`](tests/test_brand.py) |
| [`preproduction.py`](preproduction.py) | Per-video intent → prompt prefix | — |
| [`session.py`](session.py) | Save/restore pipeline state | [`test_pipeline.py`](tests/test_pipeline.py) |
| [`settings.py`](settings.py) | App config (model, backend) | [`test_repurpose_settings.py`](tests/test_repurpose_settings.py) |
| [`app.py`](app.py) | Gradio UI — 10-tab orchestrator | [`test_app_functions.py`](tests/test_app_functions.py) |
| [`make_video.sh`](make_video.sh) | Shell slideshow assembler (legacy) | — |

---

## Pipeline CLI

Each module runs independently as a CLI:

```bash
# 1. Transcribe
python3 transcribe.py recording.wav --lang zh --output-dir output/ --model base

# 2. Extract topics
python3 extract_topics.py --transcript output/transcript.txt --num-topics 5 --lang en

# 3. Write script sections
python3 write_script.py --file topics.json --style conversational --lang en --sections

# 4. Generate hooks (optional)
python3 hook_variants.py --file topics.json --lang en

# 5. TTS
python3 kokoro_tts.py --file sections/ --output-dir audio/ --lang en --voice af_heart

# 6. Acquire visuals
python3 visual_sources.py --scenes scenes.json --output-dir visuals/ --backend auto

# 7. Assemble
python3 assemble_video.py --audio audio/full.wav --scenes scenes.json --output video.mp4

# 8. Repurpose
python3 repurpose.py --video video.mp4 --scenes scenes.json --output-dir clips/
```

---

## Setup

**Requirements:** Python 3.10–3.12 (Kokoro requires < 3.13), ffmpeg

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install ffmpeg
```

**API keys** (set as env vars):

| Key | Required for |
|-----|-------------|
| `ANTHROPIC_API_KEY` | Topic extraction, script writing, hooks |
| `PEXELS_API_KEY` | Stock video backend (free at pexels.com/api) |
| `FAL_KEY` | AI video generation via fal.ai (~$0.20/clip) |
| `OPENAI_API_KEY` | DALL-E 3 image generation (optional) |

**Optional — WhisperX** (word timestamps + speaker diarization):

```bash
pip install whisperx
# For pyannote speaker diarization: set HF_TOKEN env var AND accept terms at
# https://huggingface.co/pyannote/speaker-diarization-community-1 (gated model).
# Without both, transcribe falls back to Claude inference for speaker labels.
```

**Default ASR backend — SenseVoice** ships in `requirements.txt` (`funasr`). The
SenseVoice-Small model (~1GB) downloads on first use to `~/.cache/modelscope/`.

---

## UI

```bash
.venv/bin/python3 app.py   # → http://127.0.0.1:7860
```

Ten tabs map to pipeline stages: Transcribe → Topics → Hooks → Script → TTS → Images →
Visuals → Assemble → Repurpose → Settings. Each tab runs the corresponding module
in-process. The full pipeline can be triggered from a single "Run Pipeline" button that
chains all stages and auto-populates the Repurpose tab with scene data.

---

## Voices

**Kokoro — English:** `af_heart` (default) · `af_bella` · `am_adam` · `am_michael`

**Kokoro — Chinese:** `zf_xiaobei` (default) · `zf_xiaoni` · `zm_yunjian`

---

## Documentation

| Doc | What's in it |
|-----|-------------|
| [`ROADMAP.md`](ROADMAP.md) | Product vision, competitive landscape, feature roadmap |
| [`COMPETITIVE-UX.md`](COMPETITIVE-UX.md) | Deep competitive analysis — HeyGen, InVideo AI, Runway, Sora, Kling, Descript, LTX Studio |
| [`RESEARCH_TRANSCRIPTION.md`](RESEARCH_TRANSCRIPTION.md) | Open-source transcription research — WhisperX, pyannote, NeMo, diarization trade-offs |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |
| [`CLAUDE.md`](CLAUDE.md) | Dev setup, pipeline architecture, language support notes |

---

## Tests

```bash
.venv/bin/python -m pytest tests/ -q --ignore=tests/eval
# 102 tests
```
