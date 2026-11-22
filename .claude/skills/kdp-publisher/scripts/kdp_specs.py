"""Shared KDP geometry helpers: trim sizes, gutter margins, and spine width.

All units are inches unless noted. Used by build_interior.py and build_cover.py so the
trim-size / spine math lives in exactly one place. See references/trim-sizes.md.
"""
from __future__ import annotations

BLEED = 0.125  # KDP bleed per outer edge

# Per-page thickness for spine width, by paper type (inches).
PAPER_THICKNESS = {
    "white": 0.002252,
    "cream": 0.0025,
    "color-standard": 0.002252,
    "color-premium": 0.002347,
}

# Common trim sizes (width, height) in inches.
TRIM_SIZES = {
    "5x8": (5.0, 8.0),
    "5.25x8": (5.25, 8.0),
    "5.5x8.5": (5.5, 8.5),
    "6x9": (6.0, 9.0),
    "7x10": (7.0, 10.0),
    "8.5x8.5": (8.5, 8.5),
    "8.5x11": (8.5, 11.0),
}


def parse_trim(trim: str) -> tuple[float, float]:
    """Accept a named trim ('6x9') or 'WxH' literal and return (width, height) inches."""
    if trim in TRIM_SIZES:
        return TRIM_SIZES[trim]
    try:
        w, h = trim.lower().split("x")
        return float(w), float(h)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Unrecognized trim size: {trim!r}") from exc


def inside_margin(page_count: int) -> float:
    """KDP minimum inside (gutter) margin as a function of page count."""
    if page_count <= 150:
        return 0.375
    if page_count <= 300:
        return 0.5
    if page_count <= 500:
        return 0.625
    if page_count <= 700:
        return 0.75
    return 0.875


def spine_width(page_count: int, paper: str = "white") -> float:
    """Spine width in inches for a perfect-bound paperback."""
    if paper not in PAPER_THICKNESS:
        raise ValueError(f"Unknown paper {paper!r}; choose from {list(PAPER_THICKNESS)}")
    return page_count * PAPER_THICKNESS[paper]


def cover_size(trim: str, page_count: int, paper: str = "white") -> dict:
    """Full-wrap paperback cover geometry in inches (with bleed)."""
    tw, th = parse_trim(trim)
    spine = spine_width(page_count, paper)
    return {
        "trim_width": tw,
        "trim_height": th,
        "spine": spine,
        "width": BLEED + tw + spine + tw + BLEED,
        "height": th + 2 * BLEED,
        "spine_allows_text": page_count >= 79,
    }
