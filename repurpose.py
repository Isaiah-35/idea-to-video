"""Repurpose: cut a long video into per-scene clips using ffmpeg."""
import argparse
import json
import subprocess
from pathlib import Path


def merge_short_scenes(scenes: list[dict], target_duration: float = 45.0) -> list[dict]:
    """Greedily merge adjacent scenes until each group is near target_duration.

    Scenes without a "duration_s" key are treated as having duration 0 for
    grouping purposes and are merged into the previous group if one exists.

    Returns a new list of merged scene dicts. Each merged scene has:
      - "title": first scene title in the group
      - "duration_s": sum of durations in the group (None if all were None)
      - "scenes": list of original scenes in this group
    """
    if not scenes:
        return []

    groups: list[dict] = []
    current_titles: list[str] = []
    current_duration: float = 0.0
    current_scenes: list[dict] = []

    for scene in scenes:
        dur = scene.get("duration_s")
        d = float(dur) if dur is not None else 0.0

        if current_scenes and (current_duration + d) > target_duration and current_duration > 0:
            # Flush current group
            groups.append({
                "title": current_scenes[0].get("title", ""),
                "duration_s": current_duration if current_duration > 0 else None,
                "scenes": list(current_scenes),
            })
            current_titles = []
            current_duration = 0.0
            current_scenes = []

        current_scenes.append(scene)
        current_duration += d

    if current_scenes:
        groups.append({
            "title": current_scenes[0].get("title", ""),
            "duration_s": current_duration if current_duration > 0 else None,
            "scenes": list(current_scenes),
        })

    return groups


def extract_clips(
    video_path: Path,
    scenes: list[dict],
    output_dir: Path,
    max_duration: float = 60.0,
) -> list[dict]:
    """Cut a video into one clip per scene using ffmpeg.

    Args:
        video_path: source MP4.
        scenes: list of dicts with "title" and "duration_s" keys.
            Scenes where duration_s is None are skipped.
            Scenes where duration_s > max_duration are skipped.
        output_dir: must exist — caller creates it.
        max_duration: skip scenes longer than this (seconds).

    Returns:
        List of {"title": str, "path": str, "duration_s": float} for successfully cut clips.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)

    clips: list[dict] = []
    offset: float = 0.0

    for i, scene in enumerate(scenes, start=1):
        dur = scene.get("duration_s")
        if dur is None:
            offset += 0.0
            continue
        dur = float(dur)
        if dur > max_duration:
            offset += dur
            continue

        title = scene.get("title", f"scene_{i}")
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)[:50]
        out_path = output_dir / f"{i:03d}_{safe_title}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(offset),
            "-t", str(dur),
            "-i", str(video_path),
            "-c:v", "libx264", "-c:a", "aac",
            "-movflags", "+faststart",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 100:
            clips.append({
                "title": title,
                "path": str(out_path),
                "duration_s": dur,
            })

        offset += dur

    return clips


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Cut a video into per-scene clips")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--scenes", type=Path, required=True, help="JSON file with scenes list")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-duration", type=float, default=60.0)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scenes = json.loads(args.scenes.read_text("utf-8"))

    clips = extract_clips(args.video, scenes, args.output_dir, max_duration=args.max_duration)
    print(f"Extracted {len(clips)} clips:")
    for c in clips:
        print(f"  {c['path']}  ({c['duration_s']:.1f}s)")


if __name__ == "__main__":
    main()
