# Changelog

## [0.3.0] — 2026-05-19

### Features
- **SenseVoice-Small backend** (`transcribe.py`): default ASR backend via FunASR.
  Per-utterance language detection — handles Chinese/English code-switching that Whisper
  mangles. ~15× realtime on CPU. Chained with `fsmn-vad` so long audio (>30s) processes
  cleanly instead of being silently truncated to the first chunk.
- **Mac Voice Memos picker** (`app.py:list_voice_memos`): Tab 1 dropdown lists recent
  recordings from `CloudRecordings.db` (read-only URI mode). One click loads the `.m4a`
  into the audio component — no more drag-and-drop fights with the Voice Memos UI.
  `demo.launch(allowed_paths=…)` whitelists the recordings directory so Gradio doesn't
  reject paths outside the project tree.
- **Claude cleanup pass** (`transcribe.py:clean_transcript`): post-ASR Claude pass that
  fixes residual mis-reads — English jargon misheard as Chinese homophones (`Cco` →
  `Claude Code`), homophone errors, fragmented English. Default-on checkbox in Tab 1,
  also runs inside `run_full_pipeline`. Preserves every semantic unit, never paraphrases.
- **MLX backend selection** for word-timestamp and pyannote-diarization paths that
  SenseVoice cannot serve (separate from the SenseVoice transcript path).

### Fixes
- `_claude_label` now swallows Anthropic API failures and returns the unlabeled
  transcript instead of raising — workspace cap / network errors no longer crash Tab 1.
- `clean_transcript` falls back to the raw transcript on API failure or suspiciously
  short output (< 30% of input).
- Pyannote `DiarizationPipeline` arg rename: try `token=` first, fall back to
  `use_auth_token=` for older whisperx installs.
- `print(f"[{backend}] Saved: ...")` now uses the actual backend used for the call,
  not the global `_BACKEND` (relevant when SenseVoice falls through to MLX).

### Deps
- Added `funasr` to `requirements.txt`.

## [0.2.0] — 2026-04-05

### Features
- **Visual fallback chain** (`visual_sources.py`): Ken Burns zoompan animation → Pexels stock video → fal.ai Wan 2.1 T2V → Pillow static; auto-selects best available backend based on env vars
- **Image generation** (`generate_images.py`): Pillow-based title card renderer for Ken Burns and static backends
- **Video assembly** (`assemble_video.py`): scene-by-scene video assembly with per-scene audio/visual sync
- **Hook variants** (`hooks.py`): lifecycle callbacks for each pipeline stage
- **Scene graph** (`preproduction.py`): structured scene representation with duration, image prompt, TTS text
- **Repurpose** (`repurpose.py`): extract scene-length clips from finished video; merge short scenes
- **Settings persistence** (`settings.py`): Claude model selection, Whisper backend, API key status
- **Gradio UI** (`app.py`): 10-tab interface covering full pipeline — transcribe, TTS, topics, script, visuals, video, repurpose, settings

### Fixes
- Raise `max_tokens` cap to prevent JSON truncation on Extract Topics for long transcripts
- Remove unsupported `show_api` launch arg; add `settings.json` with sane defaults
- fal.ai response guard: raise `RuntimeError` on missing `video.url` instead of silent `None` crash
- Correct `acquire_visuals` docstring: priority order is fal → pexels → kenburns (not reversed)
- Progress callback now fires per-scene inside each backend loop (not post-hoc all-at-once)
- Temp dir leak: `shutil.rmtree(img_dir)` added before all return paths in `run_full_pipeline`
- HTML injection in diff view: `html.escape()` applied to all user-controlled strings
- Tab 10 (Repurpose) now auto-populates `scenes_json` from pipeline run output

### Tests
- 102 tests total (+32 vs baseline)
- New: `tests/test_repurpose_settings.py` — 16 tests covering `merge_short_scenes`, `extract_clips`, and `settings.py`

## [0.1.0] — 2026-03-?? (initial)

- Phase 1: brand context, section TTS, WhisperX upgrade, full pipeline UI
