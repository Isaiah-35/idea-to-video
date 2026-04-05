"""Generate title-card images for each scene.

Backend priority (auto):
  1. fal      — fal.ai Flux Schnell (fast, cheap AI images); FAL_KEY required
  2. dalle3   — OpenAI DALL-E 3 (high quality); OPENAI_API_KEY required
  3. pexels   — Pexels stock photos (free, 200 req/hr); PEXELS_API_KEY required
  4. pillow   — Local title cards (no API, always works)

Set backend="auto" to use the best available option automatically.
Any paid backend that hits a billing/quota error falls through to the next tier.
"""
import argparse
import json
import os
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ── Pillow backend ─────────────────────────────────────────────────────────────

def _gradient_bg(width: int = 1920, height: int = 1080) -> Image.Image:
    top_color = np.array([10, 10, 30], dtype=np.float32)
    bot_color = np.array([25, 20, 60], dtype=np.float32)
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        t = y / (height - 1)
        arr[y, :] = (top_color + t * (bot_color - top_color)).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def _load_font(size: int):
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _make_pillow_card(scene: dict, index: int) -> Image.Image:
    img = _gradient_bg()
    draw = ImageDraw.Draw(img)
    W, H = 1920, 1080

    # — Badge (circle + number top-left)
    badge_cx, badge_cy, badge_r = 80, 80, 42
    accent = (160, 140, 255)
    draw.ellipse(
        [badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
        fill=accent,
    )
    badge_font = _load_font(32)
    badge_text = f"{index:02d}"
    bb = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(
        (badge_cx - bw // 2, badge_cy - bh // 2),
        badge_text,
        font=badge_font,
        fill=(10, 10, 30),
    )

    # — Title (centered, large)
    title_font = _load_font(88)
    title = scene.get("title", f"Scene {index}")
    bb = draw.textbbox((0, 0), title, font=title_font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    title_y = H // 2 - th // 2 - 60
    draw.text(((W - tw) // 2, title_y), title, font=title_font, fill=(220, 220, 255))

    # — Image prompt (smaller, word-wrapped, 2-line max)
    prompt_font = _load_font(36)
    raw_prompt = scene.get("image_prompt", "")
    if raw_prompt:
        wrapped = textwrap.wrap(raw_prompt, width=80)[:2]
        prompt_text = "\n".join(wrapped)
        bb = draw.textbbox((0, 0), prompt_text, font=prompt_font)
        pw, ph = bb[2] - bb[0], bb[3] - bb[1]
        prompt_y = title_y + th + 40
        draw.multiline_text(
            ((W - pw) // 2, prompt_y),
            prompt_text,
            font=prompt_font,
            fill=(140, 140, 200),
            align="center",
        )

    # — Horizontal rule
    draw.line([(80, 900), (W - 80, 900)], fill=(60, 50, 120), width=2)

    return img


# ── fal.ai backend (Flux Schnell — fast, cheap AI images) ─────────────────────

def _make_fal_card(scene: dict) -> bytes:
    """Generate via fal.ai Flux Schnell. Returns raw JPEG bytes."""
    import urllib.request
    try:
        import fal_client
    except ImportError:
        raise RuntimeError("fal backend requires fal-client: pip install fal-client")

    api_key = os.environ.get("FAL_KEY")
    if not api_key:
        raise RuntimeError("fal backend requires FAL_KEY env var")

    raw_prompt = scene.get("image_prompt") or scene.get("title", "abstract visual")
    prompt = (
        f"{raw_prompt}. "
        "Cinematic wide shot, 16:9 landscape orientation, photorealistic, "
        "high detail, no text overlays, no watermarks, no logos."
    )
    result = fal_client.subscribe(
        "fal-ai/flux/schnell",
        arguments={
            "prompt": prompt,
            "image_size": "landscape_16_9",
            "num_images": 1,
            "num_inference_steps": 4,
        },
    )
    url = result["images"][0]["url"]
    with urllib.request.urlopen(url) as r:
        return r.read()


# ── Pexels backend (free stock photos) ────────────────────────────────────────

def _make_pexels_card(scene: dict) -> bytes:
    """Fetch a relevant stock photo from Pexels. Returns raw image bytes."""
    import urllib.request
    import urllib.parse

    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise RuntimeError("pexels backend requires PEXELS_API_KEY env var")

    # Build search query from image_prompt or title
    raw = scene.get("image_prompt") or scene.get("title", "")
    # Strip instruction-style suffixes and trim to key nouns for better results
    query = raw.split(".")[0].strip()[:100]

    search_url = (
        "https://api.pexels.com/v1/search?"
        + urllib.parse.urlencode({"query": query, "per_page": 1, "orientation": "landscape"})
    )
    req = urllib.request.Request(search_url, headers={
        "Authorization": api_key,
        "User-Agent": "idea-to-video/1.0",
    })
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    photos = data.get("photos", [])
    if not photos:
        raise RuntimeError(f"Pexels: no results for query '{query}'")

    img_url = photos[0]["src"]["large2x"]  # 2560px wide
    img_req = urllib.request.Request(img_url, headers={"User-Agent": "idea-to-video/1.0"})
    with urllib.request.urlopen(img_req) as r:
        return r.read()


# ── DALL-E 3 backend ───────────────────────────────────────────────────────────

def _make_dalle3_card(scene: dict) -> bytes:
    try:
        import openai
        if not hasattr(openai, "OpenAI"):
            raise RuntimeError(
                "DALL-E 3 requires openai>=1.0. Run: pip install 'openai>=1.0' --upgrade"
            )
    except ImportError:
        raise RuntimeError(
            "DALL-E 3 requires openai>=1.0. Run: pip install 'openai>=1.0' --upgrade"
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("DALL-E 3 requires OPENAI_API_KEY env var")

    import urllib.request

    client = openai.OpenAI(api_key=api_key)
    raw_prompt = scene.get("image_prompt") or scene.get("title", "abstract visual")
    # Enforce cinematic framing so the image works as a video slide
    prompt = (
        f"{raw_prompt}. "
        "Cinematic wide shot, 16:9 landscape orientation, photorealistic, "
        "high detail, no text, no watermarks, no logos."
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    url = response.data[0].url
    with urllib.request.urlopen(url) as r:
        return r.read()


# ── Public API ─────────────────────────────────────────────────────────────────

_BILLING_SIGNALS = ("billing", "quota", "exhausted", "hard limit", "rate limit")


def _is_billing_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(s in msg for s in _BILLING_SIGNALS) or "429" in str(e)


def _resolve_auto_backend() -> str:
    """Pick best available backend: fal → dalle3 → pexels → pillow."""
    try:
        import fal_client  # noqa: F401
        if os.environ.get("FAL_KEY"):
            return "fal"
    except ImportError:
        pass
    try:
        import openai as _oai
        if hasattr(_oai, "OpenAI") and os.environ.get("OPENAI_API_KEY"):
            return "dalle3"
    except ImportError:
        pass
    if os.environ.get("PEXELS_API_KEY"):
        return "pexels"
    return "pillow"


_FALLBACK_ORDER = ["fal", "dalle3", "pexels", "pillow"]


def generate_images(
    scenes: list[dict],
    output_dir: Path,
    *,
    backend: str = "auto",
    overwrite: bool = False,
    progress_callback=None,
) -> list[dict]:
    """Generate one image per scene into output_dir.

    Args:
        scenes: list of dicts with at least "title" and "image_prompt" keys.
        output_dir: must exist — caller is responsible for creating it.
        backend: "fal" | "dalle3" | "pexels" | "pillow" | "auto"
            "auto" picks fal → dalle3 → pexels → pillow based on available keys.
            Any paid backend that hits a billing/quota error falls through automatically.
        overwrite: if False, skip scenes where the output file already exists.
        progress_callback: optional callable(i, total) called after each image.

    Returns:
        scenes list with "image_path" key added/updated for each generated image.
    """
    output_dir = Path(output_dir)
    effective_backend = _resolve_auto_backend() if backend == "auto" else backend

    result = list(scenes)
    total = len(result)

    for i, scene in enumerate(result, start=1):
        out_path = output_dir / f"img{i:03d}.jpg"

        if out_path.exists() and not overwrite:
            scene = dict(scene)
            scene["image_path"] = str(out_path)
            result[i - 1] = scene
            if progress_callback:
                progress_callback(i, total)
            continue

        scene = dict(scene)
        img_bytes: bytes | None = None

        # Try current backend, cascade on billing/quota errors
        current = effective_backend
        while img_bytes is None:
            try:
                if current == "fal":
                    img_bytes = _make_fal_card(scene)
                elif current == "dalle3":
                    img_bytes = _make_dalle3_card(scene)
                elif current == "pexels":
                    img_bytes = _make_pexels_card(scene)
                else:
                    break  # pillow path below
            except Exception as e:
                if _is_billing_error(e):
                    # Find next backend in fallback chain
                    idx = _FALLBACK_ORDER.index(current) if current in _FALLBACK_ORDER else -1
                    if idx + 1 < len(_FALLBACK_ORDER):
                        next_b = _FALLBACK_ORDER[idx + 1]
                        print(f"[generate_images] {current} billing limit — falling back to {next_b}")
                        # Cascade for all remaining scenes too
                        effective_backend = next_b
                        current = next_b
                    else:
                        break  # exhausted all API backends, use pillow
                else:
                    raise

        if img_bytes:
            out_path.write_bytes(img_bytes)
        else:
            img = _make_pillow_card(scene, i)
            img.save(str(out_path), "JPEG", quality=92)

        scene["image_path"] = str(out_path)
        result[i - 1] = scene

        if progress_callback:
            progress_callback(i, total)

    return result


# ── Visual sources helper ──────────────────────────────────────────────────────

def generate_title_card_for_scene(scene: dict, output_path: Path) -> Path:
    """Generate a single Pillow title card for a scene. Returns output_path."""
    output_path = Path(output_path)
    result = generate_images([scene], output_path.parent, backend="pillow", overwrite=True)
    # rename img001.jpg to output_path if different
    generated = Path(result[0]["image_path"])
    if generated.resolve() != output_path.resolve():
        generated.rename(output_path)
    return output_path


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate title-card images for video scenes")
    parser.add_argument("--scenes", type=Path, required=True, help="JSON file with scene list")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backend", choices=["fal", "dalle3", "pexels", "pillow", "auto"], default="auto")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scenes = json.loads(args.scenes.read_text("utf-8"))

    def progress(i, total):
        print(f"  [{i}/{total}] generated", flush=True)

    result = generate_images(
        scenes, args.output_dir,
        backend=args.backend, overwrite=args.overwrite,
        progress_callback=progress,
    )
    print(f"Done. {len(result)} images in {args.output_dir}")


if __name__ == "__main__":
    main()
