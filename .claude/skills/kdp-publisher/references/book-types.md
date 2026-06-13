# Book types — decision guide

The publishing engine (interior PDF, cover PDF, metadata, KDP upload) is identical for every
book. Only **authoring + interior layout** differ. Pick the path, read its reference, then
return to the shared pipeline.

## Quick router

- **Lots of images, little text per page; or grids/puzzles/blank lines** → children's /
  activity / low-content → `childrens-activity.md`. Interior = **fixed-layout PDF**.
- **Long continuous prose, chapters, a story** → fiction novel → `fiction-novel.md`.
  Interior = **reflowable** (EPUB for Kindle, typeset PDF for paperback).
- **Informational, structured, headings/sections, possibly figures, citations** →
  non-fiction → `nonfiction.md`. Interior = reflowable EPUB + structured PDF.

## What differs per type

| Aspect | Children's / Activity | Fiction novel | Non-fiction |
|---|---|---|---|
| Primary length | 24–40 pages | 50k–110k words | 20k–80k words |
| Interior layout | Fixed-layout, full-bleed images | Single text column, drop chapters | Headings hierarchy + TOC + figures |
| Kindle format | Fixed-layout / paperback-first | Reflowable EPUB | Reflowable EPUB |
| Front matter | Title page | Title, copyright, dedication | Title, copyright, TOC |
| Back matter | "The end" | Author note, also-by | Notes, bibliography, index, about author |
| Images | Core (every page) | Optional (cover only) | Figures, diagrams, screenshots |
| Trim size | 8.5×8.5, 8.5×11 | 5×8, 5.25×8, 6×9 | 6×9, 7×10, 8.5×11 |
| Fact-checking | n/a | n/a | **Required** |
| Special metadata | Age range, interest level | Genre/tropes keywords | Subject keywords, "how-to" framing |

## Output formats on KDP

Each is a separate KDP listing but reuses the same manuscript + metadata:

- **Paperback** — interior PDF + full-wrap cover PDF (`build_cover.py`).
- **Hardcover** — same as paperback but different spine math (case laminate vs perfect bound);
  KDP gives the exact spine when you reach the cover step. Use `build_cover.py --binding hardcover`.
- **Kindle ebook** — reflowable EPUB (novel/non-fiction) or fixed-layout (children's).

Recommended default: publish **paperback + Kindle ebook** together; add hardcover for
non-fiction and gift-oriented titles.
