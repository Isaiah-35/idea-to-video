"""Gradio UI for the idea-to-video pipeline — Phase 2 + 3 + 4."""
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import gradio as gr

from brand import load_brand, save_brand, brand_prefix
from preproduction import load_preproduction, save_preproduction, preproduction_prefix
from session import save_session, load_latest_session, build_scene_graph
from transcribe import transcribe, label_speakers
from extract_topics import extract_topics
from write_script import write_script, write_script_sections, STYLES
from kokoro_tts import generate, generate_sections
from speak import text_to_speech
from generate_images import generate_images
from hook_variants import generate_hook_variants
from repurpose import extract_clips
from settings import load_settings, save_settings, get_api_key_status
from visual_sources import acquire_visuals, detect_available_backends


# ── Helpers ───────────────────────────────────────────────────────────────────

KOKORO_VOICES = {
    "en": ["af_heart", "af_bella", "am_adam", "am_michael"],
    "zh": ["zf_xiaobei", "zf_xiaoni", "zm_yunjian"],
}

CLAUDE_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"]

_MODEL_COSTS = {
    "claude-sonnet-4-6":          ("$0.003/1K in + $0.015/1K out", "$0.01"),
    "claude-opus-4-6":            ("$0.015/1K in + $0.075/1K out", "$0.05"),
    "claude-haiku-4-5-20251001":  ("$0.00025/1K in + $0.00125/1K out", "$0.001"),
}


def _make_slide_images(topics: list[dict], img_dir: Path) -> None:
    """Generate title-card JPEGs — delegates to generate_images with pillow backend."""
    scenes = [{"title": t.get("title", f"Topic {i+1}"),
               "image_prompt": t.get("image_prompt", "")}
              for i, t in enumerate(topics)]
    generate_images(scenes, img_dir, backend="pillow", overwrite=True)


def _build_storyboard(topics: list[dict], sections: list[str]) -> str:
    """Return HTML card-per-topic storyboard view."""
    cards = []
    for i, (t, s) in enumerate(zip(topics, sections), start=1):
        cards.append(
            f'<div style="border:1px solid #555;border-radius:8px;padding:12px 16px;'
            f'margin:8px 0;background:#1a1a2e;">'
            f'<strong style="color:#a0a8ff;">Slide {i} · {t["title"]}</strong>'
            f'<p style="margin:8px 0 4px;color:#ccc;">{s}</p>'
            f'<small style="color:#888;">Image prompt: {t.get("image_prompt","—")}</small>'
            f'</div>'
        )
    return "".join(cards) if cards else "<p style='color:#888'>Run Write Script to preview storyboard.</p>"


def _extra_context(pp_goal, pp_aud, pp_emo, pp_cta) -> str:
    pp = {"goal": pp_goal, "audience": pp_aud, "emotion": pp_emo, "cta": pp_cta}
    return preproduction_prefix(pp)


def _diff_html(script_a: str, script_b: str, label_a: str = "Without brand",
               label_b: str = "With brand") -> str:
    """Return side-by-side HTML showing word-level additions in script_b vs script_a."""
    import difflib
    import html as _html
    words_a = script_a.split()
    words_b = script_b.split()
    sm = difflib.SequenceMatcher(None, words_a, words_b, autojunk=False)
    highlighted = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            highlighted.extend(_html.escape(w) for w in words_b[j1:j2])
        elif tag in ("replace", "insert"):
            for w in words_b[j1:j2]:
                highlighted.append(f'<span style="background:#1a4a1a;color:#6fda6f;">{_html.escape(w)}</span>')
        # deletions are simply omitted from the "with brand" side

    with_brand_html = " ".join(highlighted)
    return (
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">'
        f'<div><strong style="color:#aaa">{label_a}</strong>'
        f'<p style="color:#ccc;font-size:0.9em;white-space:pre-wrap;">{_html.escape(script_a)}</p></div>'
        f'<div><strong style="color:#6fda6f">{label_b}</strong>'
        f'<p style="color:#ccc;font-size:0.9em;">{with_brand_html}</p></div>'
        '</div>'
    )


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


def run_label_speakers(transcript, speaker_a, speaker_b, hints):
    if not transcript.strip():
        return "Transcribe audio first.", gr.update()
    a = speaker_a.strip() or "Speaker A"
    b = speaker_b.strip() or "Speaker B"
    claude_model = load_settings()["claude_model"]
    try:
        labeled = label_speakers(transcript, speaker_a=a, speaker_b=b,
                                 hints=hints, model=claude_model)
        return f"✓ Labeled {a} and {b}", labeled
    except Exception as e:
        return f"Error: {e}", gr.update()


