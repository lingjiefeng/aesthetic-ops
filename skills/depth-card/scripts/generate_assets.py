#!/usr/bin/env python3
"""Generate depth-card assets from a photo using Gemini.

Produces, in --out:
    photo.jpg     resized base photo
    near.png      photo pixels of the foreground region, alpha-masked (depth layer)
    sprite_N.png  pixel-art sprite per subject, transparent background, low-res
    raw/          raw Gemini generations (debugging)
    manifest.json what was made + validation stats

Usage:
    export GEMINI_API_KEY=...
    uv run --with google-genai,pillow,numpy generate_assets.py photo.jpg \
        --subject "the woman in the cap" --subject "the cow" --out assets/

Fails loudly (nonzero exit + DEPTH-CARD FAILURE message) when a sprite or the
foreground mask can't be produced cleanly. Never emits degraded assets.
"""

import argparse
import base64
import io
import json
import os
import re
import sys
from pathlib import Path

IMAGE_MODEL = os.environ.get("DEPTH_CARD_IMAGE_MODEL", "gemini-2.5-flash-image")
DEPTH_ONNX_URL = (
    "https://huggingface.co/onnx-community/depth-anything-v2-small/"
    "resolve/main/onnx/model.onnx"
)
DEPTH_ONNX_CACHE = Path.home() / ".cache" / "depth-card" / "depth-anything-v2-small.onnx"

SPRITE_PROMPT = (
    "Look at this photo. Redraw ONLY {subject} as a chunky retro pixel-art "
    "sprite in 16-bit video game style. Keep the subject's recognizable "
    "colors, clothing, pose and proportions from the photo. The whole subject "
    "must be fully visible and centered, filling most of the frame. Place it "
    "on a completely solid, flat, pure green #00FF00 background — no shadow, "
    "no ground, no outline, no border, no text, nothing else in the image."
)
SPRITE_RETRY_SUFFIX = (
    " IMPORTANT: every pixel that is not the subject itself must be exactly "
    "the flat color #00FF00."
)

BASE_MAX = 1600  # px, long edge of the base photo


def fail(msg):
    sys.exit(f"DEPTH-CARD FAILURE: {msg}")


def gen_image(client, contents):
    resp = client.models.generate_content(model=IMAGE_MODEL, contents=contents)
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            data = getattr(part, "inline_data", None)
            if data and str(data.mime_type).startswith("image/"):
                from PIL import Image
                return Image.open(io.BytesIO(data.data))
    return None


