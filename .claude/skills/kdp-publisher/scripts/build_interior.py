#!/usr/bin/env python3
"""Assemble a print-ready KDP interior PDF.

Three modes:
  --mode prose       Fiction novel: chapters (## headings), justified body, running heads.
  --mode structured  Non-fiction: heading hierarchy (##/###/####), auto table of contents.
  --mode images      Children's / activity / low-content: one full-bleed image per page.

Input is a Markdown manuscript (prose/structured) or an --images directory (images mode),
plus a YAML book spec describing trim/paper/typography. Margins and gutter are derived from
the KDP page-count rules in kdp_specs.py.

Examples
--------
  python build_interior.py --mode prose --spec book.yaml manuscript.md -o interior.pdf
  python build_interior.py --mode structured --spec book.yaml manuscript.md -o interior.pdf
  python build_interior.py --mode images --spec book.yaml --images ./pages -o interior.pdf

This is a clean, dependency-light typesetter (reportlab). For final fiction/non-fiction
ebooks, generate the EPUB with pandoc (see the book-type references); this PDF is the
paperback/hardcover interior.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import yaml
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    NextPageTemplate, Image as RLImage,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kdp_specs import parse_trim, inside_margin, BLEED  # noqa: E402

DEFAULT_SPEC = {
    "title": "Untitled",
    "author": "Anonymous",
    "trim": "6x9",
    "paper": "white",
    "body_font": "Times-Roman",
    "body_size": 11,
    "leading": 15,
    "outer_margin": 0.6,
    "top_margin": 0.75,
    "bottom_margin": 0.75,
    "running_heads": True,
}


def load_spec(path: str | None) -> dict:
    spec = dict(DEFAULT_SPEC)
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            spec.update(yaml.safe_load(fh) or {})
    return spec


def estimate_page_count(spec: dict, body_chars: int) -> int:
    """Rough page-count estimate to pick the gutter before the real layout pass."""
    tw, th = parse_trim(spec["trim"])
    text_w = tw - 2 * spec["outer_margin"] - 0.5
    text_h = th - spec["top_margin"] - spec["bottom_margin"]
    chars_per_line = max(40, int(text_w / (spec["body_size"] * 0.0083)))
    lines_per_page = max(20, int(text_h * 72 / spec["leading"]))
    chars_per_page = chars_per_line * lines_per_page
    return max(24, round(body_chars / max(1, chars_per_page)) + 4)


def make_styles(spec: dict) -> dict:
    body = ParagraphStyle(
        "Body", fontName=spec["body_font"], fontSize=spec["body_size"],
        leading=spec["leading"], alignment=TA_JUSTIFY, firstLineIndent=spec["body_size"] * 1.4,
        spaceBefore=0, spaceAfter=0,
    )
    return {
        "body": body,
        "body_noindent": ParagraphStyle("BodyNI", parent=body, firstLineIndent=0),
        "h1_chapter": ParagraphStyle(
            "H1", fontName="Times-Bold", fontSize=spec["body_size"] + 9, leading=spec["body_size"] + 12,
            alignment=TA_CENTER, spaceBefore=spec["body_size"] * 4, spaceAfter=spec["body_size"] * 2),
        "h2": ParagraphStyle(
            "H2", fontName="Times-Bold", fontSize=spec["body_size"] + 4,
            leading=spec["body_size"] + 7, spaceBefore=18, spaceAfter=8),
        "h3": ParagraphStyle(
            "H3", fontName="Times-Bold", fontSize=spec["body_size"] + 1,
            leading=spec["body_size"] + 4, spaceBefore=12, spaceAfter=6),
        "title": ParagraphStyle(
            "Title", fontName="Times-Bold", fontSize=28, leading=34, alignment=TA_CENTER),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Times-Roman", fontSize=14, leading=18, alignment=TA_CENTER),
        "toc": ParagraphStyle("TOC", fontName=spec["body_font"], fontSize=spec["body_size"],
                              leading=spec["leading"] + 2),
    }


def parse_markdown(md: str) -> list[tuple[str, str]]:
    """Return a flat list of (kind, text) blocks. kind in {h1,h2,h3,h4,p}."""
    blocks: list[tuple[str, str]] = []
    para: list[str] = []

    def flush():
        if para:
            blocks.append(("p", " ".join(para).strip()))
            para.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush()
            blocks.append((f"h{len(m.group(1))}", m.group(2).strip()))
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
    flush()
    return blocks


def inline(text: str) -> str:
    """Minimal Markdown inline -> reportlab markup."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def build_text_pdf(md_path: str, out_path: str, spec: dict, mode: str) -> None:
    with open(md_path, "r", encoding="utf-8") as fh:
        md = fh.read()
    blocks = parse_markdown(md)
    body_chars = sum(len(t) for k, t in blocks if k == "p")

    page_count = estimate_page_count(spec, body_chars)
    gutter = inside_margin(page_count)
    tw, th = parse_trim(spec["trim"])
    page_w, page_h = tw * inch, th * inch
    outer = spec["outer_margin"] * inch
    top = spec["top_margin"] * inch
    bottom = spec["bottom_margin"] * inch
    styles = make_styles(spec)

    # Mirrored frames: recto (odd) gutter on left, verso (even) gutter on right.
    fw = page_w - gutter * inch - outer
    fh_ = page_h - top - bottom
    recto = Frame(gutter * inch, bottom, fw, fh_, id="recto")
    verso = Frame(outer, bottom, fw, fh_, id="verso")

    show_heads = spec.get("running_heads", True)

    def header(canvas, doc, recto_page: bool):
        canvas.saveState()
        n = doc.page
        if show_heads and n > 1:
            canvas.setFont(spec["body_font"], spec["body_size"] - 2)
            label = spec["title"] if recto_page else spec["author"]
            y = page_h - top + 6
            if recto_page:
                canvas.drawRightString(page_w - outer, y, label)
            else:
                canvas.drawString(outer, y, label)
        canvas.setFont(spec["body_font"], spec["body_size"] - 2)
        canvas.drawCentredString(page_w / 2, bottom - 18, str(n))
        canvas.restoreState()

    doc = BaseDocTemplate(
        out_path, pagesize=(page_w, page_h),
        leftMargin=outer, rightMargin=outer, topMargin=top, bottomMargin=bottom,
        title=spec["title"], author=spec["author"],
    )
    doc.addPageTemplates([
        PageTemplate(id="recto", frames=[recto], onPage=lambda c, d: header(c, d, True)),
        PageTemplate(id="verso", frames=[verso], onPage=lambda c, d: header(c, d, False)),
    ])

    story: list = []
    # --- Front matter ---
    story += [NextPageTemplate("verso"), Spacer(1, page_h * 0.28),
              Paragraph(inline(spec["title"]), styles["title"])]
    if spec.get("subtitle"):
        story += [Spacer(1, 12), Paragraph(inline(spec["subtitle"]), styles["subtitle"])]
    story += [Spacer(1, 36), Paragraph(spec["author"], styles["subtitle"]), PageBreak()]
    story += [Spacer(1, page_h * 0.45),
              Paragraph(spec.get("copyright", f"Copyright © {spec['author']}. All rights reserved."),
                        styles["body_noindent"]), PageBreak()]

    # --- Optional auto TOC for non-fiction ---
    if mode == "structured":
        story += [Paragraph("Contents", styles["h1_chapter"])]
        for kind, text in blocks:
            if kind in ("h2", "h3"):
                indent = "&nbsp;&nbsp;&nbsp;&nbsp;" if kind == "h3" else ""
                story.append(Paragraph(f"{indent}{inline(text)}", styles["toc"]))
        story.append(PageBreak())

    # --- Body ---
    first_para_after_head = False
    for kind, text in blocks:
        if kind == "h1":
            continue  # title only; handled in front matter
        if kind == "h2":
            story += [PageBreak(), Paragraph(inline(text), styles["h1_chapter"])]
            first_para_after_head = True
        elif kind == "h3":
            story.append(Paragraph(inline(text), styles["h2"]))
            first_para_after_head = True
        elif kind == "h4":
            story.append(Paragraph(inline(text), styles["h3"]))
            first_para_after_head = True
        else:
            st = styles["body_noindent"] if first_para_after_head else styles["body"]
            story.append(Paragraph(inline(text), st))
            first_para_after_head = False

    doc.build(story)
    print(f"[interior] wrote {out_path}  (~{page_count} pages est., gutter {gutter}\", "
          f"trim {spec['trim']})")