# ── Tab 2: Extract Topics ─────────────────────────────────────────────────────

def run_extract_topics(transcript, num_topics, lang,
                       b_name, b_audience, b_tone, b_style):
    if not transcript.strip():
        return "Paste or transcribe text first.", "[]"
    brand = {"name": b_name, "audience": b_audience, "tone": b_tone, "style_notes": b_style}
    extra = preproduction_prefix()
    claude_model = load_settings()["claude_model"]
    try:
        topics = extract_topics(transcript, num_topics=int(num_topics), lang=lang,
                                brand=brand, extra_context=extra, model=claude_model)
    except Exception as e:
        return f"Error: {e}", "[]"
    display = "\n\n".join(
        f"{i+1}. {t['title']}\n   {t['summary']}\n   Image: {t['image_prompt']}"
        for i, t in enumerate(topics)
    )
    return display, json.dumps(topics, ensure_ascii=False, indent=2)


# ── Tab 3: Write Script ───────────────────────────────────────────────────────

def run_write_script(topics_json, lang, style,
                     b_name, b_audience, b_tone, b_style):
    try:
        topics = json.loads(topics_json)
    except json.JSONDecodeError:
        return "Invalid topics JSON. Run Extract Topics first.", "[]", ""
    if not topics:
        return "No topics found. Run Extract Topics first.", "[]", ""
    brand = {"name": b_name, "audience": b_audience, "tone": b_tone, "style_notes": b_style}
    extra = preproduction_prefix()
    claude_model = load_settings()["claude_model"]
    sections = write_script_sections(topics, lang=lang, style=style,
                                     brand=brand, extra_context=extra, model=claude_model)
    full_script = "\n\n".join(sections)
    storyboard = _build_storyboard(topics, sections)
    return full_script, json.dumps(sections, ensure_ascii=False, indent=2), storyboard


def run_compare_brand(topics_json, lang, style):
    """Generate script with and without brand, return side-by-side diff HTML."""
    try:
        topics = json.loads(topics_json)
    except (json.JSONDecodeError, TypeError):
        return "", "<p style='color:#888'>Run Write Script first to compare.</p>"
    if not topics:
        return "", "<p style='color:#888'>No topics — run Extract Topics first.</p>"
    extra = preproduction_prefix()
    claude_model = load_settings()["claude_model"]
    try:
        sections_no_brand = write_script_sections(topics, lang=lang, style=style,
                                                  brand=None, extra_context=extra,
                                                  model=claude_model)
        brand = load_brand()
        sections_with_brand = write_script_sections(topics, lang=lang, style=style,
                                                    brand=brand, extra_context=extra,
                                                    model=claude_model)
    except Exception as e:
        return "", f"<p style='color:red'>Error: {e}</p>"

    script_no = "\n\n".join(sections_no_brand)
    script_with = "\n\n".join(sections_with_brand)
    html = _diff_html(script_no, script_with)
    return script_no, html


# ── Tab 3: Generate Images ────────────────────────────────────────────────────

def run_generate_images_tab3(topics_json, sections_json):
    try:
        topics = json.loads(topics_json)
    except (json.JSONDecodeError, TypeError):
        return [], "", "Invalid topics JSON."
    if not topics:
        return [], "", "No topics — run Extract Topics first."

    img_dir = Path(tempfile.mkdtemp(prefix="itv_imgs_"))
    try:
        result_scenes = generate_images(topics, img_dir, backend="auto", overwrite=True)
    except Exception as e:
        return [], "", f"Error: {e}"

    gallery = [s["image_path"] for s in result_scenes if s.get("image_path")]
    return gallery, str(img_dir), f"Generated {len(gallery)} images in {img_dir}"


# ── Tab 3: Hook variants ──────────────────────────────────────────────────────

def run_generate_hooks(topics_json, lang, b_name, b_aud, b_tone, b_style):
    try:
        topics = json.loads(topics_json)
    except (json.JSONDecodeError, TypeError):
        return gr.update(choices=[], value=None, visible=False), "[]", "Invalid topics JSON."
    if not topics:
        return gr.update(choices=[], value=None, visible=False), "[]", "No topics — run Extract Topics first."
    brand = {"name": b_name, "audience": b_aud, "tone": b_tone, "style_notes": b_style}
    claude_model = load_settings()["claude_model"]
    try:
        variants = generate_hook_variants(topics, lang=lang, brand=brand, model=claude_model)
    except Exception as e:
        return gr.update(choices=[], value=None, visible=False), "[]", f"Error: {e}"

    choices = [f"{v['label']}: {v['hook']}" for v in variants]
    hooks_json = json.dumps(variants, ensure_ascii=False, indent=2)
    return gr.update(choices=choices, value=choices[0], visible=True), hooks_json, "3 hooks generated."


