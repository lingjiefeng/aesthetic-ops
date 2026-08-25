#!/usr/bin/env python3
"""Assemble a self-contained depth-card HTML page from generated assets.

Single card:
    python3 build_card.py assets/ card.config.json -o card.html
Deck (left/right arrows flip between cards):
    python3 build_card.py a1/ c1.json a2/ c2.json a3/ c3.json -o deck.html

Each card config (all fields except sprites optional):
    {
      "caption": "PASTURE · <b>No. 001</b>",
      "maxWidth": 470,
      "near": false,
      "sprites": [ {"file": "sprite_1.png", "x": 74, "y": 58, "h": 38, "z": 70} ]
    }
x/y are % of the photo area (may exceed 0-100 to overhang the card edge),
h is % of photo height, z is translateZ in px. "near": true adds the
depth-model background-parallax layer (can ghost on subject-dominant photos).

Global feel knobs (tiltMax, followLag, spriteLag, nearDepth, spriteDrift,
glare, invert, title) are read from the FIRST config given.

The emitted HTML embeds every asset as a data URI and keeps the CONFIG block
editable at the top of its <script> for post-hoc tuning.
"""

import argparse
import base64
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "template" / "card.html"
TOKEN = "/*__CONFIG__*/null"
GLOBAL_KEYS = ("tiltMax", "followLag", "spriteLag", "nearDepth",
               "spriteDrift", "glare", "invert")


def fail(msg):
    sys.exit(f"DEPTH-CARD FAILURE: {msg}")


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def load_card(assets, cfg):
    card = {}
    photo = assets / "photo.jpg"
    if not photo.exists():
        fail(f"{photo} missing — run generate_assets.py first")
    card["photoSrc"] = data_uri(photo, "image/jpeg")

    near = assets / "near.png"
    if cfg.get("near", False) and near.exists():
        card["nearSrc"] = data_uri(near, "image/png")

    if not cfg.get("sprites"):
        fail(f"config for {assets} has no sprites — a depth card needs at least one")
    card["sprites"] = []
    for s in cfg["sprites"]:
        s = dict(s)
        p = assets / s.pop("file")
        if not p.exists():
            fail(f"sprite asset missing: {p}")
        s["src"] = data_uri(p, "image/png")
        card["sprites"].append(s)

    for k in ("caption", "maxWidth"):
        if k in cfg:
            card[k] = cfg[k]
    return card


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pairs", nargs="+",
                    help="one or more <assets_dir> <config.json> pairs")
    ap.add_argument("-o", "--output", default="card.html")
    args = ap.parse_args()

    if len(args.pairs) % 2:
        fail("arguments must be <assets_dir> <config.json> pairs")

    configs = []
    for a, c in zip(args.pairs[::2], args.pairs[1::2]):
        configs.append((Path(a), json.loads(Path(c).read_text())))

    top = {k: v for k, v in configs[0][1].items() if k in GLOBAL_KEYS}
    top["cards"] = [load_card(a, cfg) for a, cfg in configs]

    html = TEMPLATE.read_text()
    if TOKEN not in html:
        fail(f"template token {TOKEN!r} not found in {TEMPLATE}")
    html = html.replace(TOKEN, json.dumps(top))
    title = configs[0][1].get("title")
    if title:
        html = html.replace("<title>depth card</title>", f"<title>{title}</title>")

    out = Path(args.output)
    out.write_text(html)
    size_mb = out.stat().st_size / 1e6
    if size_mb > 15:
        fail(f"{out} is {size_mb:.1f}MB — too heavy; shrink the photos or drop near layers")
    n = len(top["cards"])
    print(f"built {out} ({size_mb:.2f}MB, {n} card{'s' if n > 1 else ''})")


if __name__ == "__main__":
    main()
