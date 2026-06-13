# KDP metadata, keywords, categories & disclosure

Metadata is half of a book's discoverability. Fill it deliberately for every title.

## Fields

- **Title** + **Subtitle**: must match the cover exactly. Non-fiction: put the outcome/keyword
  in the subtitle ("A Step-by-Step Guide to ..."). Don't keyword-stuff the title (KDP rejects it).
- **Series**: name + number if applicable (strongly boosts read-through for fiction).
- **Author / contributors**: pen name allowed; be consistent across the series.
- **Description** (~4,000 chars): hook → stakes/benefits → bullets → call to action. Light HTML
  (`<b>`, `<br>`, lists) is supported. Write for the reader, front-load the hook.
- **Keywords**: exactly **7 slots**. Each slot is a *phrase*, not a single word. Use buyer search
  language; don't repeat words already in title/category; no other authors' names, no "free",
  no quality claims. Mix: genre/trope (fiction) or problem/solution (non-fiction), audience,
  setting/tone, format/occasion.
- **Categories**: choose the **two most specific** BISAC subjects. Specific low-competition
  categories rank faster than broad ones.
- **Age & grade range** (children's): set both.

## AI content disclosure — MANDATORY

KDP asks whether the book contains **AI-generated** content (text, images, translation). If the
manuscript or cover was AI-generated (even AI-assisted beyond light editing), you must disclose it.
`kdp_upload.py` selects the disclosure during submission. Never disable or skip it — undisclosed
AI content risks account termination.

KDP distinction: "AI-generated" (AI created it) vs "AI-assisted" (you created, AI refined).
Pick honestly per KDP's current definitions.

## Pricing & royalty (quick reference)

- **Ebook 70% royalty** band: list price **$2.99–$9.99** (delivery fee deducted); outside the
  band you get 35%.
- **Paperback / hardcover**: 60% of list **minus printing cost**. Price above printing cost +
  desired margin; KDP shows printing cost once trim/page count are set.
- Check the lowest price KDP will allow (it must cover printing) before finalizing.

## Pre-publish checklist

- [ ] Title/subtitle/author match the cover art exactly.
- [ ] Description proofed; HTML renders.
- [ ] 7 keyword slots filled, no stuffing, no banned terms.
- [ ] 2 specific categories chosen.
- [ ] AI disclosure answered honestly.
- [ ] Interior PDF/EPUB and cover validated (Kindle Previewer / KDP previewer).
- [ ] Price within the intended royalty band and above printing cost.
- [ ] Rights confirmed; no infringing content.
