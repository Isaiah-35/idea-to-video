"""Assemble final video from visual assets (images or clips) + audio."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def _check_ffmpeg() -> None:
    """Raise a clear error if ffmpeg is not installed."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is required for video assembly. Install it with: brew install ffmpeg"
        )


def assemble(
    audio_path: Path,
    visuals: list[dict],
    output_path: Path,
    *,
    fade_duration: float = 0.5,
) -> Path:
    """
    Assemble audio + visuals into MP4.

    If all visuals are images: uses ffmpeg slideshow (same as make_video.sh).
    If any visual is a video: trims each clip to duration_s, concat, mux with audio.
    Returns output_path.
    """
    _check_ffmpeg()

    audio_path = Path(audio_path)
    output_path = Path(output_path)

    visual_types = {s.get("visual_type") for s in visuals}

    if "video" in visual_types:
        return _assemble_video_clips(audio_path, visuals, output_path)
    else:
        return _assemble_image_slideshow(audio_path, visuals, output_path)


def _assemble_video_clips(
    audio_path: Path,
    visuals: list[dict],
    output_path: Path,
) -> Path:
    """Trim each clip, concat, then mux with audio."""
    _check_ffmpeg()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        trimmed_paths: list[str] = []

        # Step 1: trim each clip
        for i, scene in enumerate(visuals):
            clip_path = scene.get("visual_path")
            if not clip_path or not Path(clip_path).exists():
                raise FileNotFoundError(
                    f"Visual path not found for scene {i}: {clip_path!r}"
                )

            duration = scene.get("duration_s") or 5.0
            trimmed = tmp_dir / f"trimmed_{i:03d}.mp4"

            if scene.get("visual_type") == "image":
                # Convert static image to a short video clip
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", str(clip_path),
                    "-t", f"{duration:.2f}",
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                    "-pix_fmt", "yuv420p",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    "-an",
                    str(trimmed),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(clip_path),
                    "-t", f"{duration:.2f}",
                    "-c", "copy",
                    str(trimmed),
                ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg trim failed for scene {i}:\n{result.stderr}"
                )
            trimmed_paths.append(str(trimmed))

        # Step 2: write concat list
        concat_list = tmp_dir / "concat.txt"
        concat_list.write_text(
            "".join(f"file '{p}'\n" for p in trimmed_paths),
            encoding="utf-8",
        )

        # Step 3: concat all trimmed clips
        silent_video = tmp_dir / "silent.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(silent_video),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg concat failed:\n{result.stderr}"
            )

        # Step 4: mux with audio
        cmd = [
            "ffmpeg", "-y",
            "-i", str(silent_video),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg mux failed:\n{result.stderr}"
            )

    return output_path


def _assemble_image_slideshow(
    audio_path: Path,
    visuals: list[dict],
    output_path: Path,
) -> Path:
    """Delegate to make_video.sh for image slideshow (preserve existing behavior)."""
    import os
    script_sh = Path(__file__).parent / "make_video.sh"

    with tempfile.TemporaryDirectory() as img_dir:
        img_dir_path = Path(img_dir)
        durations_out = Path(tempfile.mktemp(suffix=".txt"))

        for i, scene in enumerate(visuals, start=1):
            src = Path(scene["visual_path"])
            dst = img_dir_path / f"img{i:03d}.jpg"
            dst.write_bytes(src.read_bytes())

        durations = [scene.get("duration_s") or 5.0 for scene in visuals]
        durations_out.write_text("\n".join(f"{d:.3f}" for d in durations), "utf-8")

        cmd = [
            "bash", str(script_sh),
            str(img_dir_path),
            str(audio_path),
            str(output_path),
            str(durations_out),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size < 1000:
        raise RuntimeError(
            f"make_video.sh slideshow failed:\n{result.stdout}\n{result.stderr}"
        )

    return output_path


def assemble_from_files(
    audio_path: Path,
    image_paths: list[Path],
    durations_path: Path | None,
    output_path: Path,
) -> Path:
    """Thin wrapper calling make_video.sh for backward compatibility."""
    _check_ffmpeg()

    script_sh = Path(__file__).parent / "make_video.sh"

    with tempfile.TemporaryDirectory() as img_dir:
        img_dir_path = Path(img_dir)
        for i, img_path in enumerate(sorted(image_paths), start=1):
            src = Path(img_path)
            dst = img_dir_path / f"img{i:03d}.jpg"
            dst.write_bytes(src.read_bytes())

        cmd = [
            "bash", str(script_sh),
            str(img_dir_path),
            str(audio_path),
            str(output_path),
        ]
        if durations_path and Path(durations_path).exists():
            cmd.append(str(durations_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size < 1000:
        raise RuntimeError(
            f"make_video.sh failed:\n{result.stdout}\n{result.stderr}"
        )

    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble video from audio + visuals")
    parser.add_argument("--audio", type=Path, required=True, help="Audio file (WAV/MP3)")
    parser.add_argument("--scenes", type=Path, required=True,
                        help="Scenes JSON with visual_path + visual_type + duration_s")
    parser.add_argument("--output", type=Path, required=True, help="Output MP4 path")
    parser.add_argument("--fade-duration", type=float, default=0.5, help="Cross-fade seconds")
    args = parser.parse_args()

    scenes = json.loads(args.scenes.read_text("utf-8"))
    result = assemble(args.audio, scenes, args.output, fade_duration=args.fade_duration)
    print(f"Done. Video: {result}  ({result.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
