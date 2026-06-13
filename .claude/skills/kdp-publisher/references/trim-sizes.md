# KDP trim sizes, margins, gutter & spine math

All values in inches unless noted. Bleed = **0.125"** on each outer edge for full-bleed interiors
and for all covers.

## Common trim sizes

| Trim | Typical use |
|---|---|
| 5 × 8 | Novels, novellas |
| 5.25 × 8 | Novels |
| 5.5 × 8.5 | Novels, non-fiction |
| 6 × 9 | Default for novels & non-fiction |
| 7 × 10 | Workbooks, technical |
| 8.5 × 8.5 | Square picture books |
| 8.5 × 11 | Activity/coloring, workbooks |

## Interior margins (no-bleed text books)

- Outside / top / bottom: **≥ 0.25"** (use 0.5–0.75" for a comfortable text block).
- **Inside (gutter)** grows with page count:

| Page count | Inside margin |
|---|---|
| 24–150 | 0.375" |
| 151–300 | 0.5" |
| 301–500 | 0.625" |
| 501–700 | 0.75" |
| 701–828 | 0.875" |

`build_interior.py` applies these automatically and mirrors them (inner vs outer) for recto/verso.

## Spine width formula (paperback, perfect bound)

`spine_width_in = page_count × per_page_thickness`

| Paper | Per-page thickness (in) |
|---|---|
| White | 0.002252 |
| Cream | 0.0025 |
| Standard color (white) | 0.002252 |
| Premium color (white) | 0.002347 |

A spine title/text is only allowed when **page_count ≥ 79**, and should stay ~0.0625" inside the
spine edges.

### Hardcover
Hardcover (case laminate) uses different math and adds wrap/hinge allowances. KDP shows the exact
required cover dimensions on the cover-upload step; use `build_cover.py --binding hardcover` to
approximate, then reconcile with the KDP template if KDP provides one.

## Full-wrap cover dimensions (paperback)

```
cover_width  = bleed + trim_width + spine_width + trim_width + bleed
             = 0.125 + trim_width + spine_width + trim_width + 0.125
cover_height = trim_height + 2 × bleed
             = trim_height + 0.25
```

Front cover = right region, back cover = left region, spine = center band of `spine_width`.
Keep text/logos ≥ 0.125" inside the trim and the spine fold lines (safe zone).

`build_cover.py` computes all of this from `--trim`, `--pages`, and `--paper`.
