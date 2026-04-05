# Transcription Signal Loss — Open Source Solutions

Research date: April 2026. Not yet implemented — investigation notes only.

---

## The Core Problem

Whisper outputs one undifferentiated text stream. A conversation between N speakers becomes
a wall of text with no attribution, no timing, no emotion, no overlap flags. Five distinct
information losses, each with different fix maturity.

---

## 1. Speaker Diarization — Who Said What

**The gap:** Whisper has no concept of speakers. Two people talking → merged transcript.

### WhisperX
- **Repo:** github.com/m-bain/whisperX — BSD-2, 21k stars
- **What it does:** Wraps pyannote.audio for diarization + wav2vec2 for forced word alignment. Outputs labeled turns: `[SPEAKER_00] word word word`
- **Drop-in fit:** Yes — same interface as Whisper, directly replaces `transcribe.py` logic
- **Catch:** Requires a HuggingFace token to pull the pyannote gated model. Diarization quality is "far from perfect" per the README — overlapping speech is explicitly flagged as a known failure.

### pyannote.audio (standalone, v4.0)
- **Repo:** github.com/pyannote/pyannote-audio — MIT, 9.5k stars
- **What it does:** The diarization engine underneath WhisperX. Version 4.0 ships `community-1`, which improves speaker counting and confusion vs 3.1. Sub-models for VAD, overlap detection, and speaker embedding are all separate and composable.
- **Speed:** ~31s per hour of audio on GPU
- **Catch:** HuggingFace token required. Linux/macOS only. GPU required for practical speed.

### NVIDIA NeMo (Sortformer)
- **Repo:** github.com/NVIDIA-NeMo/NeMo — Apache 2.0
- **What it does:** End-to-end Transformer diarizer trained on 7,500+ hours. Handles overlap natively (outputs simultaneous speaker labels). Streaming support.
- **Catch:** Hard cap at 4 simultaneous speakers. Full CUDA stack required. Overkill for local use — relevant if this pipeline scales to server deployment.

**Recommendation:** WhisperX for now. It solves diarization + word timestamps in one step and is a near drop-in for the current `transcribe.py`.

---

## 2. Word-Level Timestamps

**The gap:** Current `transcribe.py` discards all timing data. `make_video.sh` divides audio
evenly across images — blind to speech rhythm.

### WhisperX (wav2vec2 forced alignment)
- Produces timestamps at the word level via CTC alignment against a phoneme-level wav2vec2 model
- Accuracy: 88–93% on clean audio, 74–83% on spontaneous speech (200ms tolerance)
- **Limitation:** Fails on non-alphabetic tokens (numbers, currency, symbols). Requires a per-language wav2vec2 alignment model.

### faster-whisper (native DTW timestamps)
- **Repo:** github.com/SYSTRAN/faster-whisper — MIT, 21.9k stars
- CTranslate2-based Whisper, 4–8× faster than vanilla. Word timestamps derived from
  internal cross-attention via DTW — no external aligner needed, works on all languages.
- Less precise than forced alignment at phoneme level, but simpler and language-agnostic.

### CrisperWhisper (research, non-commercial)
- **Repo:** github.com/nyrahealth/CrisperWhisper — CC BY-NC 4.0 (non-commercial only)
- Fine-tuned Whisper trained to produce tighter attention-based alignments. Also preserves
  filler words ("um", "uh"). Ranked #1 on OpenASR verbatim leaderboard (Interspeech 2024).
- **Catch:** Non-commercial license and Python 3.10 only. Research use only.

### whisper-timestamped
- **Repo:** github.com/linto-ai/whisper-timestamped — GPLv3
- DTW on attention weights + **per-word confidence scores** (log probability) — unique value
  not exposed by WhisperX or faster-whisper natively.
- **Catch:** GPL license is viral for any product use.

**Recommendation:** faster-whisper for language-agnostic simplicity; WhisperX if diarization
is also needed (solves both problems at once).

---

## 3. Prosody and Emotion Detection

**The gap:** Pitch, speaking rate, volume, pauses, and emotional state are destroyed by
plain-text transcription. For this pipeline the loss is *acceptable* if scripts are rewritten
before TTS — but relevant if we ever want to preserve or classify speaker affect.

### Emotion Classification (neural, end-to-end)

**SpeechBrain + wav2vec2-IEMOCAP**
- HuggingFace: `speechbrain/emotion-recognition-wav2vec2-IEMOCAP`
- 4-class (angry/happy/neutral/sad), ~75–80% accuracy on IEMOCAP
- ~5 lines of Python via SpeechBrain's pretrained interface
- **Catch:** IEMOCAP is scripted/acted — degrades on natural in-the-wild speech

**emotion2vec (ACL 2024)**
- Repo: github.com/ddlBoJack/emotion2vec
- Self-supervised pretraining specifically for emotion representations (not fixed-class)
- More generalizable embeddings; fine-tune for your target domain

