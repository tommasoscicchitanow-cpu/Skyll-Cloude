#!/usr/bin/env python3
"""Build a print-ready full-wrap KDP cover PDF.

Computes the spine width from page count + paper type (kdp_specs.py), lays out a back +
spine + front canvas with 0.125" bleed, optionally places a full-bleed background image,
and prints the title/author on the front and (if the book is thick enough) the spine.

Examples
--------
  python build_cover.py --trim 6x9 --pages 280 --paper cream \
      --title "My Novel" --author "A. Writer" --background art.png -o cover.pdf

  # Just compute and print the geometry (no PDF):
  python build_cover.py --trim 6x9 --pages 280 --paper cream --dimensions-only
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kdp_specs import cover_size, BLEED  # noqa: E402


def build(args) -> None:
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfgen import canvas as pdfcanvas

    geo = cover_size(args.trim, args.pages, args.paper)
    if args.binding == "hardcover":
        print("[cover] NOTE: hardcover wrap/hinge allowances differ; reconcile with the KDP "
              "cover template shown on the upload step before printing.")

    W = geo["width"] * inch
    H = geo["height"] * inch
    spine = geo["spine"] * inch
    tw = geo["trim_width"] * inch

    if args.dimensions_only:
        _print_geo(geo)
        return

    c = pdfcanvas.Canvas(args.out, pagesize=(W, H))

    # Background: full-bleed image, else a solid fill.
    if args.background and os.path.exists(args.background):
        c.drawImage(args.background, 0, 0, width=W, height=H,
                    preserveAspectRatio=False, anchor="c")
    else:
        c.setFillColor(HexColor(args.bg_color))
        c.rect(0, 0, W, H, fill=1, stroke=0)

    # Region boundaries (x): [bleed | back(tw) | spine | front(tw) | bleed]
    back_x0 = BLEED * inch
    spine_x0 = back_x0 + tw
    front_x0 = spine_x0 + spine

    # --- Front cover text (right region) ---
    safe = 0.25 * inch
    cx = front_x0 + tw / 2
    c.setFillColor(white if args.background else HexColor(args.text_color))
    c.setFont("Helvetica-Bold", args.title_size)
    _wrapped_center(c, args.title, cx, H - safe - args.title_size,
                    tw - 2 * safe, args.title_size)
    if args.author:
        c.setFont("Helvetica", args.author_size)
        c.drawCentredString(cx, BLEED * inch + safe, args.author)

    # --- Spine text (only if thick enough) ---
    if geo["spine_allows_text"] and args.title:
        c.saveState()
        c.translate(spine_x0 + spine / 2, H / 2)
        c.rotate(90)
        c.setFont("Helvetica-Bold", min(args.spine_size, spine / inch * 60))
        c.setFillColor(white if args.background else HexColor(args.text_color))
        c.drawCentredString(0, -args.spine_size * 0.35, args.title)
        c.restoreState()

    # --- Optional fold guides (off the final print; enable while designing) ---
    if args.guides:
        c.setStrokeColor(HexColor("#FF00FF"))
        c.setLineWidth(0.5)
        for x in (back_x0, spine_x0, front_x0, front_x0 + tw):
            c.line(x, 0, x, H)

    c.showPage()
    c.save()
    _print_geo(geo)
    print(f"[cover] wrote {args.out}")


def _wrapped_center(c, text, cx, y, max_w, size, leading_factor=1.15):
    """Naive word wrap centered at cx, drawing downward from y."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words, line, lines = text.split(), "", []
    for w in words:
        trial = f"{line} {w}".strip()
        if stringWidth(trial, "Helvetica-Bold", size) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    for i, ln in enumerate(lines):
        c.drawCentredString(cx, y - i * size * leading_factor, ln)


def _print_geo(geo: dict) -> None:
    print(f"[cover] trim {geo['trim_width']}x{geo['trim_height']}\"  "
          f"spine {geo['spine']:.4f}\"  full wrap {geo['width']:.4f}x{geo['height']:.4f}\" "
          f"(incl. {BLEED}\" bleed)  spine_text_allowed={geo['spine_allows_text']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a KDP full-wrap cover PDF.")
    ap.add_argument("--trim", required=True, help="e.g. 6x9 or 8.5x11")
    ap.add_argument("--pages", type=int, required=True, help="interior page count")
    ap.add_argument("--paper", default="white",
                    choices=["white", "cream", "color-standard", "color-premium"])
    ap.add_argument("--binding", default="paperback", choices=["paperback", "hardcover"])
    ap.add_argument("--title", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--background", help="full-bleed background image (PNG/JPG, 300 DPI)")
    ap.add_argument("--bg-color", default="#1B2A4A")
    ap.add_argument("--text-color", default="#FFFFFF")
    ap.add_argument("--title-size", type=float, default=42)
    ap.add_argument("--author-size", type=float, default=20)
    ap.add_argument("--spine-size", type=float, default=14)
    ap.add_argument("--guides", action="store_true", help="draw magenta fold guides (design only)")
    ap.add_argument("--dimensions-only", action="store_true", help="print geometry, no PDF")
    ap.add_argument("-o", "--out", default="cover.pdf")
    args = ap.parse_args()
    build(args)


if __name__ == "__main__":
    main()
