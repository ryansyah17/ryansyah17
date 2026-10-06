#!/usr/bin/env python3
"""
Convert a photo into an animated ASCII-art SVG.

Usage:
    python scripts/photo_to_ascii.py source-photo.jpg ascii-portrait.svg
    python scripts/photo_to_ascii.py --demo ascii-portrait.svg      # placeholder silhouette

Tips for a good result: a close-up, well-lit, front-facing photo with a plain
background. Use --invert if your photo has a bright background.
Requires: pip install pillow  (numpy only for --demo)
"""
import argparse
from html import escape

from PIL import Image, ImageFilter, ImageOps

# ---- layout (must match the info card: 480 x 440) --------------------------
W, H = 480, 440
MARGIN = 20
COLS = 110
CHAR_W = (W - 2 * MARGIN) / COLS          # 4.0 px per character
FONT_SIZE = CHAR_W / 0.6                  # monospace glyph ~0.6em wide
LINE_H = FONT_SIZE
ROWS = int((H - 2 * MARGIN) // LINE_H)
RAMP = " .:-=+*#%@"                       # dark -> bright
ACCENT_TOP, ACCENT_BOTTOM = "#9be7ff", "#2f7fd1"


def demo_image(w=440, h=400):
    """Shaded head-and-shoulders silhouette used when no photo is supplied."""
    import numpy as np

    y, x = np.mgrid[0:h, 0:w].astype(float)
    img = np.zeros((h, w))
    light = np.array([-0.5, -0.6, 0.65])
    light /= np.linalg.norm(light)

    def shade(cx, cy, rx, ry, base, mask_extra=None):
        nx, ny = (x - cx) / rx, (y - cy) / ry
        d = nx**2 + ny**2
        inside = d < 1
        nz = np.sqrt(np.clip(1 - d, 0, 1))
        lum = np.clip(nx * light[0] + ny * light[1] + nz * light[2], 0, 1)
        val = base * (0.25 + 0.75 * lum)
        return inside, val, ny

    # shoulders / body
    inside, val, _ = shade(220, 455, 150, 190, 0.75)
    img = np.where(inside, val, img)
    # neck
    neck = (abs(x - 220) < 26) & (y > 215) & (y < 290)
    img = np.where(neck, 0.30 + 0.12 * (x - 194) / 52, img)
    # head
    inside, val, ny = shade(220, 140, 82, 104, 1.0)
    hair = np.clip((-ny - 0.30) / 0.5, 0, 1)      # soft hairline
    val = val * (1 - 0.65 * hair)
    img = np.where(inside, val, img)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype("uint8"), "L")


def to_ascii(img, invert=False):
    target_ratio = (COLS * CHAR_W) / (ROWS * LINE_H)
    img = ImageOps.exif_transpose(img).convert("L")
    img = ImageOps.fit(img, (int(400 * target_ratio), 400), centering=(0.5, 0.35))
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120))
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    if invert:
        img = ImageOps.invert(img)
    px = img.load()
    lines = []
    for r in range(ROWS):
        row = "".join(RAMP[min(len(RAMP) - 1, px[c, r] * len(RAMP) // 256)] for c in range(COLS))
        lines.append(row.rstrip())
    return lines


def build_svg(lines, title):
    text = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = MARGIN + (i + 1) * LINE_H - FONT_SIZE * 0.2
        length = len(line) * CHAR_W
        text.append(
            f'<text class="r" x="{MARGIN}" y="{y:.2f}" textLength="{length:.1f}" '
            f'lengthAdjust="spacing" style="animation-delay:{i * 0.035:.2f}s" '
            f'xml:space="preserve">{escape(line)}</text>'
        )
    body = "\n    ".join(text)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}">
  <title>{escape(title)}</title>
  <defs>
    <linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">
      <stop offset="0" stop-color="{ACCENT_TOP}"/>
      <stop offset="1" stop-color="{ACCENT_BOTTOM}"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#5BCDEC" stop-opacity="0"/>
      <stop offset="1" stop-color="#5BCDEC" stop-opacity=".28"/>
    </linearGradient>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  </defs>
  <style>
    .r {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
          font-size: {FONT_SIZE:.2f}px; fill: url(#g); animation: rowIn .6s ease-out both; }}
    .scan {{ animation: scan 5s linear 2.5s infinite backwards; }}
    @keyframes rowIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes scan {{ 0% {{ transform: translateY(-40px); }} 100% {{ transform: translateY({H}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .r, .scan {{ animation: none; }} }}
  </style>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="#0d1117"/>
    {body}
    <rect class="scan" width="{W}" height="40" fill="url(#scan)"/>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#30363d"/>
</svg>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="photo path (jpg/png)")
    ap.add_argument("output", nargs="?", default="ascii-portrait.svg")
    ap.add_argument("--demo", action="store_true", help="use a placeholder silhouette instead of a photo")
    ap.add_argument("--invert", action="store_true", help="invert brightness (for bright backgrounds)")
    ap.add_argument("--title", default="ASCII portrait")
    args = ap.parse_args()

    if args.demo:
        # with --demo the first positional is the output path
        out = args.input or args.output
        img = demo_image()
    else:
        if not args.input:
            ap.error("give a photo path, or use --demo")
        out, img = args.output, Image.open(args.input)

    lines = to_ascii(img, invert=args.invert)
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg(lines, args.title))
    print(f"wrote {out} ({COLS}x{ROWS} chars)")


if __name__ == "__main__":
    main()