def build_image_pdf(images_dir: str, out_path: str, spec: dict) -> None:
    from reportlab.pdfgen import canvas as pdfcanvas
    tw, th = parse_trim(spec["trim"])
    # Full-bleed page = trim + bleed on every edge.
    page_w = (tw + 2 * BLEED) * inch
    page_h = (th + 2 * BLEED) * inch
    exts = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
    files = sorted(f for f in os.listdir(images_dir) if f.lower().endswith(exts))
    if not files:
        sys.exit(f"No images found in {images_dir}")
    c = pdfcanvas.Canvas(out_path, pagesize=(page_w, page_h))
    for name in files:
        c.drawImage(os.path.join(images_dir, name), 0, 0, width=page_w, height=page_h,
                    preserveAspectRatio=False, anchor="c")
        c.showPage()
    c.save()
    print(f"[interior] wrote {out_path}  ({len(files)} full-bleed pages, "
          f"{tw + 2*BLEED}x{th + 2*BLEED}\" with bleed)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a KDP interior PDF.")
    ap.add_argument("manuscript", nargs="?", help="Markdown manuscript (prose/structured modes)")
    ap.add_argument("--mode", required=True, choices=["prose", "structured", "images"])
    ap.add_argument("--spec", help="YAML book spec")
    ap.add_argument("--images", help="Directory of page images (images mode)")
    ap.add_argument("-o", "--out", default="interior.pdf")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    if args.mode == "images":
        if not args.images:
            ap.error("--images DIR is required for --mode images")
        build_image_pdf(args.images, args.out, spec)
    else:
        if not args.manuscript:
            ap.error("a Markdown manuscript path is required for prose/structured modes")
        build_text_pdf(args.manuscript, args.out, spec, args.mode)


if __name__ == "__main__":
    main()
