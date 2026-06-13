---
name: kdp-publisher
description: >-
  Publish books end-to-end to Amazon KDP (Kindle Direct Publishing). Generates or
  structures the manuscript, assembles print-ready interior and cover PDFs (with KDP
  trim-size and spine-width math), writes metadata, keywords and categories, and submits
  the KDP form via browser automation using production-tested workarounds. Supports three
  book types: children's & activity books, fiction novels, and non-fiction. Use whenever
  the user wants to write, format, build, lay out, or publish a book — paperback, hardcover,
  or Kindle ebook — to Amazon KDP / Kindle Direct Publishing.
---

# KDP Publisher

End-to-end pipeline for publishing books to **Amazon Kindle Direct Publishing (KDP)**.

This skill grew out of a children's-book / activity-book publisher and has been extended to
cover **fiction novels** and **non-fiction**. The publishing *engine* (interior PDF, cover PDF
with spine math, metadata, KDP form automation) is shared across all book types; only the
content-authoring and layout stage differs.

## When to use

Trigger this skill when the user wants to:

- Write or structure a book manuscript (children's, novel, or non-fiction).
- Lay out a **print-ready interior PDF** (correct trim size, margins, gutter, running heads).
- Build a **full-wrap cover PDF** with the correct spine width for a given page count.
- Write KDP **metadata** — title, subtitle, description (A+ ready), 7 keywords, categories.
- **Submit / upload** the book to KDP via browser automation.

## The pipeline (same 5 stages for every book)

1. **Author** the content → see the book-type reference below.
2. **Assemble the interior** → `scripts/build_interior.py`.
3. **Assemble the cover** → `scripts/build_cover.py` (computes spine width from page count).
4. **Write metadata / keywords / categories** → `references/metadata-keywords.md`.
5. **Submit to KDP** → `scripts/kdp_upload.py` (Playwright + CDP, with workarounds).

## Step 0 — Always start here: pick the book type

Ask the user (or infer) which path applies, then read the matching reference **before** writing:

| Book type | Reference | Interior format | Kindle ebook format |
|---|---|---|---|
| Children's picture / **activity / low-content** (planners, journals, puzzles, coloring) | `references/childrens-activity.md` | Fixed-layout PDF | Fixed-layout (often paperback-only) |
| **Fiction novel** | `references/fiction-novel.md` | Reflowable text → typeset PDF | Reflowable EPUB |
| **Non-fiction** (guide, how-to, memoir, business, academic) | `references/nonfiction.md` | Structured text + figures/TOC | Reflowable EPUB |

A book can be published as **paperback**, **hardcover**, and/or **Kindle ebook** — these are
separate KDP entries that share the same manuscript and metadata.

## Shared references

- `references/book-types.md` — decision guide + what differs per type (read if unsure).
- `references/trim-sizes.md` — KDP trim sizes, margins, gutter and spine-width formulas.
- `references/metadata-keywords.md` — how to write title/subtitle/description, the 7 keyword
  slots, category selection, AI-content disclosure, pricing & royalty notes.
- `references/kdp-automation.md` — the non-obvious KDP browser-automation workarounds
  (JS `evaluate` instead of typing, CDP `DOM.setFileInputFiles` for uploads, AI disclosure).

## Scripts

All scripts live in `scripts/`. Install deps once:

```bash
pip install -r .claude/skills/kdp-publisher/scripts/requirements.txt
python -m playwright install chromium   # only needed for kdp_upload.py
```

- `build_interior.py` — manuscript (Markdown) + book spec (YAML) → print-ready interior PDF.
  Handles novel & non-fiction typesetting (chapters, headings, TOC, running heads, page
  numbers, mirrored gutter margins) and an image-page mode for children's/activity books.
- `build_cover.py` — computes KDP spine width from page count + paper type, then renders a
  full-wrap cover PDF (back + spine + front, with 0.125" bleed) from a background image and
  title/author text.
- `kdp_upload.py` — drives a logged-in Chrome over CDP to create a KDP title, fill metadata,
  upload interior + cover PDFs, set the AI-content disclosure, and stop at the final review
  for human confirmation (it does **not** auto-publish unless `--publish` is passed).

## Guardrails (read before publishing)

- **AI disclosure is mandatory.** KDP requires you to declare AI-generated text/images.
  The automation selects the disclosure; never bypass it. See `references/metadata-keywords.md`.
- **Quality bar.** KDP increasingly removes low-value, mass-produced content. Don't ship
  unedited AI output — review, fact-check (especially non-fiction), and proofread.
- **Rights & originality.** Only publish content the user owns or has rights to. No
  copyrighted characters, trademarks, or plagiarized text.
- **Adult/explicit content** is allowed but has its own category, cover and searchability
  rules — handle metadata accordingly.
- **Never auto-publish without explicit confirmation.** `kdp_upload.py` stops at review by
  default; pass `--publish` only when the user has approved the final preview.
- The KDP form changes over time; if a selector breaks, re-inspect and update
  `references/kdp-automation.md` rather than guessing.
