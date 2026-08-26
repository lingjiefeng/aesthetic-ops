---
name: pixel-tilt-card
description: Turn one or more photos into an interactive "pixel tilt card" — a self-contained HTML page where each photo tilts in 3D under the cursor while pixel-art sprites of the photo's own subjects float in front, overhanging the card's edges. Multiple photos become a deck with left/right arrows. Use when the user wants a pixel tilt card, a 3D tilting photo card, or pixel-art parallax page from photos.
---

# Pixel Tilt Card

Input: one or more photos, plus (optionally) which subjects to lift and
taste knobs. Output: one self-contained `.html` file — no server, no build,
no network. Several photos become a deck: on-screen arrows and ←/→ keys
flip between cards with a swing transition.

## Requirements

- `GEMINI_API_KEY` in the environment (sprites are drawn by Gemini's image
  model). In non-interactive shells load it with
  `eval "$(grep -m1 '^export GEMINI_API_KEY=' ~/.zshrc)"`. NEVER print or
  copy the key; pipe run output through `grep -viE 'AIza|api.key'`.
- `uv` (deps fetched per-run: `google-genai,pillow,numpy,onnxruntime`).
- First-ever run downloads a ~50MB local depth model to
  `~/.cache/pixel-tilt-card/` (one time, then offline).

## Workflow

1. **Look at the photo** (Read it; convert HEIC first:
   `sips -s format jpeg in.heic --out out.jpg --resampleHeightWidthMax 1400`).
   If the user didn't name subjects, pick 1–3 distinct foreground subjects
   yourself and tell the user what you chose. Describe each subject
   specifically ("the woman wearing the dark baseball cap and white tank
   top", not "the woman") — specificity is what steers the sprite model.

2. **Generate assets** — once per photo, each into its own directory:
   ```
   uv run --with google-genai,pillow,numpy,onnxruntime \
     scripts/generate_assets.py photo.jpg \
     --subject "..." [--subject "..."] --out assets/
   ```
   Knob: `--sprite-res N` (default 96) — sprite height in pixels; lower =
   chunkier pixel art.

3. **Verify visually — mandatory.** Read each `assets/sprite_N.png` and
   judge: recognizable as the subject (clothing, colors, pose)? Clean
   transparent edges? If a sprite is off, delete the cached
   `assets/raw/gen_N_try*.png` for it and rerun (fresh generations), or
   sharpen the subject description. The script already fails loudly on
   mechanical problems (unkeyable background, implausible coverage); your
   job is the judgment call it can't make. If it still doesn't meet the bar
   after a couple of rounds, STOP and tell the user plainly which subject
   won't lift and why — never ship a degraded card.

4. **Write a card config per photo** (`card.config.json`), placing sprites
   yourself by looking at the photo:
   ```json
   {
     "title": "short name",
     "caption": "SMALL LABEL · <b>ACCENT</b>",
     "maxWidth": 470,
     "near": false,
     "sprites": [
       { "file": "sprite_1.png", "x": 13, "y": 76, "h": 46, "z": 85 },
       { "file": "sprite_2.png", "x": 92, "y": 46, "h": 32, "z": 55 }
     ]
   }
   ```
   - `x`/`y`: sprite center in % of the photo area — go past 0/100 slightly
     so sprites overhang the card edge (that's the look). Place each sprite
     near its real counterpart in the photo, overlapping it.
   - `h`: sprite height in % of photo height. `z`: float distance in px
     (bigger = drifts more; vary z between sprites for depth).
   - `near`: keep `false` by default. `true` adds photo-pixel background
     parallax from the depth model — it GHOSTS (doubled subject) when the
     lifted subject fills much of the frame (selfies), so only enable it for
     photos whose subjects are small/distant, and check for doubling.
   - Feel knobs (defaults are tuned; override only on request): `tiltMax`
     13, `followLag` 0.10 (lower = heavier), `spriteLag` 0.055,
     `spriteDrift` 1.5, `glare` 0.42, `nearDepth` 22.

5. **Build and review**:
   ```
   python3 scripts/build_card.py assets/ card.config.json -o card.html
   # deck — repeat <assets> <config> pairs; global feel comes from the 1st:
   python3 scripts/build_card.py a1/ c1.json a2/ c2.json -o deck.html
   ```
   Screenshot it with Playwright (rest + mid-hover after mouse moves; for a
   deck also click `#next` and check the counter/second card) and Read the
   screenshots: sprites placed well? Overhanging? Then `open card.html` for
   the user.

6. **After delivery**, tell the user the knobs live in the `CONFIG` object
   at the top of the emitted file's `<script>` — edit and reload.

## Output page behavior (already in the template — don't rebuild it)

Weighted cursor-follow tilt with lag, sprites at their own depths trailing
slightly behind the card's motion, light sweep + shifting ground shadow,
settle on leave, idle sway on touch/no-hover devices, static under
`prefers-reduced-motion`, everything inlined as data URIs (single file).

## Privacy

Personal photos and built cards must NOT be committed to this (public)
repo. Keep them in the user's own directories. Exception: `examples/`
holds a demo deck the repo owner explicitly chose to publish for
illustration — add nothing there without the same explicit ask.
