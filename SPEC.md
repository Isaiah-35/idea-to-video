# idea-to-video — Feature Specification & Reconstruction Blueprint

**Purpose of this document.** A complete, implementation-agnostic specification of every
significant feature in `idea-to-video`, with enough technical detail (signatures, models, prompts,
data contracts, data flow, failure modes, config) to **reconstruct any part of it in another
system — specifically `Projects/loop`** (Tauri 2 / Rust + React) — without reading the Python
source. This is a spec, not a port. It describes *what* each feature does and the contracts it
depends on, so you can re-express it in whatever stack you choose.

- **Source system:** Python 3.12 pipeline + Gradio UI + one Bash/ffmpeg assembler.
- **Target for reconstruction:** `loop` (see §12 for the mapping).
- **One-line identity:** *Talk → Transcribe → Topics → Script → TTS → Video.*
- **Status note:** everything runs locally except the LLM (Anthropic) and optional image/video
  cloud backends. All cloud steps degrade gracefully.

---

## Table of contents

1. [System architecture](#1-system-architecture)
2. [Tech stack & dependencies](#2-tech-stack--dependencies)
3. [End-to-end data flow & artifacts](#3-end-to-end-data-flow--artifacts)
4. [Core data contracts](#4-core-data-contracts)
5. [Stage 1 — Transcription / ASR](#5-stage-1--transcription--asr)
6. [Stage 2 — Topic extraction](#6-stage-2--topic-extraction)
7. [Stage 3 — Script & hooks](#7-stage-3--script--hooks)
8. [Stage 4 — Text-to-speech](#8-stage-4--text-to-speech)
9. [Stage 5 — Visual acquisition](#9-stage-5--visual-acquisition)
10. [Stage 6 — Video assembly](#10-stage-6--video-assembly)
11. [Stage 7 — Repurpose](#11-stage-7--repurpose)
12. [Cross-cutting features](#12-cross-cutting-features) (Brand, Pre-production, Settings, Session, Voice Memos picker)
13. [Prompt library (verbatim)](#13-prompt-library-verbatim)
14. [Config surface](#14-config-surface)
15. [Orchestration & UI model](#15-orchestration--ui-model)
16. [Reconstruction mapping to Loop](#16-reconstruction-mapping-to-loop)
17. [Known inconsistencies & gotchas](#17-known-inconsistencies--gotchas)

---

## 1. System architecture

Seven decoupled pipeline stages. Each is an independent Python module runnable via CLI *and*
callable in-process by the Gradio orchestrator. Stages communicate through **plain data contracts**
(JSON topic list, scene graph, durations file, `img{NNN}.jpg` sequence) — never shared globals.

```
 ┌─────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐
 │  Audio  │──▶│ 1 Transcribe │──▶│ 2 Topics │──▶│ 3 Script │──▶│ 4 TTS     │
 │ (wav/m4a)│  │  (ASR+clean) │   │  (Claude)│   │  (Claude)│   │ (Kokoro)  │
 └─────────┘   └──────────────┘   └──────────┘   └────┬─────┘   └─────┬─────┘
                                                       │ image_prompt  │ wav + durations
                                                       ▼               │
                                                 ┌──────────┐          │
                                                 │ 5 Visuals│          │
                                                 │ (img/vid)│          │
                                                 └────┬─────┘          │
                                                      │ img{NNN}.jpg   │
                                                      ▼                ▼
                                                 ┌──────────────────────────┐   ┌────────────┐
                                                 │ 6 Assemble (ffmpeg)       │──▶│ 7 Repurpose│
                                                 │ 1920×1080 H.264/AAC MP4   │   │ short clips│
                                                 └──────────────────────────┘   └────────────┘

 Cross-cutting: Brand prefix · Pre-production prefix · Settings · Session snapshot · Scene graph
```

**Design invariants worth preserving in reconstruction:**
- Stages are independently runnable and independently testable (each has a `main()` CLI).
- All Claude steps degrade gracefully — a dead/blocked API never breaks the pipeline; the stage
  returns its best non-LLM output (raw transcript, etc.).
- The **scene graph** is the integration contract that binds topics + script + images + durations
  for the assembler.

---

## 2. Tech stack & dependencies

| Concern | Dependency | Notes |
|---|---|---|
| UI | `gradio` | Single `gr.Blocks`, 11 tabs |
| LLM | `anthropic` | Topics, script, hooks, transcript cleanup, speaker labeling |
| ASR (default) | `funasr` (SenseVoice-Small + fsmn-vad) | zh/en code-switching; ~1 GB model to `~/.cache/modelscope/` |
| ASR (fallbacks) | `mlx-whisper` → `whisperx` → `openai-whisper` | Apple-Silicon GPU → CT2 int8 → CPU reference |
| Diarization | `whisperx` + `pyannote` (needs `HF_TOKEN`) | Runs on MPS; else Claude-inferred turns |
| TTS (primary) | `kokoro>=0.9` | 24 kHz neural TTS |
| TTS (fallback) | `pyttsx3` | Offline OS TTS |
| Chinese text | `pypinyin`, `cn2an`, `jieba`, `ordered_set` | Kokoro zh normalization |
| Images/audio | `Pillow`, `numpy`, `soundfile` | Title cards, array ops, WAV I/O |
| Image gen (optional) | `fal_client` (FLUX), `openai>=1.0` (DALL·E 3) | Cloud, key-gated |
| Video assembly | **ffmpeg** (system binary) | Scaling, fades, concat, encode |
| Runtime constraint | **Python < 3.13** | Kokoro requirement; project uses 3.12 venv |

Env-var keys (all optional except Anthropic): `ANTHROPIC_API_KEY` (required), `PEXELS_API_KEY`,
`FAL_KEY`, `OPENAI_API_KEY`, `HF_TOKEN`. See §14.

---

## 3. End-to-end data flow & artifacts

Trace of the full pipeline (`run_full_pipeline`), naming every intermediate artifact:

| Step | Function | Input | Output artifact |
|---|---|---|---|
| 1 | `transcribe()` + `clean_transcript()` | audio filepath | `transcript: str` (+ `<stem>.txt`, `<stem>.words.json` in temp) |
| 2 | `extract_topics()` | transcript | `topics: list[dict]` → `topics_json` |
| 3 | `write_script_sections()` | topics | `sections: list[str]` → `full_script = "\n\n".join(sections)` |
| 3.5 | `acquire_visuals()` / uploaded imgs | scenes | `img_dir/img{NNN}.jpg` (or `scene{NNN}_<backend>.mp4`) → `generated_image_paths` |
| 4 | `generate_sections()` | sections | `audio_out.wav` (24 kHz) + `durations_out.txt` (one `%.3f` sec/line) |
| 5 | `make_video.sh` or `assemble()` | audio + imgs + durations | `video_out.mp4` (1920×1080 H.264/AAC) |
| 6 | `build_scene_graph()` + `save_session()` | all of the above | `scenes_json` + `~/.idea-to-video/sessions/<ts>.json` |
| 7 (opt) | `extract_clips()` | video + scenes | per-scene short MP4s (zipped) |

**Naming conventions (contract):**
- Still images: `img{NNN}.jpg`, **1-indexed**, zero-padded to 3 digits, `sort`-ordered.
- Video visuals (from `visual_sources`): `scene{NNN}_<backend>.<ext>` (renamed to `img{NNN}.jpg`
  for the slideshow path).
- Durations file: plain text, one float (seconds, `%.3f`) per line, aligned to section order.
- Output validation heuristic (used everywhere): file exists **and** size > 1000 bytes.

---

## 4. Core data contracts

These are the reusable schemas. Reconstruct these first; everything else consumes them.

**Topic** (produced by Stage 2, consumed by 3, 5):
```jsonc
{
  "title": "string",
  "summary": "string",              // 2-3 sentences; speaker-attributed in conversation mode
  "image_prompt": "string",         // visual description for image search/generation
  "speakers": ["Name", ...]         // present ONLY in conversation mode
}
```

**Scene** (the integration contract — `build_scene_graph`):
```jsonc
{
  "index": 0,
  "title": "string",
  "spoken_text": "string",          // the script section for this scene
  "image_prompt": "string",
  "image_path": "string|null",      // still-image path (Stage 5 image path)
  "visual_path": "string|null",     // richer visual (video/image) path — visual_sources
  "visual_type": "image|video",     // set by visual_sources
  "duration_s": 3.5                  // from Kokoro per-section durations
}
```
`build_scene_graph(topics, sections, image_paths=None, durations=None)` zips lists by index and
**raises `ValueError` on any length mismatch** (topics vs sections vs image_paths vs durations).

**Session snapshot** (`~/.idea-to-video/sessions/YYYYMMDD-HHMMSS.json`):
```jsonc
{
  "saved_at": "iso-ish timestamp",
  "transcript": "...", "topics_json": "...", "full_script": "...",
  "sections_json": "...", "scenes_json": "...",
  "lang": "en|zh", "style": "conversational|formal|educational",
  "brand": { ... }, "preproduction": { ... }
}
```
`load_latest_session()` returns the newest by filename sort, swallowing all errors → `None`.

**Durations file:** newline-delimited `%.3f` seconds, index-aligned to script sections.

---

## 5. Stage 1 — Transcription / ASR

**Module:** `transcribe.py`. The richest feature; the reason the tool handles bilingual audio well.

### 5.1 Backend selection (import-time, ordered)
1. **SenseVoice-Small** (FunASR) — default. Chosen because it does **per-utterance language
   auto-detection**, which is the only correct way to transcribe zh/en **code-switching** (Whisper
   locks one language per 30 s window). Disabled by env `SENSEVOICE_DISABLE=1`.
2. **MLX-Whisper** — Apple-Silicon GPU/ANE, ~10× CPU.
3. **WhisperX** — CTranslate2 int8, all CPU cores, pyannote diarization.
4. **openai-whisper** — reference CPU fallback.

Fall-through rule: SenseVoice **cannot** produce word timestamps or diarization, so if
`need_word_timestamps` **or** (`speaker_names` **and** `HF_TOKEN`) is requested, the call falls
through to MLX/WhisperX/Whisper automatically.

Models cached at module level (`_sensevoice_cache`, `_asr_cache`, `_align_cache`, `_diarize_cache`)
— loaded once per process.

### 5.2 Public API
```python
transcribe(file_path, *, language=None, model_name="base", output_dir=None,
           device=None, speaker_names=None, speaker_hints="",
           need_word_timestamps=False) -> str
transcribe_with_timestamps(file_path, *, language=None, model_name="base",
           device=None) -> tuple[str, list[dict]]
```
- `language`: `"en" | "zh" | None`; `None` → SenseVoice `"auto"` (the code-switching path).
- `model_name`: `tiny|base|small|medium|large` (Whisper-family only; SenseVoice ignores it).
- Writes `<stem>.txt` always, and `<stem>.words.json` when word segments exist.

### 5.3 SenseVoice specifics (reconstruct these exactly)
- Model: `iic/SenseVoiceSmall` (234 M params; supports zh/en/yue/ja/ko + auto), device **CPU**
  (MPS experimental in FunASR).
- **VAD chaining is required** for audio > 30 s: `vad_model="fsmn-vad"`,
  `vad_kwargs={"max_single_segment_time": 30000}` (ms). Without it, SenseVoice transcribes only one
  window and silently drops the tail.
- `generate(input=..., cache={}, language=<auto|zh|en|yue|ja|ko>, use_itn=True,
  batch_size_s=60, merge_vad=True, merge_length_s=15)`.
- **Tag stripping:** output contains special tags like `<|zh|><|NEUTRAL|><|Speech|><|woitn|>`;
  strip with regex `<\|[^|]*\|>` then `.strip()`.
- No word timestamps; returns `(text, [])`.

### 5.4 Diarization & speaker labeling
- **Audio-level (accurate):** pyannote `DiarizationPipeline` on MPS, `num_speakers=len(names)`, via
  WhisperX `assign_word_speakers`, then `_format_turns` merges consecutive same-speaker segments →
  `[Name]: text` lines. Requires `HF_TOKEN`.
- **Claude fallback (no HF_TOKEN):** `_claude_label(transcript, names, hints, model)` — see prompt
  in §13. Graceful: any API error → returns the unlabeled transcript.
- `is_labeled(text)` = regex `^\[.+\]:` (MULTILINE).

### 5.5 `clean_transcript()` — the bilingual cleanup pass
```python
clean_transcript(transcript, *, lang=None, model="claude-sonnet-4-6",
                 max_tokens=16384) -> str
```
Fixes typical zh/en ASR failure modes: English technical jargon transcribed as Chinese homophones
("colre" → "Claude Code", "launing on graph" → "LangGraph", "MCP servver" → "MCP server"), and
garbled code-switching. **Preserves length** (no summarizing) and any `[Name]:` labels. Full prompt
in §13.
- **Length guard:** if output is empty or `< 30%` of input length → keep original (treats it as a
  meta-response failure).
- **Graceful degradation:** any exception → returns the original transcript unchanged.

---

## 6. Stage 2 — Topic extraction

**Module:** `extract_topics.py`. Transcript → structured topics (first LLM stage).

```python
extract_topics(transcript, num_topics=5, lang="en", brand=None,
               extra_context="", model="claude-sonnet-4-6") -> list[dict]
```
- Auto-detects **conversation mode** (`^\[.+\]:` present) vs **monologue mode** and switches prompt
  (conversation mode adds `speakers` per topic and demands speaker-attributed summaries). See §13.
- `max_tokens=4096`, no temperature, single user message (no system role).
- Prompt context assembly (uniform across LLM stages): `ctx = extra_context + "\n\n" +
  brand_prefix(brand)` prepended to the task.
- Output: JSON array of Topic objects (§4). `_parse_json` strips ``` fences; on malformed JSON
  raises `ValueError` noting likely truncation. **No internal try/except** — callers handle errors.

---

## 7. Stage 3 — Script & hooks

**Module:** `write_script.py` + `hook_variants.py`.

### 7.1 Script
```python
write_script(topics, lang="en", style="conversational", brand=None,
             extra_context="", model="claude-sonnet-4-6") -> str
write_script_sections(topics, lang="en", style="conversational", brand=None,
             extra_context="", model="claude-sonnet-4-6") -> list[str]
```
- `STYLES = ["conversational", "formal", "educational"]`.
- `write_script` → one continuous narration; `write_script_sections` → **one paragraph per topic**
  (drives per-scene audio + durations). The orchestrator uses the sections variant.
- `max_tokens=2048`. Sections variant returns a JSON array of exactly `n` strings (count enforced
  only by prompt, not validated). Prompts in §13.

### 7.2 Hooks
```python
generate_hook_variants(topics, lang="en", brand=None, extra_context="",
                       model="claude-sonnet-4-6") -> list[dict]
```
- Returns **exactly 3** `{"label", "hook"}` objects with canonical labels **Curiosity / Empathy /
  Authority** (labels overwritten post-parse to guarantee order). Raises `ValueError` if count ≠ 3.
- The UI lets the user pick one hook, which is **prepended to `sections[0]`** of the script.

---

## 8. Stage 4 — Text-to-speech

**Modules:** `kokoro_tts.py` (primary), `speak.py` (offline fallback).

### 8.1 Kokoro (primary)
```python
generate(text, output, lang="en", voice=None) -> None
generate_sections(sections, output, lang="en", voice=None) -> list[float]
```
- Model: **Kokoro** `KPipeline(lang_code=...)`; `lang_code` `"a"` (English) / `"z"` (Chinese).
- **Sample rate: 24000 Hz** (hardcoded). Writes WAV via `soundfile`.
- **Default voices:** en → `af_heart`, zh → `zf_xiaobei`.
  UI voice menu: `{"en": ["af_heart","af_bella","am_adam","am_michael"],
  "zh": ["zf_xiaobei","zf_xiaoni","zm_yunjian"]}`.
- `generate_sections` concatenates all sections into one WAV **and returns per-section durations**
  (`len(section_audio)/24000`) — these become each scene's `duration_s` and drive the slideshow
  timing. Optional `--durations-out` writes one `%.3f`/line.
- No network, no config surface; empty text → exit 1.

### 8.2 pyttsx3 (fallback)
```python
text_to_speech(text, *, output_file=None, rate=160, volume=0.9) -> None
```
Offline OS TTS, English-oriented, engine-dependent sample rate. Lower quality; used when Kokoro is
unavailable or for quick previews.

---

## 9. Stage 5 — Visual acquisition

Two parallel subsystems. Both auto-select a backend from available API keys; **`generate_images.py`
has a billing-error cascade, `visual_sources.py` does not.**

### 9.1 `generate_images.py` — still title cards (`img{NNN}.jpg`)
```python
generate_images(scenes, output_dir, *, backend="auto", overwrite=False,
                progress_callback=None) -> list[dict]
generate_title_card_for_scene(scene, output_path) -> Path   # forces pillow
```
- Backends & priority (`auto`): **fal (FLUX)** → **DALL·E 3** → **Pexels photo** → **Pillow**.
- Model/endpoint constants:
  - fal: `fal-ai/flux/schnell`, `image_size="landscape_16_9"`, `num_images=1`,
    `num_inference_steps=4`.
  - DALL·E 3: `dall-e-3`, `size="1792x1024"`, `quality="standard"`.
  - Pexels: `GET https://api.pexels.com/v1/search` (`per_page=1`, `orientation=landscape`), uses
    `src.large2x`; header `Authorization: <key>`, `User-Agent: idea-to-video/1.0`.
  - Pillow: 1920×1080 gradient card `[10,10,30]→[25,20,60]`, numbered badge, centered title (font
    88), wrapped `image_prompt` (2 lines), rule at y=900; saved JPEG quality 92.
- **Billing cascade:** `_is_billing_error` matches `billing|quota|exhausted|hard limit|rate
  limit|429`. On a billing error it advances `fal→dalle3→pexels→pillow` and makes the fallback
  **sticky** for remaining scenes. Non-billing exceptions re-raise.
- Writes `output_dir/img{i:03d}.jpg` (1-indexed), skips existing unless `overwrite`.

### 9.2 `visual_sources.py` — motion visuals (video preferred)
```python
acquire_visuals(scenes, output_dir, *, backend="auto", overwrite=False,
                progress_callback=None) -> list[dict]   # sets visual_path + visual_type
```
- `VisualBackend = "auto"|"kenburns"|"pexels"|"fal"|"pillow"`; auto priority: **fal (Wan T2V)** →
  **Pexels video** → **Ken Burns** → Pillow. No cross-backend billing cascade (per-scene falls back
  to Ken Burns on failure).
- fal video: `fal-ai/wan-t2v`, `resolution="480p"`, `num_frames=81`, `frames_per_second=16`.
- Pexels video: `GET https://api.pexels.com/videos/search` (`per_page=3`, `orientation=landscape`,
  `size=medium`), picks `sd` quality file.
- **Ken Burns** (always available; needs ffmpeg): renders a Pillow card, then zoompan:
  ```
  ffmpeg -y -loop 1 -i card.jpg -filter_complex
   "[0:v]scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=<frames>:s=1920x1080:fps=25[out]"
   -map [out] -pix_fmt yuv420p -c:v libx264 -preset fast -crf 23 -t <duration> -an out.mp4
  ```
  `duration = scene.duration_s or 5.0`, `frames = max(1, int(duration*25))`.
- Names outputs `scene{i+1:03d}_<backend>.<ext>`, sets `visual_type` ∈ {image, video}.

---

## 10. Stage 6 — Video assembly

### 10.1 `make_video.sh` — slideshow assembler (still-image path)
`./make_video.sh <topic_dir> <audio_file> <output_file> [durations_file]`
- Probes audio duration (`ffprobe`), counts `img*.jpg`, exits 1 on empty/unreadable.
- Duration distribution: reads per-image seconds from `durations_file` (rounded up, min 2 s), else
  uniform ceil-division across images (min 2 s). `FADE=1`.
- Per-image filter: scale to fit 1920×1080 preserving aspect → pad/letterbox to full frame centered
  on black → `setsar=1` → 1 s fade-in + 1 s fade-out (`fade_out_start = D-1`).
- Concat + encode:
  ```
  ffmpeg -y <inputs> -i <audio> -filter_complex "<per-image filters>;concat=n=N:v=1:a=0,format=yuv420p[outv]" \
    -map [outv] -map <audio>:a -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k \
    -shortest -movflags +faststart <output>
  ```
- Output spec: **1920×1080, H.264 (libx264 preset fast CRF 23, yuv420p), AAC 128k**, `-shortest`,
  faststart. **Per-image in/out fades only — no crossfade.**
- Validation: exists **and** size > 1000 bytes (macOS `stat -f%z`).

### 10.2 `assemble_video.py` — orchestrator (mixed image/video path)
```python
assemble(audio_path, visuals, output_path, *, fade_duration=0.5) -> Path
```
- If any scene `visual_type == "video"` → `_assemble_video_clips` (trim each to `duration_s`,
  re-encode images, **stream-copy** existing clips, concat via `concat` demuxer, mux AAC audio,
  `-shortest`). Else → `_assemble_image_slideshow` (copies visuals to `img{NNN}.jpg`, writes
  durations, delegates to `make_video.sh`).
- `assemble_from_files(audio, image_paths, durations_path, output)` — back-compat wrapper over
  `make_video.sh`.
- **Note:** `fade_duration` is accepted but inert (no true crossfade anywhere).

---

## 11. Stage 7 — Repurpose

**Module:** `repurpose.py`. Pure ffmpeg (no LLM). Long rendered video → per-scene short clips.
```python
merge_short_scenes(scenes, target_duration=45.0) -> list[dict]   # greedy grouping
extract_clips(video_path, scenes, output_dir, max_duration=60.0) -> list[dict]
```
- `extract_clips` cuts one clip per scene using an accumulating `offset` (= start timestamp);
  skips scenes with `duration_s is None` (no advance) or `> max_duration` (advance, no cut).
- Output name `f"{i:03d}_{safe_title}.mp4"` (title sanitized, ≤ 50 chars).
- ffmpeg: `-ss <offset> -t <dur> -i <video> -c:v libx264 -c:a aac -movflags +faststart`.
- Per-clip graceful skip (failed/`< 100`-byte output silently dropped). Returns
  `[{title, path, duration_s}]` for successful cuts.
- UI zips the resulting clips.

---

## 12. Cross-cutting features

### 12.1 Brand (`brand.py`, `brand.json`)
`load_brand()/save_brand()/brand_prefix()`. Keys: `name, audience, tone, style_notes` (default
`""`). `brand_prefix` emits a `"Brand context (apply throughout):"` block of only non-empty fields,
or `""` if all empty (safe no-op). Prepended to every Claude prompt.

### 12.2 Pre-production (`preproduction.py`, `preproduction.json`)
`load/save_preproduction()`, `preproduction_prefix()`. Keys: `goal, audience, emotion, cta`. Emits a
`"Video pre-production context:"` block. **Ordering rule:** in every LLM call the context is
`preproduction_prefix` **first**, then `brand_prefix`, then the task.

### 12.3 Settings (`settings.py`, `settings.json`)
Keys: `claude_model` (default `claude-sonnet-4-6`), `whisper_backend` (default `whisper`).
`get_api_key_status()` reports anthropic/pexels/fal presence. UI model menu:
`["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"]`.

### 12.4 Session (`session.py`)
Auto-save/restore of full pipeline state to `~/.idea-to-video/sessions/YYYYMMDD-HHMMSS.json`; see
§4 for the schema. `build_scene_graph` also lives here (the integration contract).

### 12.5 Mac Voice Memos picker  ⭐ (directly relevant to your bilingual-memo use case)
- Dir: `~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings`.
- DB: `CloudRecordings.db`, opened **read-only via URI** so the live DB is never locked:
  `sqlite3.connect("file:<db>?mode=ro", uri=True)`.
- Query:
  ```sql
  SELECT ZCUSTOMLABEL, ZPATH, ZDATE, ZDURATION
  FROM ZCLOUDRECORDING WHERE ZPATH IS NOT NULL
  ORDER BY ZDATE DESC LIMIT ?;
  ```
- `ZDATE` is seconds since the **Core Data epoch** `2001-01-01T00:00:00Z` — convert accordingly.
- TCC/permissions: if the dir can't be read → returns a "Full Disk Access required" sentinel. If DB
  read fails → filesystem glob `*.m4a` sorted by mtime.
- Selected recording's `.m4a` path flows straight into the transcription input (`gr.Audio`), and
  the app whitelists the dir via `allowed_paths` at launch so Gradio can serve it.

---

## 13. Prompt library (verbatim)

Reconstruct these exactly — prompt wording is load-bearing for output quality/format.

### 13.1 `clean_transcript` (bilingual ASR cleanup)
```
You are cleaning a raw automatic-speech-recognition (ASR) transcript. {lang_hint}

The ASR often mishears English technical jargon as Chinese homophones, or garbles English
words inside Chinese sentences. Common examples:
  - 'colre', 'co re', 'clo code' → likely 'Claude Code', 'code', or 'Cline'
  - 'Cco', 'CC' → likely 'Claude Code'
  - 'MCP servver', 'MCP serv' → 'MCP server'
  - 'K见' → '回见'  (Chinese homophone for 'see you')
  - 'launing on graph' → 'LangGraph'
  - English word fragments stuck together: 'projectject' → 'project'

Rules:
1. Fix obvious ASR errors using context. Restore English technical terms (AI tool names,
   programming concepts, framework names).
2. Fix Chinese homophone errors that are clearly mishearings.
3. PRESERVE every semantic unit — do NOT summarize, condense, or paraphrase. Output should be
   roughly the same length as input.
4. Preserve [Name]: speaker labels if present, exactly as-is.
5. Preserve natural code-switching — keep English where the speaker meant English, Chinese where
   they meant Chinese. Never translate.
6. Light punctuation cleanup is fine; do not restructure paragraphs.
7. If a fragment is ambiguous, leave it alone rather than guess.

Return ONLY the cleaned transcript. No preamble, no explanations, no markdown fences.

Raw transcript:
{transcript}
```
`lang_hint` ∈ {zh: "The audio is primarily Chinese with English technical terms mixed in.",
en: "The audio is primarily English with some non-English terms.",
default: "The audio mixes Chinese and English (code-switching)."}. `max_tokens=16384`.

### 13.2 `_claude_label` (speaker labeling fallback)
```
Raw transcript of a two-person conversation between {A} and {B}. No speaker labels.
{hints}
Break into turns. Prefix each with [{A}]: or [{B}]:. Preserve every word exactly. Each turn on
a new line. Return ONLY the labeled transcript.

Transcript:
{transcript}
```
`max_tokens=8096`.

### 13.3 `extract_topics` — conversation mode
```
The following is a labeled conversation between {speakers}. Extract {N} key topics discussed.
{lang_note}

For each topic, the summary must preserve who said what — attribute insights, questions, and
positions to the correct speaker by name. Do not flatten the conversation into a single voice.

Return a JSON array only — no other text. Each element:
{"title": str, "summary": str (2-3 sentences, speaker-attributed),
 "image_prompt": str (visual description for image search/generation),
 "speakers": [list of speaker names who contributed to this topic]}

IMPORTANT: Summarize faithfully. Do not add conclusions, rhetorical framing, or concepts not
explicitly present in the transcript.

Transcript:
{transcript}
```
Monologue mode is identical minus speaker attribution and the `speakers` field.
`lang_note` = "Respond in Chinese." / "Respond in English." `max_tokens=4096`.

### 13.4 `write_script_sections`
```
{ctx}Write a {style} script for a short video. {lang_note}

There are exactly {N} topics. Write exactly one spoken paragraph per topic.
Requirements:
- Plain spoken prose only — no headers, bullets, markdown, em-dashes, or rhetorical questions
- EXACTLY 2-4 sentences per section — hard limit, no exceptions
- Write as natural speech, not written content: avoid listicle phrasing, staccato conditionals,
  and performative hooks
- Smooth transitions between sections

Topics:
{topics_text}

Return a JSON array of exactly {N} strings — one string per topic section. No other text.
```
(`write_script` non-sections variant: same intent, "2-4 sentences per topic", "1-3 minutes",
returns plain text.) `max_tokens=2048`.

### 13.5 `generate_hook_variants`
```
{ctx}I'm creating a short video covering these topics: {titles}.

Write 3 distinct opening hooks for this video. {lang_note}

Each hook is 1-3 sentences of plain spoken prose — no headers, no markdown.
The three hooks must use exactly these rhetorical stances:
1. "Curiosity" — open with an intriguing question or surprising fact
2. "Empathy" — open by naming a pain the viewer already feels
3. "Authority" — open with a confident, direct statement of stakes or expertise

Return a JSON array of exactly 3 objects with keys "label" and "hook".
Labels must be exactly: "Curiosity", "Empathy", "Authority" in that order.
No other text.
```
`max_tokens=2048`.

---

## 14. Config surface

| Env var | Required | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | topics, script, hooks, cleanup, labeling |
| `PEXELS_API_KEY` | No | Pexels photo/video backends |
| `FAL_KEY` | No | fal FLUX images / Wan T2V video |
| `OPENAI_API_KEY` | No | DALL·E 3 images |
| `HF_TOKEN` | No | WhisperX/pyannote diarization (else Claude-inferred turns) |
| `SENSEVOICE_DISABLE=1` | No | force a Whisper backend instead of SenseVoice |

On-disk config (all next to source, `load_*`/`save_*` merged over defaults): `brand.json`,
`preproduction.json`, `settings.json`. Sessions: `~/.idea-to-video/sessions/`. ASR model cache:
`~/.cache/modelscope/` (~1 GB SenseVoice on first run).

---

## 15. Orchestration & UI model

Single Gradio `gr.Blocks`, **11 tabs**, one per stage plus config/session. Cross-tab data moves via
**component-to-component `lambda` wiring + tab switch** (`gr.update(selected=N)`), not global state —
the only `gr.State` objects are the 4 brand fields (a documented Gradio-bug workaround: max 4
`gr.State` before `gr.Tabs()`).

| id | Tab | Drives |
|---|---|---|
| 0 | Brand | `brand` |
| 1 | Transcribe (+ Voice Memos picker, Claude cleanup) | `transcribe` |
| 2 | Extract Topics | `extract_topics` |
| 3 | Write Script (+ images, brand-diff, hooks) | `write_script`, `generate_images`, `hook_variants` |
| 4 | Kokoro TTS | `kokoro_tts` |
| 5 | Speak (fallback) | `speak` |
| 6 | Make Video | `make_video.sh`, title cards |
| 7 | Run Full Pipeline | everything + `session`, `visual_sources`, `assemble_video` |
| 8 | Pre-production | `preproduction` |
| 9 | Settings | `settings` |
| 10 | Repurpose | `repurpose` |

Key cross-tab flows: Tab 1 → 2 (transcript), 2 → 3 & 2 → 6 (topics json), 3 → 4 (script + sections),
3 → 6 (images), 4 → 6 (audio + durations), 6/7 → 10 (video + scenes). Auto-fill wiring is what makes
the multi-tab flow feel like one pipeline.

---

## 16. Reconstruction mapping to Loop

`loop` is Tauri 2 (Rust backend `apps/desktop/src-tauri`, React 19 frontend `apps/desktop/src`,
shared TS in `packages/shared`). It already **captures** meetings (live macOS SFSpeechRecognizer /
OpenAI Whisper / AssemblyAI transcription + FluidAudio diarization + a meeting recorder that writes
`audio.wav`). idea-to-video adds the **creation** half. Feature-by-feature target:

| idea-to-video feature | Loop reconstruction target | Notes |
|---|---|---|
| **SenseVoice zh/en ASR** | New local provider via `sherpa-rs` (Rust bindings to sherpa-onnx; has `OfflineRecognizer` + `OfflineSenseVoiceModelConfig`, static-links, downloads prebuilt lib at build). Model + VAD downloaded on first use (mirror FluidAudio pattern). Add a `TranscriptionProvider::SenseVoice` variant in `capture/audio.rs`; VAD-chain long audio via silero VAD. | The single highest-value addition for bilingual memos. Best fit is a **post-meeting whole-file re-transcription** of the recorder's `audio.wav`, plus optionally a selectable live provider. |
| **`clean_transcript` cleanup** | Rust fn + Tauri command reusing loop's existing `ClaudeClient::complete` (`llm/mod.rs`) — transcript as `context`, the §13.1 prompt as `prompt`. Port the length-guard (<30% → keep original) and graceful-degradation. | Runs on the whole transcript (post-meeting), not per live chunk. |
| **Voice Memos picker** | Rust: open `CloudRecordings.db` read-only (`?mode=ro`), same SQL (§12.5), Core-Data-epoch conversion; expose selected `.m4a` to the frontend. | `rusqlite` is already a loop dep. |
| Topics / script / hooks | Frontend feature calling loop's LLM router (`get_suggestion`) with the §13 prompts; store outputs alongside the meeting. | Pure LLM; no new native deps. |
| Kokoro TTS | Rust sidecar or a sherpa-onnx TTS model (loop has no TTS today). | Heavier; optional. |
| Image gen / video assembly | Out of loop's current scope (it's an overlay, not a renderer). Reconstruct only if you want a full idea→video path inside loop. | ffmpeg would become a new system dep. |
| Scene graph / session | Map onto loop's existing recorder DB (meetings/turns/media) rather than JSON snapshots. | Reuse, don't reinvent. |

**Recommended reconstruction order for Loop:** (1) SenseVoice provider + (2) `clean_transcript` —
together they give loop accurate bilingual meeting transcripts, which is the immediate need. Topics/
script/hooks are a cheap follow-on since loop already has an LLM router. TTS/images/assembly are
only worth it if you want loop to *produce* videos, not just better transcripts.

---

## 17. Known inconsistencies & gotchas

- **Default-ASR-backend mismatch:** `settings.json` defaults `whisper_backend="whisper"`, but the
  import-time chooser prefers SenseVoice if `funasr` is installed (and `requirements.txt` calls
  SenseVoice "the default backend"). The `settings.json` value only affects the Whisper-family
  fallback selection; SenseVoice-vs-Whisper is decided by import availability + `SENSEVOICE_DISABLE`.
- **`fade_duration` is inert** in `assemble_video.py` — there is no true crossfade anywhere, only
  per-image 1 s in/out fades in `make_video.sh`.
- **No section-count validation** in `write_script_sections` — relies on the prompt to return `N`
  strings; a mismatch will later trip `build_scene_graph`'s `ValueError`.
- **`extract_topics` / `hook_variants` raise on bad JSON** (no internal fallback) — the orchestrator
  wraps them; a reconstruction should decide where to put the try/except.
- **Two visual subsystems diverge:** `generate_images` (stills, billing cascade) vs `visual_sources`
  (motion, per-scene Ken Burns fallback, no billing cascade) — different backend priorities.
- **Temperature is never set** on any Claude call — decide whether to pin it on reconstruction.
- **No system prompt** is used — brand + pre-production context are folded into the single user
  message.
- Voice Memos picker needs **Full Disk Access** (TCC) for the running terminal/app; without it the
  picker returns a guidance sentinel and falls back to a filesystem glob.

---

*Generated as a reconstruction spec; no engineering/porting was performed. Source of truth is the
`idea-to-video` codebase at the time of writing.*
