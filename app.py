"""Gradio UI for the idea-to-video pipeline."""
import json
import subprocess
import tempfile
from pathlib import Path

import gradio as gr

from brand import load_brand, save_brand, brand_prefix
from transcribe import transcribe
from extract_topics import extract_topics
from write_script import write_script, write_script_sections, STYLES
from kokoro_tts import generate, generate_sections
from speak import text_to_speech


# ── Helpers ───────────────────────────────────────────────────────────────────

KOKORO_VOICES = {
    "en": ["af_heart", "af_bella", "am_adam", "am_michael"],
    "zh": ["zf_xiaobei", "zf_xiaoni", "zm_yunjian"],
}


def _make_slide_images(topics: list[dict], img_dir: Path) -> None:
    """Generate simple title-card JPEGs (one per topic) when no images are uploaded."""
    from PIL import Image, ImageDraw, ImageFont

    for i, topic in enumerate(topics, start=1):
        img = Image.new("RGB", (1920, 1080), color=(18, 18, 30))
        draw = ImageDraw.Draw(img)
        title = topic.get("title", f"Topic {i}")
        # Try to find a usable font; fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 96)
        except Exception:
            font = ImageFont.load_default()
        # Center text
        bbox = draw.textbbox((0, 0), title, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((1920 - w) // 2, (1080 - h) // 2), title, font=font, fill=(220, 220, 255))
        img.save(str(img_dir / f"img{i:03d}.jpg"), quality=92)


# ── Tab 0: Brand Context ──────────────────────────────────────────────────────

def run_load_brand():
    b = load_brand()
    return b["name"], b["audience"], b["tone"], b["style_notes"], "Loaded."

def run_save_brand(name, audience, tone, style_notes):
    save_brand({"name": name, "audience": audience, "tone": tone, "style_notes": style_notes})
    return "Saved to brand.json."

def run_preview_brand(name, audience, tone, style_notes):
    brand = {"name": name, "audience": audience, "tone": tone, "style_notes": style_notes}
    prefix = brand_prefix(brand)
    return prefix if prefix else "(no brand context set — fields are empty)"


# ── Tab 1: Transcribe ─────────────────────────────────────────────────────────

def run_transcribe(audio_path, lang, model):
    if audio_path is None:
        return "Record or upload an audio file first."
    language = None if lang == "auto" else lang
    with tempfile.TemporaryDirectory() as tmp:
        text = transcribe(Path(audio_path), language=language, model_name=model, output_dir=Path(tmp))
    return text


# ── Tab 2: Extract Topics ─────────────────────────────────────────────────────

def run_extract_topics(transcript, num_topics, lang, b_name, b_audience, b_tone, b_style):
    if not transcript.strip():
        return "Paste or transcribe text first.", "[]"
    brand = {"name": b_name, "audience": b_audience, "tone": b_tone, "style_notes": b_style}
    try:
        topics = extract_topics(transcript, num_topics=int(num_topics), lang=lang, brand=brand)
    except Exception as e:
        return f"Error: {e}", "[]"
    display = "\n\n".join(
        f"{i+1}. {t['title']}\n   {t['summary']}\n   Image: {t['image_prompt']}"
        for i, t in enumerate(topics)
    )
    return display, json.dumps(topics, ensure_ascii=False, indent=2)


# ── Tab 3: Write Script ───────────────────────────────────────────────────────

def run_write_script(topics_json, lang, style, b_name, b_audience, b_tone, b_style):
    try:
        topics = json.loads(topics_json)
    except json.JSONDecodeError:
        return "Invalid topics JSON. Run Extract Topics first.", "[]"
    if not topics:
        return "No topics found. Run Extract Topics first.", "[]"
    brand = {"name": b_name, "audience": b_audience, "tone": b_tone, "style_notes": b_style}
    sections = write_script_sections(topics, lang=lang, style=style, brand=brand)
    full_script = "\n\n".join(sections)
    return full_script, json.dumps(sections, ensure_ascii=False, indent=2)


# ── Tab 4: Kokoro TTS ─────────────────────────────────────────────────────────

def update_voice_choices(lang):
    voices = KOKORO_VOICES[lang]
    return gr.Dropdown(choices=voices, value=voices[0])

def run_kokoro(text, sections_json, lang, voice):
    if not text.strip():
        return None, None, "Enter some text first."
    out = Path(tempfile.mktemp(suffix=".wav"))
    durations_out = Path(tempfile.mktemp(suffix=".txt"))

    try:
        sections = json.loads(sections_json) if sections_json.strip() and sections_json.strip() != "[]" else None
    except (json.JSONDecodeError, AttributeError):
        sections = None

    if sections and len(sections) > 1:
        durations = generate_sections(sections, out, lang=lang, voice=voice)
        durations_out.write_text("\n".join(f"{d:.3f}" for d in durations), "utf-8")
        info = f"{out.name}  ({out.stat().st_size // 1024} KB, {len(sections)} sections)"
    else:
        generate(text, out, lang=lang, voice=voice)
        durations_out = None
        info = f"{out.name}  ({out.stat().st_size // 1024} KB)"

    return str(out), str(durations_out) if durations_out else None, info


# ── Tab 5: Speak (fallback TTS) ───────────────────────────────────────────────

def run_speak(text, rate, volume):
    if not text.strip():
        return None, "Enter some text first."
    out = Path(tempfile.mktemp(suffix=".wav"))
    text_to_speech(text, output_file=out, rate=int(rate), volume=float(volume))
    return str(out), f"{out.name}  ({out.stat().st_size // 1024} KB)"


# ── Tab 6: Make Video ─────────────────────────────────────────────────────────

def run_make_video(audio_path, durations_path, image_files, topics_json):
    if audio_path is None:
        return None, "Upload an audio file."

    with tempfile.TemporaryDirectory() as img_dir:
        img_dir_path = Path(img_dir)

        if image_files:
            for i, img_path in enumerate(sorted(image_files), start=1):
                src = Path(img_path)
                dst = img_dir_path / f"img{i:03d}.jpg"
                dst.write_bytes(src.read_bytes())
        else:
            # Auto-generate slide images from topic titles
            try:
                topics = json.loads(topics_json) if topics_json and topics_json.strip() != "[]" else []
            except (json.JSONDecodeError, TypeError):
                topics = []
            if not topics:
                return None, "Upload images or run Extract Topics first."
            _make_slide_images(topics, img_dir_path)

        out = Path(tempfile.mktemp(suffix=".mp4"))
        script = Path(__file__).parent / "make_video.sh"
        cmd = ["bash", str(script), str(img_dir_path), audio_path, str(out)]
        if durations_path and Path(durations_path).exists():
            cmd.append(durations_path)

        result = subprocess.run(cmd, capture_output=True, text=True)

    log = (result.stdout + result.stderr).strip()
    if not out.exists() or out.stat().st_size < 1000:
        return None, f"Failed:\n{log}"
    return str(out), log


# ── Tab 7: Run Full Pipeline ──────────────────────────────────────────────────

def run_full_pipeline(audio, lang, model, num_topics, style, voice, image_files,
                      b_name, b_audience, b_tone, b_style, progress=gr.Progress()):
    brand = {"name": b_name, "audience": b_audience, "tone": b_tone, "style_notes": b_style}
    log_lines = []

    def log(msg):
        log_lines.append(msg)
        return "\n".join(log_lines)

    if audio is None:
        return None, None, "[]", "", "Record or upload audio first."

    # 1. Transcribe
    progress(0.05, desc="Transcribing audio…")
    with tempfile.TemporaryDirectory() as tmp:
        transcript = transcribe(Path(audio), language=None if lang == "auto" else lang,
                                model_name=model, output_dir=Path(tmp))
    status = log(f"✓ Transcribed ({len(transcript.split())} words)")

    # 2. Extract topics
    progress(0.25, desc="Extracting topics…")
    try:
        topics = extract_topics(transcript, num_topics=int(num_topics), lang=lang, brand=brand)
    except Exception as e:
        return None, transcript, "[]", "[]", log(f"✗ Extract topics failed: {e}")
    topics_json = json.dumps(topics, ensure_ascii=False, indent=2)
    status = log(f"✓ Extracted {len(topics)} topics")

    # 3. Write script (sections)
    progress(0.45, desc="Writing script…")
    try:
        sections = write_script_sections(topics, lang=lang, style=style, brand=brand)
    except Exception as e:
        return None, transcript, topics_json, "[]", log(f"✗ Write script failed: {e}")
    full_script = "\n\n".join(sections)
    sections_json = json.dumps(sections, ensure_ascii=False, indent=2)
    status = log(f"✓ Script written ({len(sections)} sections)")

    # 4. Generate TTS
    progress(0.60, desc="Generating speech…")
    audio_out = Path(tempfile.mktemp(suffix=".wav"))
    durations_out = Path(tempfile.mktemp(suffix=".txt"))
    try:
        durations = generate_sections(sections, audio_out, lang=lang, voice=voice)
        durations_out.write_text("\n".join(f"{d:.3f}" for d in durations), "utf-8")
        status = log(f"✓ TTS generated ({sum(durations):.1f}s total)")
    except Exception as e:
        return None, transcript, topics_json, full_script, log(f"✗ TTS failed: {e}")

    # 5. Assemble video
    progress(0.80, desc="Assembling video…")
    with tempfile.TemporaryDirectory() as img_dir:
        img_dir_path = Path(img_dir)

        if image_files:
            for i, img_path in enumerate(sorted(image_files), start=1):
                src = Path(img_path)
                dst = img_dir_path / f"img{i:03d}.jpg"
                dst.write_bytes(src.read_bytes())
        else:
            _make_slide_images(topics, img_dir_path)
            status = log("  (auto-generated title cards)")

        video_out = Path(tempfile.mktemp(suffix=".mp4"))
        script = Path(__file__).parent / "make_video.sh"
        result = subprocess.run(
            ["bash", str(script), str(img_dir_path), str(audio_out), str(video_out), str(durations_out)],
            capture_output=True, text=True,
        )

    ffmpeg_log = (result.stdout + result.stderr).strip()
    if not video_out.exists() or video_out.stat().st_size < 1000:
        return None, transcript, topics_json, full_script, log(f"✗ Video failed:\n{ffmpeg_log}")

    progress(1.0, desc="Done!")
    status = log(f"✓ Video ready ({video_out.stat().st_size // 1024} KB)")
    return str(video_out), transcript, topics_json, full_script, status


# ── Layout ────────────────────────────────────────────────────────────────────

_b = load_brand()

with gr.Blocks(title="idea-to-video") as demo:
    gr.Markdown("# idea-to-video\n`Record → Transcribe → Topics → Script → TTS → Video`")

    # Shared brand state (hidden, loaded once, synced from Brand tab)
    b_name  = gr.State(_b["name"])
    b_aud   = gr.State(_b["audience"])
    b_tone  = gr.State(_b["tone"])
    b_style = gr.State(_b["style_notes"])

    with gr.Tabs() as tabs:

        # ── Tab 0: Brand ──
        with gr.Tab("0 · Brand", id=0):
            gr.Markdown(
                "Set your brand context once. Every Claude call reads it automatically.\n\n"
                "**Highest-leverage change:** this prefix shapes every generated script and topic."
            )
            with gr.Row():
                br_name = gr.Textbox(label="Brand / channel name", value=_b["name"], placeholder="e.g. TechSimplified")
                br_aud  = gr.Textbox(label="Target audience", value=_b["audience"], placeholder="e.g. software engineers, 25–40")
            with gr.Row():
                br_tone  = gr.Textbox(label="Tone", value=_b["tone"], placeholder="e.g. direct, curious, no buzzwords")
                br_style = gr.Textbox(label="Style notes", value=_b["style_notes"], placeholder="e.g. start with a concrete example, never use jargon")
            with gr.Row():
                br_load    = gr.Button("Load from brand.json")
                br_save    = gr.Button("Save to brand.json", variant="primary")
                br_preview = gr.Button("Preview prompt prefix")
            br_status      = gr.Textbox(label="Status", interactive=False)
            br_preview_out = gr.Textbox(label="Prompt prefix preview", lines=6, interactive=False)

            br_load.click(run_load_brand, outputs=[br_name, br_aud, br_tone, br_style, br_status])
            br_save.click(run_save_brand, [br_name, br_aud, br_tone, br_style], br_status)
            br_save.click(lambda n, a, t, s: (n, a, t, s), [br_name, br_aud, br_tone, br_style],
                          [b_name, b_aud, b_tone, b_style])
            br_preview.click(run_preview_brand, [br_name, br_aud, br_tone, br_style], br_preview_out)

        # ── Tab 1: Transcribe ──
        with gr.Tab("1 · Transcribe", id=1):
            gr.Markdown("Record live or upload audio → speech-to-text (WhisperX if installed, else Whisper).")
            t_audio = gr.Audio(label="Audio", sources=["microphone", "upload"], type="filepath")
            with gr.Row():
                t_lang  = gr.Dropdown(["auto", "en", "zh"], value="auto", label="Language")
                t_model = gr.Dropdown(["tiny", "base", "small", "medium", "large"], value="base", label="Whisper model")
            t_run  = gr.Button("Transcribe", variant="primary")
            t_out  = gr.Textbox(label="Transcript", lines=8)
            t_send = gr.Button("→ Extract Topics")

        # ── Tab 2: Extract Topics ──
        with gr.Tab("2 · Extract Topics", id=2):
            gr.Markdown("Transcript → key topics + image prompts via Claude.")
            e_transcript = gr.Textbox(label="Transcript", lines=5, placeholder="Paste transcript or auto-fill from Tab 1…")
            with gr.Row():
                e_num  = gr.Slider(1, 10, value=5, step=1, label="Number of topics")
                e_lang = gr.Dropdown(["en", "zh"], value="en", label="Language")
            e_run     = gr.Button("Extract Topics", variant="primary")
            e_display = gr.Textbox(label="Topics", lines=10, interactive=False)
            e_json    = gr.Textbox(label="Topics JSON", lines=4, visible=False)
            e_send    = gr.Button("→ Write Script")

        # ── Tab 3: Write Script ──
        with gr.Tab("3 · Write Script", id=3):
            gr.Markdown("Topics → per-section spoken script via Claude (one section per topic = one slide).")
            w_topics = gr.Textbox(label="Topics JSON", lines=4, placeholder="Auto-filled from Extract Topics…")
            with gr.Row():
                w_lang  = gr.Dropdown(["en", "zh"], value="en", label="Language")
                w_style = gr.Dropdown(STYLES, value="conversational", label="Style")
            w_run      = gr.Button("Write Script", variant="primary")
            w_out      = gr.Textbox(label="Full Script", lines=10)
            w_sections = gr.Textbox(label="Sections JSON", lines=4, visible=False)
            w_send     = gr.Button("→ Kokoro TTS")

        # ── Tab 4: Kokoro TTS ──
        with gr.Tab("4 · Kokoro TTS", id=4):
            gr.Markdown("Text → high-quality neural speech (Kokoro). Uses sections for timestamp-driven slide cuts.")
            k_text     = gr.Textbox(label="Script", lines=5, placeholder="Auto-filled from Write Script…")
            k_sections = gr.Textbox(label="Sections JSON", lines=2, visible=False)
            with gr.Row():
                k_lang  = gr.Dropdown(["en", "zh"], value="en", label="Language")
                k_voice = gr.Dropdown(KOKORO_VOICES["en"], value="af_heart", label="Voice")
            k_lang.change(update_voice_choices, k_lang, k_voice)
            k_run       = gr.Button("Generate", variant="primary")
            k_audio     = gr.Audio(label="Output", type="filepath")
            k_durations = gr.Textbox(label="Durations file path", visible=False)
            k_info      = gr.Textbox(label="Info", interactive=False)

        # ── Tab 5: Speak (fallback TTS) ──
        with gr.Tab("5 · Speak (fallback TTS)", id=5):
            gr.Markdown("Offline pyttsx3 TTS — no cloud, lower quality.")
            s_text   = gr.Textbox(label="Text", lines=4, placeholder="Enter text to speak…")
            with gr.Row():
                s_rate   = gr.Slider(80, 300, value=160, step=10, label="Rate (wpm)")
                s_volume = gr.Slider(0.0, 1.0, value=0.9, step=0.05, label="Volume")
            s_run   = gr.Button("Generate", variant="primary")
            s_audio = gr.Audio(label="Output", type="filepath")
            s_info  = gr.Textbox(label="Info", interactive=False)

        # ── Tab 6: Make Video ──
        with gr.Tab("6 · Make Video", id=6):
            gr.Markdown(
                "Audio + images → MP4.\n\n"
                "Leave images empty to auto-generate title cards from topic titles."
            )
            with gr.Row():
                v_audio  = gr.Audio(label="Audio (WAV/MP3)", type="filepath")
                v_images = gr.File(label="Images (JPG) — sorted by filename", file_count="multiple", file_types=["image"])
            v_durations = gr.Textbox(label="Durations file (auto-filled from TTS)", visible=False)
            v_topics    = gr.Textbox(label="Topics JSON (for auto-slide generation)", visible=False)
            v_run   = gr.Button("Make Video", variant="primary")
            v_video = gr.Video(label="Output")
            v_log   = gr.Textbox(label="Log", interactive=False)

        # ── Tab 7: Run Full Pipeline ──
        with gr.Tab("7 · Run Full Pipeline", id=7):
            gr.Markdown(
                "**End-to-end:** record → transcribe → topics → script → TTS → video.\n\n"
                "Brand context from Tab 0 is applied automatically.\n"
                "Leave images empty to use auto-generated title cards."
            )
            with gr.Row():
                p_audio  = gr.Audio(label="Audio", sources=["microphone", "upload"], type="filepath")
                p_images = gr.File(label="Images (optional)", file_count="multiple", file_types=["image"])
            with gr.Row():
                p_lang   = gr.Dropdown(["auto", "en", "zh"], value="auto", label="Language")
                p_model  = gr.Dropdown(["tiny", "base", "small", "medium", "large"], value="base", label="Whisper model")
                p_topics = gr.Slider(1, 10, value=5, step=1, label="Topics")
                p_style  = gr.Dropdown(STYLES, value="conversational", label="Style")
                p_voice  = gr.Dropdown(KOKORO_VOICES["en"], value="af_heart", label="TTS voice")
            p_run    = gr.Button("Run Full Pipeline", variant="primary", size="lg")
            p_video  = gr.Video(label="Output video")
            with gr.Accordion("Intermediate outputs", open=False):
                p_transcript = gr.Textbox(label="Transcript", lines=4, interactive=False)
                p_topics_out = gr.Textbox(label="Topics JSON", lines=6, interactive=False)
                p_script_out = gr.Textbox(label="Script", lines=8, interactive=False)
            p_status = gr.Textbox(label="Progress log", lines=6, interactive=False)

    # ── Wire pipeline ─────────────────────────────────────────────────────────

    # Tab 1 → Tab 2  (copy transcript + navigate)
    t_run.click(run_transcribe, [t_audio, t_lang, t_model], t_out)
    t_send.click(lambda t: (t, gr.update(selected=2)), t_out, [e_transcript, tabs])

    # Tab 2 → Tab 3  (copy topics JSON + navigate)
    e_run.click(run_extract_topics,
                [e_transcript, e_num, e_lang, b_name, b_aud, b_tone, b_style],
                [e_display, e_json])
    e_send.click(lambda j: (j, gr.update(selected=3)), e_json, [w_topics, tabs])

    # Tab 3 → Tab 4  (copy script + sections + navigate)
    w_run.click(run_write_script,
                [w_topics, w_lang, w_style, b_name, b_aud, b_tone, b_style],
                [w_out, w_sections])
    w_run.click(lambda s: s, w_out, k_text)
    w_run.click(lambda s: s, w_sections, k_sections)
    w_send.click(
        lambda s, j: (s, j, gr.update(selected=4)),
        [w_out, w_sections], [k_text, k_sections, tabs]
    )

    # Tab 4
    k_run.click(run_kokoro, [k_text, k_sections, k_lang, k_voice],
                [k_audio, k_durations, k_info])
    k_run.click(lambda d: d, k_durations, v_durations)
    e_run.click(lambda _, j: j, [e_display, e_json], v_topics)

    # Tab 5
    s_run.click(run_speak, [s_text, s_rate, s_volume], [s_audio, s_info])

    # Tab 6
    v_run.click(run_make_video, [v_audio, v_durations, v_images, v_topics], [v_video, v_log])

    # Tab 7 — full pipeline
    p_run.click(
        run_full_pipeline,
        [p_audio, p_lang, p_model, p_topics, p_style, p_voice, p_images,
         b_name, b_aud, b_tone, b_style],
        [p_video, p_transcript, p_topics_out, p_script_out, p_status],
    )


if __name__ == "__main__":
    demo.launch()
