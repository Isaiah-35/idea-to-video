"""Visual acquisition: Ken Burns → Pexels → fal.ai → Pillow title card."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal

from generate_images import generate_title_card_for_scene

VisualBackend = Literal["auto", "kenburns", "pexels", "fal", "pillow"]


def _auto_backend() -> VisualBackend:
    """Select best available backend based on env vars."""
    if os.environ.get("FAL_KEY"):
        return "fal"
    if os.environ.get("PEXELS_API_KEY"):
        return "pexels"
    return "kenburns"


def detect_available_backends() -> dict[str, bool]:
    """Return dict of available backends for UI display."""
    return {
        "kenburns": True,           # always available (ffmpeg + PIL)
        "pexels": bool(os.environ.get("PEXELS_API_KEY")),
        "fal": bool(os.environ.get("FAL_KEY")),
        "pillow": True,
    }


# ── Ken Burns ──────────────────────────────────────────────────────────────────

def _kenburns_single(scene: dict, index: int, output_dir: Path, overwrite: bool) -> str:
    """Animate a single Pillow title card with Ken Burns zoom effect. Returns output path str."""
    out_path = output_dir / f"scene{index + 1:03d}_kenburns.mp4"
    if not overwrite and out_path.exists():
        return str(out_path)

    duration = scene.get("duration_s") or 5.0
    frames = max(1, int(duration * 25))

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_f:
        tmp_jpg = Path(tmp_f.name)

    try:
        generate_title_card_for_scene(scene, tmp_jpg)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(tmp_jpg),
            "-filter_complex",
            (
                f"[0:v]scale=8000:-1,"
                f"zoompan=z='min(zoom+0.0015,1.5)'"
                f":x='iw/2-(iw/zoom/2)'"
                f":y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s=1920x1080:fps=25[out]"
            ),
            "-map", "[out]",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-t", f"{duration:.2f}",
            "-an",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg Ken Burns failed for scene {index + 1}:\n{result.stderr}"
            )
    finally:
        try:
            tmp_jpg.unlink(missing_ok=True)
        except Exception:
            pass

    return str(out_path)


def _acquire_kenburns(
    scenes: list[dict], output_dir: Path, overwrite: bool, progress_cb=None
) -> list[dict]:
    """Animate each title card with Ken Burns zoompan. Returns scenes with visual_path set."""
    import shutil
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is required for Ken Burns backend. Install it with: brew install ffmpeg"
        )
    result = list(scenes)
    total = len(result)
    for i, scene in enumerate(result):
        scene = dict(scene)
        scene["visual_path"] = _kenburns_single(scene, i, output_dir, overwrite)
        scene["visual_type"] = "video"
        result[i] = scene
        if progress_cb:
            progress_cb(i + 1, total, "kenburns")
    return result


# ── Pillow static ──────────────────────────────────────────────────────────────

def _acquire_pillow(
    scenes: list[dict], output_dir: Path, overwrite: bool, progress_cb=None
) -> list[dict]:
    """Generate static Pillow title cards. Returns scenes with visual_path set."""
    result = list(scenes)
    total = len(result)
    for i, scene in enumerate(result):
        scene = dict(scene)
        out_path = output_dir / f"scene{i + 1:03d}_pillow.jpg"
        if not overwrite and out_path.exists():
            scene["visual_path"] = str(out_path)
            scene["visual_type"] = "image"
            result[i] = scene
        else:
            generate_title_card_for_scene(scene, out_path)
            scene["visual_path"] = str(out_path)
            scene["visual_type"] = "image"
            result[i] = scene
        if progress_cb:
            progress_cb(i + 1, total, "pillow")
    return result


# ── Pexels ────────────────────────────────────────────────────────────────────

def _extract_keywords(image_prompt: str, max_words: int = 4) -> str:
    """Extract searchable keywords from an image prompt."""
    stop = {
        "a", "an", "the", "with", "and", "or", "of", "in", "on", "at",
        "to", "for", "is", "are", "that", "this", "shows", "depicting",
    }
    words = [w for w in re.findall(r'\b[a-zA-Z]+\b', image_prompt.lower()) if w not in stop]
    return " ".join(words[:max_words])


def _acquire_pexels(
    scenes: list[dict], output_dir: Path, overwrite: bool, progress_cb=None
) -> list[dict]:
    """Download stock video from Pexels API for each scene."""
    api_key = os.environ["PEXELS_API_KEY"]
    result = list(scenes)
    total = len(result)

    for i, scene in enumerate(result):
        scene = dict(scene)
        query = _extract_keywords(scene.get("image_prompt", scene.get("title", "abstract")), max_words=4)
        url = (
            f"https://api.pexels.com/videos/search"
            f"?query={urllib.parse.quote(query)}&per_page=3&orientation=landscape&size=medium"
        )
        req = urllib.request.Request(url, headers={"Authorization": api_key})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
        except Exception:
            data = {"videos": []}

        videos = data.get("videos", [])
        if not videos:
            # fallback to kenburns for this scene
            scene["visual_path"] = _kenburns_single(scene, i, output_dir, overwrite)
            scene["visual_type"] = "video"
            result[i] = scene
            continue

        # Pick the SD quality file (smallest that's still watchable)
        video_files = videos[0].get("video_files", [])
        sd_file = next((f for f in video_files if f.get("quality") == "sd"), video_files[0])

        out_path = output_dir / f"scene{i + 1:03d}_pexels.mp4"
        if not overwrite and out_path.exists():
            scene["visual_path"] = str(out_path)
            scene["visual_type"] = "video"
            result[i] = scene
            continue

        urllib.request.urlretrieve(sd_file["link"], str(out_path))
        scene["visual_path"] = str(out_path)
        scene["visual_type"] = "video"
        result[i] = scene
        if progress_cb:
            progress_cb(i + 1, total, "pexels")

    return result


# ── fal.ai ────────────────────────────────────────────────────────────────────

def _acquire_fal(
    scenes: list[dict], output_dir: Path, overwrite: bool, progress_cb=None
) -> list[dict]:
    """Generate AI video via fal.ai Wan 2.1."""
    try:
        import fal_client  # noqa: F401
    except ImportError:
        raise ImportError("fal.ai backend requires: pip install fal-client")

    import fal_client

    result = list(scenes)
    total = len(result)
    for i, scene in enumerate(result):
        scene = dict(scene)
        out_path = output_dir / f"scene{i + 1:03d}_fal.mp4"
        if not overwrite and out_path.exists():
            scene["visual_path"] = str(out_path)
            scene["visual_type"] = "video"
            result[i] = scene
            continue

        fal_result = fal_client.subscribe("fal-ai/wan-t2v", {
            "input": {
                "prompt": scene.get("image_prompt", scene.get("title", "abstract visual")),
                "resolution": "480p",
                "num_frames": 81,
                "frames_per_second": 16,
            }
        })
        video_url = (fal_result.get("video") or {}).get("url")
        if not video_url:
            raise RuntimeError(
                f"fal.ai returned unexpected response shape for scene {i}: {fal_result!r}"
            )
        urllib.request.urlretrieve(video_url, str(out_path))
        scene["visual_path"] = str(out_path)
        scene["visual_type"] = "video"
        result[i] = scene
        if progress_cb:
            progress_cb(i + 1, total, "fal")

    return result


# ── Public API ────────────────────────────────────────────────────────────────

def acquire_visuals(
    scenes: list[dict],
    output_dir: Path,
    *,
    backend: VisualBackend = "auto",
    overwrite: bool = False,
    progress_callback=None,
) -> list[dict]:
    """
    Acquire one visual asset per scene. Returns scenes with "visual_path" (str) set.

    Priority order for "auto" (highest quality first):
      1. fal      (if FAL_KEY env var is set — Wan 2.1 T2V via fal.ai)
      2. pexels   (if PEXELS_API_KEY env var is set — stock video)
      3. kenburns (always available — animates title card via ffmpeg zoompan)
      4. pillow   (static title card, always works)

    Each backend sets scene["visual_path"] and scene["visual_type"] ("video"|"image").
    """
    output_dir = Path(output_dir)
    effective = _auto_backend() if backend == "auto" else backend

    if effective == "kenburns":
        results = _acquire_kenburns(scenes, output_dir, overwrite, progress_cb=progress_callback)
    elif effective == "pexels":
        results = _acquire_pexels(scenes, output_dir, overwrite, progress_cb=progress_callback)
    elif effective == "fal":
        results = _acquire_fal(scenes, output_dir, overwrite, progress_cb=progress_callback)
    else:
        results = _acquire_pillow(scenes, output_dir, overwrite, progress_cb=progress_callback)

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire visuals for video scenes")
    parser.add_argument("--scenes", type=Path, required=True, help="JSON file with scene list")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--backend",
        choices=["auto", "kenburns", "pexels", "fal", "pillow"],
        default="auto",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scenes = json.loads(args.scenes.read_text("utf-8"))

    def progress(i, total, src):
        print(f"  [{i}/{total}] {src}", flush=True)

    result = acquire_visuals(
        scenes, args.output_dir,
        backend=args.backend, overwrite=args.overwrite,
        progress_callback=progress,
    )
    print(f"Done. {len(result)} visuals in {args.output_dir}")
    for s in result:
        print(f"  {s.get('visual_path')}  ({s.get('visual_type')})")


if __name__ == "__main__":
    main()
