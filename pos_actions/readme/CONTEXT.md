# Key features

- **A line for the desks** — above the register bar, built from the
  registry, with the active one lit. The point of sale's own bar is left
  exactly as it is underneath.
- **A registry instead of five patches** — `registerArea(id, area)` on the
  `pos_actions_areas` category. Nothing about the bar has to be known by
  the module that wants to be on it.
- **`sequence`** — where the entry sits, and in what order the areas are
  asked which of them is active.
- **`screens`** — the screens that mean "we are here"; the register
  declares none and answers for everything else.
- **`isActive(pos)`** — for two desks sharing a screen and differing by the
  tab, the narrower one declared first.
- **`count(pos)`** — a badge with the work waiting at that desk.
- **`open(pos)`** — what the entry does, when navigating to the first
  screen is not enough.
- **Free** — LGPL-3, so the desks that build on it may be licensed however
  their authors like.
