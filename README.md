# aesthetic-ops

A hub of skills and prompts for generating striking visuals — for content creation, video generation, slides, posts, and beyond.

Like DevOps, but for aesthetics: reusable, battle-tested recipes that turn "make it look good" into an operational capability.

## What lives here

- **Skills** — self-contained instruction sets (e.g. Claude skills) that produce a specific visual style or effect
- **Prompts** — curated prompts for image/video generation models that reliably hit a distinctive look
- **Collections** — pointers to interesting open-source visual skills from around the ecosystem

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
