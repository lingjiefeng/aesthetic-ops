# pixel-tilt-card

Turn photos into an interactive card page: the photo tilts in 3D under your
cursor while pixel-art sprites of its own subjects float in front and hang
past the card's edges. Several photos become a deck with arrow navigation.

**[▶ Live demo](https://lingjiefeng.github.io/aesthetic-ops/examples/pixel-tilt-card/field-notes.html)**

## Install

Marketplace (recommended) — from inside Claude Code:

```
/plugin marketplace add lingjiefeng/aesthetic-ops
/plugin install pixel-tilt-card@aesthetic-ops
```

Or copy it in manually:

```bash
git clone https://github.com/lingjiefeng/aesthetic-ops.git
cp -R aesthetic-ops/plugins/pixel-tilt-card/skills/pixel-tilt-card ~/.claude/skills/
```

Then set a free Gemini key, used to draw the sprites:

```bash
export GEMINI_API_KEY=...   # https://aistudio.google.com/apikey
```

Needs [`uv`](https://docs.astral.sh/uv/). The first run downloads a ~50MB
depth model to `~/.cache/pixel-tilt-card/`; after that it's offline except
for sprite generation.

## Use

Ask Claude Code, naming photos and optionally what to lift from each:

```
/pixel-tilt-card ~/photos/beach.jpg (the dog and the surfer), ~/photos/hike.jpg
```

Name subjects specifically ("the woman in the red jacket" beats "the
woman") — that's what steers the sprite drawing. Omit them and Claude picks
1–3 foreground subjects after looking at the photo. Output is one
self-contained `.html`: no build, no server, no network at view time.

## Tune

Every knob lives in the `CONFIG` block at the top of the generated file —
edit and reload, no regeneration (one exception: the optional background
parallax layer is a build-time key, `"near": true`, in the card config):

| knob | does |
|---|---|
| `tiltMax` | how far the card tips (degrees) |
| `followLag` | cursor-follow weight; lower = heavier, laggier |
| `spriteLag` / `spriteDrift` | how far the sprites trail and outrun the card |
| `glare` | strength of the light sweep |
| `cards[].sprites[].x/y/h/z` | each sprite's position (% — past 0/100 overhangs), height, float depth |

## How it works

1. Gemini's image model redraws each named subject as a pixel-art sprite on
   a flat background; the sprite is keyed to transparency and pixel-snapped
   locally.
2. A local Depth Anything V2 model derives the optional background layer.
3. `build_card.py` inlines everything as data URIs into the page template.

Sprites are verified visually before assembly. If a subject can't be lifted
cleanly, the run stops and says why rather than shipping a degraded card.

## Files

```
SKILL.md            instructions Claude follows
scripts/            generate_assets.py (sprites + depth), build_card.py
template/card.html  the interactive page
```