def run_select_hook(selected_label_hook, hooks_json, current_full_script, current_sections_json):
    """Prepend the selected hook as the first paragraph of the script."""
    if not selected_label_hook:
        return current_full_script, current_sections_json
    try:
        variants = json.loads(hooks_json) if hooks_json and hooks_json.strip() != "[]" else []
    except (json.JSONDecodeError, TypeError):
        return current_full_script, current_sections_json

    selected_hook = None
    for v in variants:
        label = v.get("label", "")
        if selected_label_hook.startswith(label + ":"):
            selected_hook = v["hook"]
            break
    if not selected_hook:
        return current_full_script, current_sections_json

    try:
        sections = json.loads(current_sections_json) if current_sections_json else []
    except (json.JSONDecodeError, TypeError):
        sections = []

    if sections:
        sections = [selected_hook + " " + sections[0]] + sections[1:]
    else:
        sections = [selected_hook]

    updated_script = "\n\n".join(sections)
    return updated_script, json.dumps(sections, ensure_ascii=False, indent=2)


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
                      b_name, b_audience, b_tone, b_style,
                      pp_goal, pp_aud, pp_emo, pp_cta,
                      visual_src,
                      progress=gr.Progress()):
    brand = {"name": b_name, "audience": b_audience, "tone": b_tone, "style_notes": b_style}
    pp = {"goal": pp_goal, "audience": pp_aud, "emotion": pp_emo, "cta": pp_cta}
    extra = preproduction_prefix(pp)
    claude_model = load_settings()["claude_model"]
    log_lines = []

    def log(msg):
        log_lines.append(msg)
        return "\n".join(log_lines)

    if audio is None:
        return None, None, "[]", "", "Record or upload audio first.", "", ""

    # Step 1: Transcribe
    progress(0.05, desc="Step 1/5 · Transcribing audio…")
    with tempfile.TemporaryDirectory() as tmp:
        transcript = transcribe(Path(audio), language=None if lang == "auto" else lang,
                                model_name=model, output_dir=Path(tmp))
    status = log(f"✓ Step 1/5 · Transcribed ({len(transcript.split())} words)")

    # Step 2: Extract topics
    progress(0.20, desc="Step 2/5 · Extracting topics with Claude…")
    try:
        topics = extract_topics(transcript, num_topics=int(num_topics), lang=lang,
                                brand=brand, extra_context=extra, model=claude_model)
    except Exception as e:
        return None, transcript, "[]", "[]", log(f"✗ Step 2/5 · Extract topics failed: {e}"), "", ""
    topics_json = json.dumps(topics, ensure_ascii=False, indent=2)
    status = log(f"✓ Step 2/5 · Extracted {len(topics)} topics")

    # Step 3: Write script
    progress(0.38, desc="Step 3/5 · Writing script with Claude…")
    try:
        sections = write_script_sections(topics, lang=lang, style=style,
                                         brand=brand, extra_context=extra, model=claude_model)
    except Exception as e:
        return None, transcript, topics_json, "[]", log(f"✗ Step 3/5 · Write script failed: {e}"), "", ""
    full_script = "\n\n".join(sections)
    status = log(f"✓ Step 3/5 · Script written ({len(sections)} sections)")

    # Step 3.5: Acquire visuals
    progress(0.52, desc="Step 3.5/5 · Acquiring visuals…")
    img_dir = Path(tempfile.mkdtemp(prefix="itv_pipeline_imgs_"))
    generated_image_paths: list[str | None] = []
    scenes_with_visuals: list[dict] = []
    if image_files:
        for i, img_path in enumerate(sorted(image_files), start=1):
            src = Path(img_path)
            dst = img_dir / f"img{i:03d}.jpg"
            dst.write_bytes(src.read_bytes())
            generated_image_paths.append(str(dst))
        # Treat uploaded images as pillow type for assembly
        scenes_with_visuals = build_scene_graph(topics, sections)
        for i, s in enumerate(scenes_with_visuals):
            s = dict(s)
            s["visual_path"] = generated_image_paths[i] if i < len(generated_image_paths) else None
            s["visual_type"] = "image"
            scenes_with_visuals[i] = s
        status = log(f"  (using {len(image_files)} uploaded images)")
    else:
        try:
            scenes_for_visuals = build_scene_graph(topics, sections)
            scenes_with_visuals = acquire_visuals(
                scenes_for_visuals, img_dir,
                backend=visual_src,
                progress_callback=lambda i, total, src: progress(
                    0.52 + 0.08 * (i / total),
                    desc=f"Step 3.5/5 · Generating visuals ({src}, {i}/{total})…"
                ),
            )
            generated_image_paths = [s.get("visual_path") for s in scenes_with_visuals]
            status = log(f"✓ Step 3.5/5 · {len(generated_image_paths)} visuals acquired ({visual_src})")
        except Exception as e:
            # Non-fatal: fall back to pillow title cards
            _make_slide_images(topics, img_dir)
            generated_image_paths = [str(img_dir / f"img{i+1:03d}.jpg") for i in range(len(topics))]
            scenes_with_visuals = build_scene_graph(topics, sections)
            for i, s in enumerate(scenes_with_visuals):
                s = dict(s)
                s["visual_path"] = generated_image_paths[i]
                s["visual_type"] = "image"
                scenes_with_visuals[i] = s
            status = log(f"  (visual acquisition warning: {e} — using title cards)")

    # Step 4: Generate TTS
    progress(0.68, desc="Step 4/5 · Generating Kokoro TTS (local, free)…")
    audio_out = Path(tempfile.mktemp(suffix=".wav"))
    durations_out = Path(tempfile.mktemp(suffix=".txt"))
    try:
        durations = generate_sections(sections, audio_out, lang=lang, voice=voice)
        durations_out.write_text("\n".join(f"{d:.3f}" for d in durations), "utf-8")
        status = log(f"✓ Step 4/5 · TTS generated ({sum(durations):.1f}s total)")
    except Exception as e:
        shutil.rmtree(img_dir, ignore_errors=True)
        return None, transcript, topics_json, full_script, log(f"✗ Step 4/5 · TTS failed: {e}"), "", ""

    # Step 5: Assemble video
    progress(0.84, desc="Step 5/5 · Assembling video with ffmpeg (local, free)…")
    video_out = Path(tempfile.mktemp(suffix=".mp4"))

    # Update scenes_with_visuals with per-section durations
    for i, s in enumerate(scenes_with_visuals):
        s = dict(s)
        s["duration_s"] = durations[i] if i < len(durations) else None
        scenes_with_visuals[i] = s

    visual_types = {s.get("visual_type") for s in scenes_with_visuals}
    if "video" in visual_types:
        try:
            from assemble_video import assemble
            assemble(audio_out, scenes_with_visuals, video_out)
        except Exception as e:
            shutil.rmtree(img_dir, ignore_errors=True)
            return None, transcript, topics_json, full_script, log(f"✗ Step 5/5 · Video assembly failed: {e}"), "", ""
    else:
        script_sh = Path(__file__).parent / "make_video.sh"
        result = subprocess.run(
            ["bash", str(script_sh), str(img_dir), str(audio_out), str(video_out), str(durations_out)],
            capture_output=True, text=True,
        )
        ffmpeg_log = (result.stdout + result.stderr).strip()
        if not video_out.exists() or video_out.stat().st_size < 1000:
            shutil.rmtree(img_dir, ignore_errors=True)
            return None, transcript, topics_json, full_script, log(f"✗ Step 5/5 · Video failed:\n{ffmpeg_log}"), "", ""

    progress(1.0, desc="Done!")
    status = log(f"✓ Step 5/5 · Video ready ({video_out.stat().st_size // 1024} KB)")

    # Build scene graph
    scenes = build_scene_graph(
        topics, sections,
        image_paths=generated_image_paths,
        durations=durations,
    )

    # Save session
    session_path = save_session({
        "saved_at": __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S"),
        "transcript": transcript,
        "topics_json": topics_json,
        "full_script": full_script,
        "sections_json": json.dumps(sections, ensure_ascii=False),
        "scenes_json": json.dumps(scenes, ensure_ascii=False),
        "lang": lang,
        "style": style,
        "brand": brand,
        "preproduction": pp,
    })
    session_msg = f"Session saved: {session_path.name}"
    scenes_json_out = json.dumps(scenes, ensure_ascii=False)
    shutil.rmtree(img_dir, ignore_errors=True)

    return str(video_out), transcript, topics_json, full_script, status, session_msg, scenes_json_out