def chroma_key(img, sprite_res):
    """Flat background -> transparent, crop, snap to low-res crisp pixels.

    Keys against the image's actual border color (models rarely hit #00FF00
    exactly). Returns (sprite_image, coverage_fraction); (None, -1.0) if the
    border isn't a flat color, (None, coverage) if the keyed area is implausible.
    """
    import numpy as np
    from PIL import Image

    rgb = np.asarray(img.convert("RGB"), dtype=np.int16)
    h, w = rgb.shape[:2]
    bw = max(4, min(h, w) // 20)
    border = np.concatenate([rgb[:bw].reshape(-1, 3), rgb[-bw:].reshape(-1, 3),
                             rgb[:, :bw].reshape(-1, 3), rgb[:, -bw:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    if float(np.abs(border - bg).sum(axis=1).mean()) > 40:
        return None, -1.0  # border isn't flat -> background instruction ignored

    dist = np.abs(rgb - bg).sum(axis=2)
    # distance <= 40 -> transparent, >= 100 -> opaque
    alpha = np.clip((dist - 40) * 255 // 60, 0, 255).astype(np.uint8)

    coverage = float((alpha > 128).mean())
    if not (0.02 < coverage < 0.75):
        return None, coverage

    # decontaminate edges: unpremultiply against the known background color
    a = alpha[..., None].astype(np.float32) / 255.0
    soft = (a > 0) & (a < 1)
    out_rgb = np.where(soft, np.clip((rgb - (1 - a) * bg) / np.maximum(a, .2), 0, 255), rgb)
    out = np.dstack([out_rgb.astype(np.uint8), alpha])
    sprite = Image.fromarray(out, "RGBA")

    ys, xs = np.where(alpha > 24)
    m = 4
    sprite = sprite.crop((max(xs.min() - m, 0), max(ys.min() - m, 0),
                          min(xs.max() + m, sprite.width), min(ys.max() + m, sprite.height)))

    # snap to chunky pixels: downscale, harden alpha, quantize colors
    h = sprite_res
    w = max(1, round(sprite.width * h / sprite.height))
    small = sprite.resize((w, h), Image.LANCZOS)
    arr = np.asarray(small).copy()
    arr[..., 3] = np.where(arr[..., 3] > 110, 255, 0)
    small = Image.fromarray(arr, "RGBA")
    pal = small.convert("RGB").quantize(colors=48).convert("RGB")
    small = Image.merge("RGBA", (*pal.split(), small.split()[3]))
    return small, coverage


def make_sprite(client, photo, subject, idx, out_dir, sprite_res):
    from PIL import Image
    prompt = SPRITE_PROMPT.format(subject=subject)
    for attempt in (1, 2, 3):
        cached = out_dir / "raw" / f"gen_{idx}_try{attempt}.png"
        if cached.exists():
            print(f"  attempt {attempt}: reusing cached generation")
            raw = Image.open(cached)
        else:
            raw = gen_image(client, [photo, prompt])
            if raw is None:
                print(f"  attempt {attempt}: no image returned, retrying")
                continue
            raw.convert("RGB").save(cached)
        sprite, coverage = chroma_key(raw, sprite_res)
        if sprite is not None:
            path = out_dir / f"sprite_{idx}.png"
            sprite.save(path)
            print(f"  sprite_{idx}.png  ({sprite.width}x{sprite.height}, coverage {coverage:.0%})")
            return {"file": path.name, "subject": subject, "coverage": round(coverage, 3),
                    "size": [sprite.width, sprite.height]}
        why = "background not flat" if coverage < 0 else f"keyed coverage {coverage:.0%} out of bounds"
        print(f"  attempt {attempt}: {why}, retrying")
        prompt = SPRITE_PROMPT.format(subject=subject) + SPRITE_RETRY_SUFFIX
    fail(
        f'could not produce a clean pixel-art sprite for "{subject}" after 3 attempts. '
        f"The model kept returning images whose green background could not be keyed out "
        f"(raw attempts saved in {out_dir/'raw'}). This subject may be too entangled with "
        f"the scene, too small, or ambiguous — try a more specific description or a different photo."
    )


def make_near_layer(photo, out_dir):
    """Foreground layer from a local monocular depth model (Depth Anything V2
    small, ONNX). near.png = the photo's nearest ~third, feathered by depth.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    if not DEPTH_ONNX_CACHE.exists():
        print(f"  downloading depth model (~50MB, one-time) -> {DEPTH_ONNX_CACHE}")
        import urllib.request
        DEPTH_ONNX_CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = DEPTH_ONNX_CACHE.with_suffix(".part")
        urllib.request.urlretrieve(DEPTH_ONNX_URL, tmp)
        tmp.rename(DEPTH_ONNX_CACHE)

    import onnxruntime as ort
    sess = ort.InferenceSession(str(DEPTH_ONNX_CACHE), providers=["CPUExecutionProvider"])

    W, H = photo.size
    inp = np.asarray(photo.resize((518, 518), Image.BICUBIC), dtype=np.float32) / 255.0
    inp = (inp - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    inp = inp.transpose(2, 0, 1)[None].astype(np.float32)
    depth = sess.run(None, {sess.get_inputs()[0].name: inp})[0].squeeze()

    d = (depth - depth.min()) / max(1e-6, depth.max() - depth.min())  # 1 = nearest
    depth_img = Image.fromarray((d * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC)
    depth_img.save(out_dir / "raw" / "depth.png")

    dn = np.asarray(depth_img, dtype=np.float32) / 255.0
    if float(dn.std()) < 0.04:
        fail(
            f"the scene has almost no depth variation (std {dn.std():.3f}) — "
            "the card would have no background parallax. Try a photo with "
            "clearer near/far separation."
        )
    # near = nearest ~35% of the depth range, soft-edged over the next 12%
    lo = float(np.quantile(dn, 0.65))
    alpha = np.clip((dn - lo) / 0.12, 0, 1)
    frac = float((alpha > 0.5).mean())
    feathered = Image.fromarray((alpha * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(1.5))
    near = photo.convert("RGBA")
    near.putalpha(feathered)
    near.save(out_dir / "near.png")
    print(f"  near.png  (foreground {frac:.0%}, depth std {dn.std():.2f})")
    return {"file": "near.png", "fraction": round(frac, 3), "depth_std": round(float(dn.std()), 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo")
    ap.add_argument("--subject", action="append", required=True,
                    help="plain-language subject to lift, repeatable (1-3)")
    ap.add_argument("--out", default="assets", help="output directory")
    ap.add_argument("--sprite-res", type=int, default=96,
                    help="sprite height in pixels; lower = chunkier pixel art (default 96)")
    args = ap.parse_args()

    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        fail("GEMINI_API_KEY is not set — https://aistudio.google.com/apikey")
    if not Path(args.photo).exists():
        fail(f"photo not found: {args.photo}")
    if not 1 <= len(args.subject) <= 3:
        fail("give 1-3 --subject values")

    from PIL import Image, ImageOps
    from google import genai

    out_dir = Path(args.out)
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)

    photo = Image.open(args.photo)
    photo = ImageOps.exif_transpose(photo).convert("RGB")
    if max(photo.size) > BASE_MAX:
        photo.thumbnail((BASE_MAX, BASE_MAX), Image.LANCZOS)
    photo.save(out_dir / "photo.jpg", quality=90)
    print(f"base photo {photo.width}x{photo.height}")

    client = genai.Client()

    sprites = []
    for i, subject in enumerate(args.subject, 1):
        print(f'sprite {i}: "{subject}"')
        sprites.append(make_sprite(client, photo, subject, i, out_dir, args.sprite_res))

    print("foreground depth layer")
    near = make_near_layer(photo, out_dir)

    manifest = {"photo": "photo.jpg", "photo_size": list(photo.size),
                "sprites": sprites, "near": near, "sprite_res": args.sprite_res,
                "models": {"image": IMAGE_MODEL, "depth": "depth-anything-v2-small (local onnx)"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"done — assets in {out_dir}/ (inspect sprites visually before building the card)")


if __name__ == "__main__":
    main()
