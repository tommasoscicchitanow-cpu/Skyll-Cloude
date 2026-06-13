# Non-fiction

Guides, how-to, self-help, business, memoir, cookbooks, academic/technical. Reflowable like a
novel, but **structured**: heading hierarchy, table of contents, figures/tables, and references.

## Authoring

1. **Define the promise**: who is the reader, what transformation/outcome does the book deliver?
   A sharp promise drives the title, the structure, and the keywords.
2. **Outline as a hierarchy**: Parts → Chapters → Sections (H1/H2/H3). Each chapter should have a
   clear objective and a takeaway/summary.
3. **Draft section by section**, keeping a source list. For factual/technical/medical/legal
   content, **fact-check every claim** and cite sources — this is mandatory and is the main
   quality risk with AI drafts.
4. **Add apparatus**: examples, checklists, callout boxes, figures/diagrams, tables, exercises.
5. **Front/back matter**: title, copyright, **table of contents** (required for non-fiction),
   foreword/intro; then notes, bibliography, glossary, index, "about the author".

Manuscript in Markdown with real heading levels so the TOC and EPUB nav build automatically:

```
# Book Title
## Part I — ...
### Chapter 1 — ...
#### Section ...
```

## Interior layout — PDF

`build_interior.py --mode structured --spec book.yaml`

- Trim sizes: **6×9** (standard), **7×10** / **8.5×11** (workbooks, lots of figures/tables).
- Auto-generated **table of contents** with page numbers.
- Distinct, consistent heading styles per level; figures with captions; tables; block quotes;
  optional running heads showing the current chapter.
- Mirrored gutter margins (computed from page count), page numbers.
- Footnotes/endnotes supported via Markdown footnote syntax.

## Kindle ebook — EPUB

```bash
pandoc manuscript.md -o book.epub \
  --metadata title="..." --metadata author="..." \
  --toc --toc-depth=3 --epub-chapter-level=2
```

Reflowable EPUB with a working nav TOC (KDP requires a logical TOC for non-fiction). Verify in
Kindle Previewer. Cookbooks/heavy-figure books may instead warrant fixed-layout — decide per title.

## KDP metadata specifics

- Title/subtitle should state the **outcome + audience** ("... A Step-by-Step Guide for ...").
- Categories: most specific non-fiction BISAC subjects (two).
- Keywords: problem/solution phrases the reader searches ("how to ...", "for beginners",
  "30-day plan"); avoid stuffing.
- Consider **hardcover** for credibility/gifting.
- Disclose AI involvement. Be especially careful with health, legal, and financial claims.
