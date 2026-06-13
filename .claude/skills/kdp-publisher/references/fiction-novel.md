# Fiction novels

Long-form prose: novels, novellas, short-story collections. Interior is **reflowable** —
the Kindle ebook is an EPUB; the paperback is a typeset PDF generated from the same manuscript.

## Authoring

Work from a manuscript in **Markdown** (one file, or one file per chapter). Structure:

```
# Book Title            <- title (H1, used for the title page only)

## Chapter One          <- each H2 starts a new chapter (page break + drop)
Prose paragraphs...

## Chapter Two
...
```

Guidance when generating or co-writing:

1. **Outline first**: premise, POV, setting, character sheets, beat sheet (3-act or save-the-cat).
   Keep a `characters.md` / `outline.md` so the model stays consistent across a long draft.
2. **Draft chapter by chapter** to control length and continuity; don't one-shot a whole novel.
3. **Length targets**: novella 17k–40k, novel 50k–110k words by genre.
4. **Revise**: line edit for voice, cut filler, vary sentence rhythm, fix continuity. AI first
   drafts must be edited — KDP penalizes unedited, generic content.
5. **Genre awareness**: honor reader expectations (romance HEA, mystery fair-play clues, etc.).

## Front / back matter (in order)

1. Title page  2. Copyright page (see template)  3. Dedication (optional)
4. (Chapters)  5. Acknowledgments / author's note  6. "Also by" / call-to-action to review.

## Interior layout — paperback PDF

`build_interior.py --mode prose --spec book.yaml`

- Trim sizes: **5×8** (mass-market feel), **5.25×8**, **6×9** (most common).
- Single column, justified, 11–12 pt serif (e.g. a Garamond/Minion-like face), ~1.3–1.45 leading.
- **Mirrored margins with gutter**: inner margin larger than outer (the script computes the
  gutter from page count). Top/bottom ~0.75–0.9".
- Running heads (author name verso / book title recto) and page numbers; suppress on chapter
  openers. Each chapter starts on a new (recto-preferred) page with a drop.

## Kindle ebook — EPUB

Generate a reflowable EPUB from the same Markdown (do **not** upload the fixed PDF as the ebook):

```bash
pandoc manuscript.md -o book.epub \
  --metadata title="Book Title" --metadata author="Author Name" \
  --toc --epub-chapter-level=2
```

(If `pandoc` isn't available, note it to the user — it's the cleanest Markdown→EPUB path.)
KDP accepts EPUB directly. Verify in Kindle Previewer before publishing.

## KDP metadata specifics

- Categories: pick the two most specific fiction subgenres (not just "Fiction").
- Keywords: tropes, setting, tone, comparable-author phrasing readers search
  ("enemies to lovers", "small town mystery", "dark academia").
- Series: set series name/number if applicable.
- Disclose AI involvement honestly (text and/or cover image).