# ── Tab 7: Session restore ────────────────────────────────────────────────────

def run_resume_session():
    state = load_latest_session()
    if not state:
        return "", "[]", "", gr.update(value="No saved sessions found.", visible=True)
    return (
        state.get("transcript", ""),
        state.get("topics_json", "[]"),
        state.get("full_script", ""),
        gr.update(value=f"Resumed: {state.get('saved_at', 'unknown')}", visible=True),
    )


# ── Tab 8: Pre-production ─────────────────────────────────────────────────────

def run_load_preproduction():
    pp = load_preproduction()
    return pp["goal"], pp["audience"], pp["emotion"], pp["cta"], "Loaded."

def run_save_preproduction(goal, audience, emotion, cta):
    save_preproduction({"goal": goal, "audience": audience, "emotion": emotion, "cta": cta})
    return "Saved to preproduction.json."

def run_preview_preproduction(goal, audience, emotion, cta):
    pp = {"goal": goal, "audience": audience, "emotion": emotion, "cta": cta}
    prefix = preproduction_prefix(pp)
    return prefix if prefix else "(no pre-production context set — fields are empty)"


# ── Tab 9: Settings ───────────────────────────────────────────────────────────

def _cost_estimate(model: str) -> str:
    pricing, approx = _MODEL_COSTS.get(model, ("unknown", "?"))
    return f"Estimated cost per run: ~{approx}  ({pricing}, ~3 calls × ~500 tokens)"


