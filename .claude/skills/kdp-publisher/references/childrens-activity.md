# Children's & activity / low-content books

This is the skill's original home. Covers picture books, coloring books, puzzle/activity books,
planners, journals, notebooks, and other "low-content" titles.

## Authoring

1. **Concept**: theme, target age range (0–2, 3–5, 6–8, 9–12), interest/skill level.
2. **Story or activity plan**: page-by-page outline. Picture books are typically 24–32 interior
   pages (multiples of 2; KDP paperback minimum 24 pages).
3. **Illustration prompts**: for each page write a precise image prompt — subject, style
   (e.g. "soft watercolor, thick outlines, flat colors"), composition, palette, and a
   **consistency anchor** (recurring character sheet) so characters stay on-model across pages.
   Generate images with an image model, then place them.
4. **Activity content**: for puzzles/coloring/planners, generate the page grids
   (mazes, sudoku, dot-to-dot, lined planner layouts, coloring line-art) directly as vector or
   high-res raster pages.

## Interior layout — fixed layout

Use `build_interior.py --mode images`. Each page is a full-bleed image (text baked into the
image or overlaid). Fixed-layout because position matters.

- Trim sizes: **8.5×8.5** (square picture book), **8.5×11** (activity/coloring).
- Full-bleed: art must extend **0.125"** past trim on every outer edge.
- Keep critical content (faces, text) **≥ 0.25"** inside the trim (safe zone).
- 300 DPI minimum for all raster art.

## Front / back matter

- Page 1: title page. Optional: copyright page.
- Last page: "The End" / about, or blank.

## Cover

`build_cover.py` — square or letter trim; bright, high-contrast, legible thumbnail title.

## KDP metadata specifics

- Set **age range** and **grade range** when prompted.
- Keywords: theme + format + occasion (e.g. "toddler coloring book", "dinosaur activity book",
  "preschool gift").
- Choose Children's categories; for activity books also consider Crafts & Hobbies.
- Disclose AI-generated illustrations/text (mandatory).
