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
| [`pixel-tilt-card`](https://github.com/lingjiefeng/pixel-tilt-card) ↗ | Photos → an interactive 3D-tilting card page: pixel-art sprites of the photo's own subjects float in front and overhang the edges; multiple photos become an arrow-navigable deck. Single self-contained HTML file. |

Skills that outgrow this hub move to their own repository and are listed
here with a ↗. `pixel-tilt-card` did; install it from there:

```
/plugin marketplace add lingjiefeng/pixel-tilt-card
/plugin install pixel-tilt-card@pixel-tilt-card
```

## Structure

```
prompts/            standalone prompts, organized by medium
examples/           demo output per skill
```

## Adding a skill

A skill starts here as `plugins/<plugin>/skills/<skill>/` with a `SKILL.md` describing:

1. **What it produces** — the visual outcome, ideally with an example
2. **When to use it** — the kind of content it fits
3. **The instructions/prompt itself**

Add `.claude-plugin/marketplace.json` to make the hub installable again once
a second skill lands.