def run_save_settings(claude_model, whisper_backend):
    save_settings({"claude_model": claude_model, "whisper_backend": whisper_backend})
    return "Saved to settings.json.", _cost_estimate(claude_model)


def run_load_settings_ui():
    s = load_settings()
    model = s.get("claude_model", "claude-sonnet-4-6")
    backend = s.get("whisper_backend", "whisper")
    key_status = ("✓ ANTHROPIC_API_KEY set" if os.environ.get("ANTHROPIC_API_KEY")
                  else "✗ ANTHROPIC_API_KEY not set")
    return model, backend, _cost_estimate(model), key_status, "Loaded."


# ── Tab 10: Repurpose ─────────────────────────────────────────────────────────

def run_repurpose(video_path, scenes_json, max_duration):
    if video_path is None:
        return None, "Upload a video first."
    try:
        scenes = json.loads(scenes_json) if scenes_json and scenes_json.strip() not in ("", "[]") else []
    except (json.JSONDecodeError, TypeError):
        return None, "Invalid scenes JSON."
    if not scenes:
        return None, "No scenes found. Run the full pipeline first (Tab 7)."

    out_dir = Path(tempfile.mkdtemp(prefix="itv_clips_"))
    try:
        clips = extract_clips(Path(video_path), scenes, out_dir, max_duration=float(max_duration))
    except Exception as e:
        return None, f"Error: {e}"

    if not clips:
        return None, "No clips extracted (check scene durations and max_duration setting)."

    # Zip clips
    zip_path = Path(tempfile.mktemp(suffix=".zip"))
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for clip in clips:
            zf.write(clip["path"], Path(clip["path"]).name)

    log_lines = [f"Extracted {len(clips)} clips:"]
    for c in clips:
        log_lines.append(f"  {Path(c['path']).name}  ({c['duration_s']:.1f}s)")
    return str(zip_path), "\n".join(log_lines)


# ── Layout ────────────────────────────────────────────────────────────────────

_b  = load_brand()
_pp = load_preproduction()
_s  = load_settings()

