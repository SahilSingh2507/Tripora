"""
Build the hero banner from a real head-on airplane photo.

    python tools/make_hero_from_photo.py path/to/plane_photo.jpg [--y0 0.09 --y1 0.55]

Writes assets/images/hero_airplane.jpg (2400x640): the aircraft "face" is cropped, scaled up
and placed flush right; the sky colour of the photo is extended to the left and deepened to
blue so the headline has clean space. The photo itself keeps its natural colours.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets" / "images"


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--y0", type=float, default=0.09)
    ap.add_argument("--y1", type=float, default=0.55)
    ap.add_argument("--shift", type=int, default=0, help="move the aircraft left(-)/right(+) in px")
    a = ap.parse_args()

    W, H = 2400, 640
    photo = Image.open(a.photo).convert("RGB")
    pw, ph = photo.size
    crop = photo.crop((0, int(ph * a.y0), pw, int(ph * a.y1)))
    scale = H / crop.height
    crop = crop.resize((round(crop.width * scale), H), Image.LANCZOS)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=2.2, percent=90, threshold=2))
    crop = ImageEnhance.Contrast(crop).enhance(1.10)
    crop = ImageEnhance.Color(crop).enhance(1.18)
    w, h = crop.size
    x0 = W - w + a.shift

    # sky colour taken from the photo's own top corners, so the seam is invisible
    small = crop.resize((w, h))
    top = small.crop((0, 0, 14, 60)).resize((1, 1), Image.BOX).getpixel((0, 0))
    mid = small.crop((0, int(h * .30), 14, int(h * .42))).resize((1, 1), Image.BOX).getpixel((0, 0))
    bg = Image.new("RGB", (W, H))
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] + (mid[i] - top[i]) * smooth(t / .7)) for i in range(3))
        col.putpixel((0, y), c)
    bg = col.resize((W, H), Image.BILINEAR)
    # deepen to a rich blue toward the left (headline side)
    deep_top, deep_bot = (14, 84, 205), (70, 160, 238)
    deep = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        deep.putpixel((0, y), tuple(int(deep_top[i] + (deep_bot[i] - deep_top[i]) * t) for i in range(3)))
    deep = deep.resize((W, H), Image.BILINEAR)
    ramp = Image.new("L", (W, 1))
    for x in range(W):
        ramp.putpixel((x, 0), int(255 * (1 - smooth((x - 700) / (x0 + w * .30 - 700)))))
    ramp = ramp.resize((W, H))
    bg = Image.composite(deep, bg, ramp)

    # feather only the photo's left edge (sky + wing stub) into the background
    fw = int(w * .26)
    mask = Image.new("L", (w, h), 255)
    edge = Image.new("L", (fw, 1))
    for x in range(fw):
        edge.putpixel((x, 0), int(255 * smooth(x / fw)))
    mask.paste(edge.resize((fw, h)), (0, 0))
    bg.paste(crop, (x0, 0), mask)

    OUT.mkdir(parents=True, exist_ok=True)
    bg.save(OUT / "hero_airplane.jpg", quality=92, optimize=True)
    print("wrote", OUT / "hero_airplane.jpg", "photo", crop.size, "at x", x0)


if __name__ == "__main__":
    main()
