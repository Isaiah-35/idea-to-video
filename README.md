# idea-to-video

From idea to video — AI-powered content pipeline that turns conversations into short videos.

## Pipeline

```
Record audio → Transcribe (Whisper) → Extract topics → Write scripts → TTS (Kokoro) → Slideshow video (ffmpeg)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `transcribe.py` | Speech-to-text using local Whisper model |
| `kokoro_tts.py` | High-quality neural TTS (Chinese + English) via Kokoro |
| `speak.py` | Basic TTS via pyttsx3 (fallback) |
| `make_video.sh` | Combine images + audio into slideshow video with fade transitions |

## Usage

### 1. Transcribe audio

```bash
python3 transcribe.py /path/to/recording.wav --lang zh --output-dir output/
```

### 2. Generate TTS audio

```bash
# English
python3 kokoro_tts.py --file script_en.txt --output audio_en.wav --lang en

# Chinese
python3 kokoro_tts.py --file script_zh.txt --output audio_zh.wav --lang zh
```

### 3. Create video

```bash
# Put images (img1.jpg, img2.jpg, ...) in topic folder, then:
bash make_video.sh ./topic_folder audio_en.wav video_en.mp4
```

## Requirements

- Python 3.10+
- ffmpeg
- `pip install -r requirements.txt`

## Voices

Kokoro voices:
- English: `af_heart` (default), `af_bella`, `am_adam`, `am_michael`
- Chinese: `zf_xiaobei` (default), `zf_xiaoni`, `zm_yunjian`