**EmoBox (Interspeech 2024)**
- Repo: github.com/emo-box/EmoBox
- Not a model — a benchmark toolkit covering 32 SER datasets in 14 languages
- Key finding: **WavLM-Large consistently tops intra- and cross-corpus SER** — if fine-tuning
  for emotion, start from WavLM-Large

### Prosody Feature Extraction (traditional)

**openSMILE**
- Repo: github.com/audeering/opensmile + Python wrapper
- C++ feature extractor: F0 (pitch), energy, MFCCs, formants, jitter, shimmer, HNR, speaking
  rate proxies. ComParE 2016 = 6,373 features
- **Catch:** Free for research only — commercial use requires a paid license. You get features,
  not predictions; need a downstream classifier.

**Parselmouth (Praat via Python)**
- `pip install praat-parselmouth` — GPL 3.0
- Python interface to Praat. Extracts pitch contours, intensity, formants, jitter, shimmer,
  HNR, articulation rate, pause duration — the complete prosody feature set
- **Catch:** GPL license. Not designed for batch processing.

**Recommendation:** For the current pipeline, this is low priority — prosody is rebuilt in
the TTS step. Revisit if we add emotion-conditioned TTS (Kokoro doesn't support it; would need
a different synthesis model).

---

## 4. Hallucination and Confidence Filtering

**The gap:** Whisper silently hallucinates text in silence, background noise, or music. No
canonical open source library exists — current state is a pragmatic patchwork.

### Silero VAD (most effective mitigation)
- **Repo:** github.com/snakers4/silero-vad — MIT
- Strip non-speech segments before feeding to Whisper. WhisperX and faster-whisper both
  integrate Silero VAD natively.
- Most hallucinations happen in silence/noise — VAD preprocessing cuts the majority of them.

### Whisper's built-in scoring parameters
Not a library — parameters available in the Whisper/faster-whisper API:
- `no_speech_threshold` (default 0.6): discard segment if no-speech probability exceeds this
- `logprob_threshold` (default -1.0): trigger fallback if avg log-prob drops below this
- `compression_ratio_threshold` (default 2.4): high ratio = repetition loop hallucination
- Community-validated combination: `compression_ratio_threshold=2.4, logprob_threshold=-0.5`
- Also: `condition_on_previous_text=False` cuts hallucination cascades across segments

### whisper-timestamped (per-word confidence)
- Exposes per-word and per-segment log-probability confidence scores
- Allows filtering low-confidence words/segments before they enter the script

### Calm-Whisper (2025 research — not packaged)
- arxiv 2505.12969: identifies 3 attention heads responsible for >75% of non-speech
  hallucinations. Selective fine-tuning cuts hallucination rate by ~84.5%.
- Not yet pip-installable.

**Recommendation:** VAD preprocessing (already in WhisperX) + set `condition_on_previous_text=False` + filter by `no_speech_prob` and `compression_ratio`. Whisper-timestamped for word-level confidence if precision matters.

---

## 5. Overlapping Speech Detection

**The gap:** When two speakers talk simultaneously, Whisper picks whichever is louder and
silently drops the other. The transcript has a hole where the overlap was.

### pyannote/overlapped-speech-detection
- HuggingFace: `pyannote/overlapped-speech-detection` — MIT, ~538k downloads/month
- Dedicated binary classifier: outputs time segments where ≥2 speakers are simultaneously
  active. 4 lines of Python.
- **Catch:** Based on pyannote 2.1 internals; not yet updated to community-1 model.
  Requires HuggingFace token.

### NeMo Sortformer
- Handles overlap natively by emitting simultaneous speaker labels (up to 4 speakers)
- Better at overlap than cascaded systems, which fail silently

**Honest state of the field:** Detection is solved well enough to flag overlap regions.
Transcribing overlapping speech accurately is an open research problem — no ASR system
handles it reliably. The practical response is to detect overlap regions and annotate them
as `[OVERLAP]` in the transcript rather than attempting to transcribe them.

---

## Summary and Priority Order

| Problem | Best Option | Effort | Priority |
|---------|-------------|--------|----------|
| Speaker diarization | WhisperX | Low (drop-in) | **High** — unlocks per-speaker TTS voices |
| Word timestamps | WhisperX (or faster-whisper) | Low (drop-in) | **High** — better video sync |
| Hallucination filtering | Silero VAD + Whisper params | Low (config) | **Medium** — silent data corruption risk |
| Overlapping speech | pyannote OSD | Medium | **Medium** — flag regions, don't transcribe |
| Emotion/prosody | WavLM-Large fine-tune | High | **Low** — only relevant if pipeline evolves to affect-aware TTS |

**First upgrade path:** Replace `transcribe.py` with WhisperX. Solves diarization + word
timestamps simultaneously. Single dependency swap. Unlocks speaker-attributed scripts →
multi-voice Kokoro TTS output.