with gr.Blocks(title="idea-to-video") as demo:
    gr.Markdown("# idea-to-video\n`Talk → Transcribe → Topics → Script → TTS → Video`")

    # Shared brand state (hidden, loaded once, synced from Tab 0)
    # CRITICAL: max 4 gr.State() before gr.Tabs() to avoid Gradio bug
    b_name  = gr.State(_b["name"])
    b_aud   = gr.State(_b["audience"])
    b_tone  = gr.State(_b["tone"])
    b_style = gr.State(_b["style_notes"])

    with gr.Tabs() as tabs:

        # ── Tab 0: Brand ──
        with gr.Tab("0 · Brand", id=0):
            gr.Markdown(
                "Set your brand context once — loaded automatically into every Claude call.\n\n"
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

            with gr.Accordion("Label speakers (for interviews / conversations)", open=False):
                gr.Markdown(
                    "Got a conversation between two people? Claude reads the transcript and labels "
                    "who said what — no audio re-processing needed.\n\n"
                    "The labeled transcript flows into Extract Topics, which will then attribute "
                    "insights, questions, and positions to each person by name."
                )
                with gr.Row():
                    t_speaker_a = gr.Textbox(label="Speaker A name", placeholder="e.g. Paul", scale=1)
                    t_speaker_b = gr.Textbox(label="Speaker B name", placeholder="e.g. Sam", scale=1)
                t_hints = gr.Textbox(
                    label="Optional hints (helps Claude distinguish voices)",
                    placeholder="e.g. Paul asks most of the questions. Sam explains technical details.",
                    lines=2,
                )
                t_label_btn    = gr.Button("Label Speakers", variant="primary")
                t_label_status = gr.Textbox(label="Status", interactive=False, lines=1)

            t_send = gr.Button("→ Extract Topics")

        # ── Tab 2: Extract Topics ──
        with gr.Tab("2 · Extract Topics", id=2):
            gr.Markdown("Transcript → key topics + image prompts via Claude. Pre-production and brand context applied automatically.")
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

            with gr.Accordion("Storyboard preview", open=False):
                gr.Markdown("*Card-per-slide view — verify structure before committing to TTS.*")
                w_storyboard = gr.HTML(value="<p style='color:#888'>Run Write Script to preview storyboard.</p>")

                # Generate Images (Phase 3)
                w_gen_img_btn = gr.Button("Generate Images", variant="secondary")
                w_gallery = gr.Gallery(label="Generated images", columns=3, visible=False)
                w_images_dir = gr.Textbox(label="Images dir", visible=False)
                w_img_status = gr.Textbox(label="Image status", interactive=False, visible=False)

            with gr.Accordion("Brand impact — with vs without", open=False):
                gr.Markdown("*Compare script with brand context applied vs. a generic script — word-level additions highlighted.*")
                w_compare_btn = gr.Button("Compare: script without brand context", variant="secondary")
                w_no_brand_script = gr.Textbox(label="Script without brand (hidden)", visible=False)
                w_diff_html_out = gr.HTML(value="<p style='color:#888'>Click Compare to see brand impact.</p>")

            with gr.Accordion("Hook variants", open=False):
                gr.Markdown("*Generate 3 opening hooks and pick the best one.*")
                w_hooks_btn = gr.Button("Generate 3 Opening Hooks", variant="secondary")
                w_hooks_radio = gr.Radio(choices=[], label="Pick a hook", visible=False)
                w_hooks_json = gr.Textbox(label="Hooks JSON", visible=False)
                w_hooks_status = gr.Textbox(label="Hook status", interactive=False, visible=False)

            w_send = gr.Button("→ Kokoro TTS")

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
                "## Talk about your idea → get a video\n\n"
                "Record yourself speaking — no script needed. The pipeline transcribes, "
                "extracts structure, writes a TTS script, generates speech, and assembles the video.\n\n"
                "**Brand context** (Tab 0) and **pre-production intent** (Tab 8 or accordion below) "
                "are applied automatically to every Claude call."
            )
            with gr.Row():
                p_audio  = gr.Audio(label="Record your idea (or upload)", sources=["microphone", "upload"], type="filepath")
                p_images = gr.File(label="Slide images (optional — auto-generated if empty)", file_count="multiple", file_types=["image"])
            with gr.Row():
                p_lang   = gr.Dropdown(["auto", "en", "zh"], value="auto", label="Language")
                p_model  = gr.Dropdown(["tiny", "base", "small", "medium", "large"], value="base", label="Whisper model")
                p_topics = gr.Slider(1, 10, value=5, step=1, label="Topics")
                p_style  = gr.Dropdown(STYLES, value="conversational", label="Style")
                p_voice  = gr.Dropdown(KOKORO_VOICES["en"], value="af_heart", label="TTS voice")
            with gr.Row():
                p_visual_src = gr.Dropdown(
                    ["auto", "kenburns", "pexels", "fal", "pillow"],
                    value="auto",
                    label="Visual source",
                    info="auto = best available based on API keys set in Tab 9",
                )

            with gr.Accordion("Pre-production context (optional — sets video intent)", open=False):
                gr.Markdown(
                    "*Fill these to shape narrative structure and pacing. "
                    "Saved permanently in Tab 8.*"
                )
                with gr.Row():
                    pp7_goal = gr.Textbox(label="Video goal", placeholder="e.g. Drive newsletter signups among indie hackers")
                    pp7_aud  = gr.Textbox(label="Audience", placeholder="e.g. indie hackers, 25–40, building solo")
                with gr.Row():
                    pp7_emo  = gr.Textbox(label="Desired emotion", placeholder="e.g. inspired and slightly uncomfortable")
                    pp7_cta  = gr.Textbox(label="CTA", placeholder="e.g. Subscribe at the link below")

            p_run    = gr.Button("Run Full Pipeline", variant="primary", size="lg")
            gr.Markdown(
                "_Free to iterate: Whisper transcription, Kokoro TTS, and ffmpeg video assembly "
                "all run locally. Only the 3 Claude API calls cost money — approximately $0.01 per run._"
            )
            p_video  = gr.Video(label="Output video")
            with gr.Accordion("Intermediate outputs", open=False):
                p_transcript = gr.Textbox(label="Transcript", lines=4, interactive=False)
                p_topics_out = gr.Textbox(label="Topics JSON", lines=6, interactive=False)
                p_script_out = gr.Textbox(label="Script", lines=8, interactive=False)
            p_status      = gr.Textbox(label="Progress log", lines=6, interactive=False)
            p_session_info = gr.Textbox(label="Session", interactive=False, visible=False)
            # Hidden: scenes JSON for Tab 10 repurpose
            p_scenes_json = gr.Textbox(label="Scenes JSON", visible=False)
            resume_btn    = gr.Button("Resume last session")

        # ── Tab 8: Pre-production ──
        with gr.Tab("8 · Pre-production", id=8):
            gr.Markdown(
                "Set the **intent** for this video. These 4 answers get prepended before brand context "
                "in every Claude call — shaping narrative structure, pacing, and call-to-action.\n\n"
                "**Use this for per-video goals.** Brand context (Tab 0) is for persistent identity."
            )
            with gr.Row():
                pp_goal_inp = gr.Textbox(label="Video goal", value=_pp["goal"],
                                         placeholder="e.g. Drive newsletter signups")
                pp_aud_inp  = gr.Textbox(label="Target audience", value=_pp["audience"],
                                         placeholder="e.g. indie hackers, 25–40, building solo")
            with gr.Row():
                pp_emo_inp  = gr.Textbox(label="Desired emotion at end", value=_pp["emotion"],
                                         placeholder="e.g. inspired and slightly uncomfortable")
                pp_cta_inp  = gr.Textbox(label="Call to action", value=_pp["cta"],
                                         placeholder="e.g. Subscribe at the link below")
            with gr.Row():
                pp_load    = gr.Button("Load from preproduction.json")
                pp_save    = gr.Button("Save to preproduction.json", variant="primary")
                pp_preview = gr.Button("Preview prompt prefix")
            pp_status      = gr.Textbox(label="Status", interactive=False)
            pp_preview_out = gr.Textbox(label="Prompt prefix preview (sent to Claude)", lines=8, interactive=False)

            pp_load.click(run_load_preproduction,
                          outputs=[pp_goal_inp, pp_aud_inp, pp_emo_inp, pp_cta_inp, pp_status])
            pp_save.click(run_save_preproduction,
                          [pp_goal_inp, pp_aud_inp, pp_emo_inp, pp_cta_inp], pp_status)
            pp_preview.click(run_preview_preproduction,
                             [pp_goal_inp, pp_aud_inp, pp_emo_inp, pp_cta_inp], pp_preview_out)

        # ── Tab 9: Settings ──
        with gr.Tab("9 · Settings", id=9):
            gr.Markdown(
                "Configure Claude model, Whisper backend, and view cost estimates.\n\n"
                "Changes take effect on the next pipeline run."
            )
            with gr.Row():
                cfg_model = gr.Dropdown(
                    CLAUDE_MODELS,
                    value=_s.get("claude_model", "claude-sonnet-4-6"),
                    label="Claude model",
                )
                cfg_whisper = gr.Dropdown(
                    ["whisper", "whisperx"],
                    value=_s.get("whisper_backend", "whisper"),
                    label="Whisper backend",
                )
            cfg_cost    = gr.Textbox(
                label="Cost estimate",
                value=_cost_estimate(_s.get("claude_model", "claude-sonnet-4-6")),
                interactive=False,
            )
            cfg_key     = gr.Textbox(
                label="API key status",
                value=("✓ ANTHROPIC_API_KEY set" if os.environ.get("ANTHROPIC_API_KEY")
                       else "✗ ANTHROPIC_API_KEY not set"),
                interactive=False,
            )
            cfg_pexels_status = gr.Textbox(
                label="Pexels API key",
                value=get_api_key_status()["pexels"],
                interactive=False,
            )
            cfg_fal_status = gr.Textbox(
                label="fal.ai API key",
                value=get_api_key_status()["fal"],
                interactive=False,
            )
            with gr.Row():
                cfg_save_btn = gr.Button("Save settings", variant="primary")
                cfg_load_btn = gr.Button("Reload from settings.json")
            cfg_status = gr.Textbox(label="Status", interactive=False)

            # Update cost estimate live when model changes
            cfg_model.change(_cost_estimate, cfg_model, cfg_cost)

            cfg_save_btn.click(run_save_settings, [cfg_model, cfg_whisper], [cfg_status, cfg_cost])
            cfg_load_btn.click(run_load_settings_ui,
                               outputs=[cfg_model, cfg_whisper, cfg_cost, cfg_key, cfg_status])

        # ── Tab 10: Repurpose ──
        with gr.Tab("10 · Repurpose", id=10):
            gr.Markdown(
                "## Cut long video into short clips\n\n"
                "Upload a video (or use the one from Tab 7) and extract per-scene clips.\n"
                "Scenes JSON is auto-filled from the last full pipeline run."
            )
            with gr.Row():
                rp_video = gr.Video(label="Input video")
                rp_scenes = gr.Textbox(label="Scenes JSON (auto-filled from Tab 7)", lines=6,
                                       placeholder='[{"title": "...", "duration_s": 12.3}, ...]')
            rp_max_dur = gr.Slider(15, 120, value=60, step=5, label="Max clip duration (seconds)")
            rp_run     = gr.Button("Extract Clips", variant="primary")
            rp_zip     = gr.File(label="Download clips (ZIP)")
            rp_log     = gr.Textbox(label="Log", lines=8, interactive=False)

            rp_run.click(run_repurpose, [rp_video, rp_scenes, rp_max_dur], [rp_zip, rp_log])

    # ── Wire pipeline ─────────────────────────────────────────────────────────

    # Tab 1 → Tab 2
    t_run.click(run_transcribe, [t_audio, t_lang, t_model], t_out)
    t_label_btn.click(
        run_label_speakers,
        [t_out, t_speaker_a, t_speaker_b, t_hints],
        [t_label_status, t_out],
    )
    t_send.click(lambda t: (t, gr.update(selected=2)), t_out, [e_transcript, tabs])

    # Tab 2 → Tab 3
    e_run.click(run_extract_topics,
                [e_transcript, e_num, e_lang, b_name, b_aud, b_tone, b_style],
                [e_display, e_json])
    e_send.click(lambda j: (j, gr.update(selected=3)), e_json, [w_topics, tabs])

    # Tab 3 → Tab 4
    w_run.click(run_write_script,
                [w_topics, w_lang, w_style, b_name, b_aud, b_tone, b_style],
                [w_out, w_sections, w_storyboard])
    w_run.click(lambda s: s, w_out, k_text)
    w_run.click(lambda s: s, w_sections, k_sections)
    w_send.click(
        lambda s, j: (s, j, gr.update(selected=4)),
        [w_out, w_sections], [k_text, k_sections, tabs]
    )

    # Tab 3: Generate images
    w_gen_img_btn.click(
        run_generate_images_tab3,
        [w_topics, w_sections],
        [w_gallery, w_images_dir, w_img_status],
    )
    w_gen_img_btn.click(
        lambda: (gr.update(visible=True), gr.update(visible=True)),
        None,
        [w_gallery, w_img_status],
    )

    # Tab 3: Brand comparison
    w_compare_btn.click(
        run_compare_brand,
        [w_topics, w_lang, w_style],
        [w_no_brand_script, w_diff_html_out],
    )

    # Tab 3: Hook variants
    w_hooks_btn.click(
        run_generate_hooks,
        [w_topics, w_lang, b_name, b_aud, b_tone, b_style],
        [w_hooks_radio, w_hooks_json, w_hooks_status],
    )
    w_hooks_btn.click(lambda: gr.update(visible=True), None, w_hooks_status)
    w_hooks_radio.change(
        run_select_hook,
        [w_hooks_radio, w_hooks_json, w_out, w_sections],
        [w_out, w_sections],
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

    # Tab 7 — full pipeline (pp7_* inline fields override shared State pp_*)
    p_run.click(
        run_full_pipeline,
        [p_audio, p_lang, p_model, p_topics, p_style, p_voice, p_images,
         b_name, b_aud, b_tone, b_style,
         pp7_goal, pp7_aud, pp7_emo, pp7_cta,
         p_visual_src],
        [p_video, p_transcript, p_topics_out, p_script_out, p_status, p_session_info, p_scenes_json],
    )
    p_run.click(lambda _: gr.update(visible=False), p_status, p_session_info)
    p_session_info.change(lambda v: gr.update(visible=bool(v)), p_session_info, p_session_info)

    # Auto-populate Tab 10 scenes from pipeline output
    p_scenes_json.change(lambda v: v if v and v != "[]" else gr.update(), p_scenes_json, rp_scenes)

    # Resume last session
    resume_btn.click(run_resume_session, [],
                     [p_transcript, p_topics_out, p_script_out, p_session_info])

    # Wire scenes JSON to Tab 10 repurpose: auto-fill from last session
    resume_btn.click(
        lambda: (load_latest_session() or {}).get("scenes_json", "[]"),
        None, rp_scenes,
    )


if __name__ == "__main__":
    demo.launch()
