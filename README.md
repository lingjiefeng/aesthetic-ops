# aesthetic-ops

A hub of skills and prompts for generating striking visuals — for content creation, video generation, slides, posts, and beyond.

Like DevOps, but for aesthetics: reusable, battle-tested recipes that turn "make it look good" into an operational capability.

## What lives here

- **Skills** — self-contained instruction sets (e.g. Claude skills) that produce a specific visual style or effect
- **Prompts** — curated prompts for image/video generation models that reliably hit a distinctive look
- **Collections** — pointers to interesting open-source visual skills from around the ecosystem

## Skills

| Skill | What it makes |
|---|---|
| [`depth-card`](skills/depth-card/) | Photos → an interactive 3D-tilting card page: pixel-art sprites of the photo's own subjects float in front and overhang the edges; multiple photos become an arrow-navigable deck. Single self-contained HTML file. |

## Showcase: depth-card

**[▶ Open the live demo](https://lingjiefeng.github.io/aesthetic-ops/skills/depth-card/examples/field-notes.html)** — hover to tilt, use the arrows (or ←/→) to flip cards.

<!-- To add a demo video: open this README on github.com, click the pencil
     (edit), and drag your screen recording (.mp4/.mov, under 100MB) into the
     editor right here. GitHub uploads it and inserts an embedded player;
     commit and the video plays inline. -->

Each card is a real photo; the pixel-art figures are that photo's own
subjects, redrawn by an image model and floating in front of the card at
their own depths:

| | | |
|---|---|---|
| ![golden hour, with cow](skills/depth-card/examples/card-golden-hour.png) | ![sunflower field](skills/depth-card/examples/card-sunflower.png) | ![lakeside daydream](skills/depth-card/examples/card-daydream.png) |

The whole deck is [one 2MB HTML file](skills/depth-card/examples/field-notes.html)
— no build, no server, works from a double-click.

## Structure

```
skills/     # one directory per skill (SKILL.md + supporting assets)
prompts/    # standalone prompt files, organized by medium
  video/
  image/
  slides/
```

## Adding a skill

Each skill gets its own directory under `skills/` with a `SKILL.md` describing:

1. **What it produces** — the visual outcome, ideally with an example
2. **When to use it** — the kind of content it fits
3. **The instructions/prompt itself**
