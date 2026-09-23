#!/usr/bin/env python3
"""Make assets/cover.jpg: the Standard Ebooks cover art (Daumier, "Don
Quixote and the Dead Mule", c. 1864, public domain; SE's crop is CC0) with
this edition's title set in a dark box, the way SE lays out its covers.

The result is committed, so the build doesn't need Pillow or the fonts. Rerun
by hand (macOS, needs Pillow) only to change the cover:

    curl -sLO https://raw.githubusercontent.com/standardebooks/miguel-de-cervantes-saavedra_don-quixote_john-ormsby/master/images/cover.jpg
    python3 tools/make_cover.py cover.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path("/System/Library/Fonts/Supplemental")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def main(src):
    img = Image.open(src).convert("RGB")  # 1400x2100
    w, h = img.size
    lines = [
        ("DON QUIJOTE", font("Georgia Bold.ttf", 132), 0),
        ("DE LA MANCHA", font("Georgia Bold.ttf", 84), 18),
        ("MIGUEL DE CERVANTES", font("Georgia.ttf", 56), 70),
        ("Edición anotada para angloparlantes", font("Georgia Italic.ttf", 50), 44),
    ]
    heights = []
    for text, f, _ in lines:
        l, t, r, b = f.getbbox(text)
        heights.append(b - t)
    pad = 70
    box_h = sum(heights) + sum(gap for *_, gap in lines) + 2 * pad
    box_top = 1380
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([0, box_top, w, box_top + box_h], fill=(0, 0, 0, 185))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    d = ImageDraw.Draw(img)
    y = box_top + pad
    for (text, f, gap), th in zip(lines, heights):
        y += gap
        l, t, r, b = f.getbbox(text)
        d.text(((w - (r - l)) / 2 - l, y - t), text, font=f, fill=(245, 240, 228))
        y += th
    out = ROOT / "assets/cover.jpg"
    out.parent.mkdir(exist_ok=True)
    img.convert("RGB").save(out, "JPEG", quality=85, optimize=True)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
