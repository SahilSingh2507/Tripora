"""
Generate Tripora's three brand images with Pillow (no network needed).

    python tools/generate_assets.py

Outputs (written to assets/images/):
    tripora_logo.png       512x512  blue circle + white airplane (transparent corners)
    hero_airplane.png      2400x640 airliner flying through a blue sky with clouds
    sidebar_mountains.png  720x720  layered blue mountains, pines and a small airplane

Everything is drawn at 2x and down-sampled, so edges are smooth at any display size.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets" / "images"


# ------------------------------------------------------------------ helpers
def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def vgrad(size, top, bottom):
    """Vertical gradient image (RGB or RGBA depending on colour tuples)."""
    w, h = size
    mode = "RGBA" if len(top) == 4 else "RGB"
    ramp = Image.linear_gradient("L").resize((w, h), Image.BILINEAR)
    return Image.composite(Image.new(mode, size, bottom), Image.new(mode, size, top), ramp)


def smooth_mask(size, scale):
    m = Image.new("L", size, 0)
    return m, ImageDraw.Draw(m)


def paste_fill(layer, mask, fill):
    """Paste a flat colour or an image through a mask onto an RGBA layer."""
    if isinstance(fill, tuple):
        fill = Image.new("RGBA", layer.size, fill if len(fill) == 4 else fill + (255,))
    layer.paste(fill, (0, 0), mask)


def top_down_plane(cx, cy, size, angle_deg):
    """Polygon (list of points) of a top-down airliner silhouette; nose points up then rotated."""
    half = [(0, -52), (4.5, -46), (6.5, -30), (6.5, -8), (60, 24), (60, 33), (6.5, 12),
            (6.5, 31), (23, 43), (23, 50), (3.5, 43), (0, 52)]
    pts = half + [(-x, y) for x, y in reversed(half[1:-1])]
    a = math.radians(angle_deg)
    out = []
    for x, y in pts:
        x, y = x * size, y * size
        out.append((cx + x * math.cos(a) - y * math.sin(a),
                    cy + x * math.sin(a) + y * math.cos(a)))
    return out


# --------------------------------------------------------------------- logo
def make_logo():
    S, N = 2, 512
    big = N * S
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    mask, d = smooth_mask((big, big), S)
    d.ellipse((0, 0, big - 1, big - 1), fill=255)
    bg = vgrad((big, big), (38, 118, 255), (10, 64, 214))
    # soft highlight in the top-left
    glow = Image.new("L", (big, big), 0)
    ImageDraw.Draw(glow).ellipse((-big * .2, -big * .35, big * .75, big * .45), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(big * .06))
    bg = Image.composite(Image.new("RGB", (big, big), (140, 190, 255)), bg, glow)
    img.paste(bg, (0, 0), mask)

    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # contrail swoosh (tapered)
    pts_top, pts_bot = [], []
    for i in range(41):
        t = i / 40
        x = big * (0.17 + 0.36 * t)
        y = big * (0.72 - 0.24 * t - 0.10 * math.sin(math.pi * t) * 0.0) + big * 0.06 * (1 - t) ** 2
        w = big * 0.020 * t
        pts_top.append((x, y - w))
        pts_bot.append((x, y + w))
    ld.polygon(pts_top + pts_bot[::-1], fill=(255, 255, 255, 235))
    # airplane
    ld.polygon(top_down_plane(big * .56, big * .46, big * .0047, 48), fill=(255, 255, 255, 255))
    shadow = layer.filter(ImageFilter.GaussianBlur(big * .012))
    sh = Image.new("RGBA", (big, big), (5, 30, 120, 0))
    sh.putalpha(shadow.split()[3].point(lambda v: int(v * .35)))
    img.alpha_composite(sh, (0, int(big * .012)))
    img.alpha_composite(layer)
    img = img.resize((N, N), Image.LANCZOS)
    img.save(OUT / "tripora_logo.png", optimize=True)


# --------------------------------------------------------------------- hero
def cloud(rng, W, H, cx, cy, w, h, alpha=255, soft=1.0):
    """Return an RGBA cumulus cloud layer (white top, blue-grey underside)."""
    hi = Image.new("L", (W, H), 0)
    sh = Image.new("L", (W, H), 0)
    dh, ds = ImageDraw.Draw(hi), ImageDraw.Draw(sh)
    n = max(8, int(w / 38))
    for _ in range(n):
        x = cx + rng.uniform(-w / 2, w / 2)
        edge = 1 - abs(x - cx) / (w / 2)
        r = h * (0.28 + 0.72 * edge ** 0.8) * rng.uniform(0.55, 1.0)
        y = cy - r * rng.uniform(0.35, 0.8)
        box = (x - r * 1.15, y - r, x + r * 1.15, y + r * .85)
        dh.ellipse(box, fill=255)
        ds.ellipse((box[0] - 6, box[1] + h * .10, box[2] + 6, box[3] + h * .14), fill=255)
    base = cy + h * .08
    if base < H:
        dh.rectangle((0, base, W, H), fill=0)
    if base + h * .10 < H:
        ds.rectangle((0, base + h * .10, W, H), fill=0)
    hi = hi.filter(ImageFilter.GaussianBlur(3.2 * soft))
    sh = sh.filter(ImageFilter.GaussianBlur(6 * soft))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shade = Image.new("RGBA", (W, H), (150, 188, 232, 255))
    shade.putalpha(sh.point(lambda v: int(v * alpha / 255)))
    out.alpha_composite(shade)
    light = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    # lower part of each cloud picks up the shade colour
    ramp = Image.new("L", (W, H), 0)
    ImageDraw.Draw(ramp).rectangle((0, cy - h * .5, W, base), fill=0)
    light.putalpha(hi.point(lambda v: int(v * alpha / 255)))
    out.alpha_composite(light)
    return out


def make_sky(W, H, rng):
    sky = vgrad((W, H), (12, 76, 196), (112, 188, 246))
    # darker, richer blue in the top-left (behind the headline)
    deep = Image.new("RGB", (W, H), (8, 48, 168))
    dm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(dm).ellipse((-W * .25, -H * .9, W * .55, H * .75), fill=150)
    sky = Image.composite(deep, sky, dm.filter(ImageFilter.GaussianBlur(160)))
    # light haze toward the right
    haze = Image.new("L", (W, H), 0)
    ImageDraw.Draw(haze).ellipse((W * .55, -H * .4, W * 1.15, H * .7), fill=90)
    haze = haze.filter(ImageFilter.GaussianBlur(120))
    sky = Image.composite(Image.new("RGB", (W, H), (150, 208, 250)), sky, haze).convert("RGBA")

    # clouds: faint wisps, then bold cumulus banks along the bottom
    specs = [  # cx, cy, w, h, alpha
        (W * .98, H * .20, 520, 70, 200), (W * .90, H * .11, 380, 52, 170),
        (W * .60, H * .30, 360, 48, 90), (W * .30, H * .60, 420, 60, 110),
        (W * .50, H * .22, 300, 40, 70), (W * .08, H * .12, 360, 46, 70),
        (W * .94, H * .53, 440, 78, 235), (W * .78, H * .60, 330, 52, 220),
        (W * .05, H * .98, 640, 120, 255), (W * .24, H * 1.00, 560, 105, 255),
        (W * .43, H * 1.01, 520, 120, 255), (W * .62, H * 1.02, 560, 100, 255),
        (W * .82, H * 1.00, 620, 125, 255), (W * 1.0, H * 1.01, 540, 120, 255),
        (W * .16, H * .90, 380, 62, 235), (W * .53, H * .93, 300, 52, 235),
        (W * .93, H * .84, 420, 72, 245),
    ]
    for cx, cy, w, h, a in specs:
        sky.alpha_composite(cloud(rng, W, H, cx, cy, w, h, a))
    return sky


def make_airliner(W, H, cx, cy, S=2):
    """Front-view airliner, drawn at S x resolution and returned at W x H."""
    BW, BH = W * S, H * S
    L = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))

    def P(pts):
        return [(x * S, y * S) for x, y in pts]

    def mask_poly(pts):
        m = Image.new("L", (BW, BH), 0)
        ImageDraw.Draw(m).polygon(P(pts), fill=255)
        return m

    def mask_ell(x0, y0, x1, y1):
        m = Image.new("L", (BW, BH), 0)
        ImageDraw.Draw(m).ellipse(P([(x0, y0), (x1, y1)]), fill=255)
        return m

    def mask_rrect(x0, y0, x1, y1, r):
        m = Image.new("L", (BW, BH), 0)
        ImageDraw.Draw(m).rounded_rectangle(P([(x0, y0), (x1, y1)]), radius=r * S, fill=255)
        return m

    def vfill(y0, y1, c0, c1):
        g = vgrad((BW, max(2, int((y1 - y0) * S))), c0, c1)
        full = Image.new("RGBA", (BW, BH), c1 + (255,))
        top = Image.new("RGBA", (BW, BH), c0 + (255,))
        full.paste(top, (0, 0))
        full.paste(g, (0, int(y0 * S)))
        full.paste(Image.new("RGBA", (BW, BH - int(y1 * S)), c1 + (255,)), (0, int(y1 * S)))
        return full

    WHITE, GREY = (252, 253, 255), (178, 192, 214)

    # --- vertical tail (a thin fin seen head-on) --------------------------------
    m = mask_poly([(cx - 9, cy - 70), (cx - 3.5, cy - 262), (cx + 3.5, cy - 262), (cx + 9, cy - 70)])
    paste_fill(L, m, vfill(cy - 262, cy - 70, (245, 248, 253), (205, 216, 232)))
    m = mask_poly([(cx + 2, cy - 250), (cx + 3.5, cy - 262), (cx + 9, cy - 70), (cx + 5, cy - 70)])
    paste_fill(L, m, (150, 168, 198, 150))

    # --- horizontal stabilisers -------------------------------------------------
    for sgn in (1, -1):
        pts = [(cx + sgn * 55, cy + 2), (cx + sgn * 255, cy - 34), (cx + sgn * 262, cy - 28),
               (cx + sgn * 60, cy + 20)]
        paste_fill(L, mask_poly(pts), vfill(cy - 34, cy + 20, (236, 242, 250), (168, 184, 208)))

    # --- landing gear (main) ----------------------------------------------------
    for sgn in (1, -1):
        gx = cx + sgn * 108
        paste_fill(L, mask_rrect(gx - 5, cy + 52, gx + 5, cy + 150, 3), (62, 72, 92, 255))
        paste_fill(L, mask_poly([(gx - 3, cy + 80), (gx + 3, cy + 80), (gx - sgn * 32, cy + 150),
                                 (gx - sgn * 38, cy + 150)]), (84, 96, 120, 255))
        for dx in (-15, 15):
            paste_fill(L, mask_rrect(gx + dx - 9, cy + 146, gx + dx + 9, cy + 198, 7), (20, 24, 34, 255))
            paste_fill(L, mask_rrect(gx + dx - 3, cy + 152, gx + dx + 1, cy + 190, 2), (80, 90, 110, 255))
        paste_fill(L, mask_rrect(gx - 22, cy + 140, gx + 22, cy + 150, 4), (74, 84, 106, 255))

    # --- wings ------------------------------------------------------------------
    def wing_pts(sgn):
        top, bot = [], []
        N = 48
        for i in range(N + 1):
            t = i / N
            x = 55 + 650 * t
            yc = 40 - 166 * t ** 1.55
            th = 34 * (1 - t) + 7
            top.append((cx + sgn * x, cy + yc - th * .5))
            bot.append((cx + sgn * x, cy + yc + th * .5))
        # winglet sweeping up at the tip
        tip = [(cx + sgn * 705, cy - 130), (cx + sgn * 716, cy - 160)]
        return top + [tip[1], tip[0]] + bot[::-1]

    for sgn in (1, -1):
        pts = wing_pts(sgn)
        m = mask_poly(pts)
        paste_fill(L, m, vfill(cy - 160, cy + 60, (250, 252, 255), (172, 187, 212)))
        # dark under-edge line for depth
        edge = Image.new("L", (BW, BH), 0)
        e = ImageDraw.Draw(edge)
        trailing = [(cx + sgn * (55 + 650 * i / 48), cy + 40 - 166 * (i / 48) ** 1.55 +
                     (34 * (1 - i / 48) + 7) * .5) for i in range(49)]
        e.line(P(trailing), fill=255, width=3 * S, joint="curve")
        edge = ImageChops.multiply(edge, m)
        paste_fill(L, edge, (120, 138, 172, 190))
        # leading-edge highlight
        hl = Image.new("L", (BW, BH), 0)
        leading = [(cx + sgn * (55 + 650 * i / 48), cy + 40 - 166 * (i / 48) ** 1.55 -
                    (34 * (1 - i / 48) + 7) * .5 + 2) for i in range(49)]
        ImageDraw.Draw(hl).line(P(leading), fill=255, width=2 * S, joint="curve")
        paste_fill(L, ImageChops.multiply(hl, m), (255, 255, 255, 255))

    # --- engines ----------------------------------------------------------------
    for sgn in (1, -1):
        ex, ey, R = cx + sgn * 238, cy + 92, 64
        # pylon
        paste_fill(L, mask_poly([(ex - 15, ey - R - 40), (ex + 15, ey - R - 40), (ex + 12, ey - R + 12),
                                 (ex - 12, ey - R + 12)]), (150, 163, 190, 255))
        # nacelle body: radial-ish shading by stacked ellipses
        nac = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nac)
        steps = 40
        for k in range(steps):
            t = k / (steps - 1)
            r = R * (1 - t * .55)
            ox, oy = -sgn * 12 * t, -14 * t
            col = lerp((176, 190, 214), (255, 255, 255), t ** .8)
            nd.ellipse(P([(ex + ox - r, ey + oy - r), (ex + ox + r, ey + oy + r)]), fill=col + (255,))
        L.paste(nac, (0, 0), mask_ell(ex - R, ey - R, ex + R, ey + R))
        # intake lip
        paste_fill(L, mask_ell(ex - 54, ey - 54, ex + 54, ey + 54), (226, 232, 242, 255))
        paste_fill(L, mask_ell(ex - 49, ey - 49, ex + 49, ey + 49), vfill(ey - 49, ey + 49, (18, 28, 52), (40, 54, 86)))
        # fan blades
        fan = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fan)
        for k in range(22):
            a0 = k * 2 * math.pi / 22
            a1 = a0 + 2 * math.pi / 22 * .62
            r0, r1 = 12, 45
            fd.polygon(P([(ex + r0 * math.cos(a0), ey + r0 * math.sin(a0)),
                          (ex + r1 * math.cos(a0 + .35), ey + r1 * math.sin(a0 + .35)),
                          (ex + r1 * math.cos(a1 + .35), ey + r1 * math.sin(a1 + .35)),
                          (ex + r0 * math.cos(a1), ey + r0 * math.sin(a1))]),
                       fill=(92, 106, 138, 255) if k % 2 else (58, 70, 100, 255))
        L.paste(fan, (0, 0), mask_ell(ex - 46, ey - 46, ex + 46, ey + 46))
        # inner rings + spinner
        ring = Image.new("L", (BW, BH), 0)
        rd = ImageDraw.Draw(ring)
        rd.ellipse(P([(ex - 33, ey - 33), (ex + 33, ey + 33)]), outline=255, width=2 * S)
        paste_fill(L, ring, (130, 146, 178, 120))
        paste_fill(L, mask_ell(ex - 14, ey - 14, ex + 14, ey + 14), vfill(ey - 14, ey + 14, (240, 244, 250), (150, 164, 192)))
        paste_fill(L, mask_ell(ex - 5, ey - 5, ex + 1, ey + 1), (255, 255, 255, 230))
        # specular on the lip
        arc = Image.new("L", (BW, BH), 0)
        ImageDraw.Draw(arc).arc(P([(ex - 59, ey - 59), (ex + 59, ey + 59)]), 200, 260, fill=255, width=3 * S)
        paste_fill(L, arc, (255, 255, 255, 220))

    # --- fuselage ---------------------------------------------------------------
    fx, fy, rx, ry = cx, cy + 10, 106, 126
    body = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    steps = 70
    for k in range(steps):
        t = k / (steps - 1)
        sx, sy = rx * (1 - t * .78), ry * (1 - t * .78)
        ox, oy = -rx * .22 * t, -ry * .26 * t
        col = lerp((182, 196, 220), (255, 255, 255), t ** .65)
        bd.ellipse(P([(fx + ox - sx, fy + oy - sy), (fx + ox + sx, fy + oy + sy)]), fill=col + (255,))
    L.paste(body, (0, 0), mask_ell(fx - rx, fy - ry, fx + rx, fy + ry))
    # centre seam + subtle belly shade
    seam = Image.new("L", (BW, BH), 0)
    ImageDraw.Draw(seam).line(P([(cx, cy + 20), (cx, cy + 128)]), fill=255, width=2 * S)
    paste_fill(L, ImageChops.multiply(seam, mask_ell(fx - rx, fy - ry, fx + rx, fy + ry)), (160, 176, 204, 150))

    # windscreen
    ws = [(cx - 66, cy - 50), (cx - 40, cy - 66), (cx + 40, cy - 66), (cx + 66, cy - 50),
          (cx + 56, cy - 22), (cx + 34, cy - 14), (cx - 34, cy - 14), (cx - 56, cy - 22)]
    wm = mask_poly(ws)
    paste_fill(L, wm, vfill(cy - 66, cy - 14, (22, 38, 78), (8, 16, 38)))
    div = Image.new("L", (BW, BH), 0)
    dd = ImageDraw.Draw(div)
    for x0, x1 in ((-37, -33), (-2, -2), (33, 37)):
        dd.line(P([(cx + x0, cy - 66 + abs(x0) * .4), (cx + x1, cy - 14)]), fill=255, width=3 * S)
    paste_fill(L, ImageChops.multiply(div, wm), (226, 232, 242, 255))
    glint = Image.new("L", (BW, BH), 0)
    ImageDraw.Draw(glint).line(P([(cx - 60, cy - 50), (cx - 38, cy - 63)]), fill=255, width=3 * S)
    paste_fill(L, ImageChops.multiply(glint, wm), (150, 180, 255, 200))

    # nose landing light glow
    glow = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(P([(cx - 12, cy + 96), (cx + 12, cy + 118)]), fill=(255, 244, 190, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(9 * S))
    L.alpha_composite(glow)
    ImageDraw.Draw(L).ellipse(P([(cx - 5, cy + 102), (cx + 5, cy + 111)]), fill=(255, 250, 225, 255))

    # nose gear
    paste_fill(L, mask_rrect(cx - 4, cy + 112, cx + 4, cy + 166, 2), (70, 80, 102, 255))
    for dx in (-13, 13):
        paste_fill(L, mask_rrect(cx + dx - 8, cy + 156, cx + dx + 8, cy + 196, 6), (20, 24, 34, 255))
        paste_fill(L, mask_rrect(cx + dx - 3, cy + 161, cx + dx, cy + 190, 2), (84, 94, 114, 255))

    return L.resize((W, H), Image.LANCZOS)


def make_hero():
    W, H = 2400, 640
    rng = random.Random(7)
    sky = make_sky(W, H, rng)
    # soft halo so the aircraft separates from the sky
    halo = Image.new("L", (W, H), 0)
    ImageDraw.Draw(halo).ellipse((1000, 60, 2200, 640), fill=60)
    halo = halo.filter(ImageFilter.GaussianBlur(70))
    white = Image.new("RGBA", (W, H), (200, 228, 255, 255))
    white.putalpha(halo)
    sky.alpha_composite(white)
    plane = make_airliner(W, H, cx=1600, cy=290)
    # contact shadow of the plane on the sky behind it (very soft)
    sh = Image.new("RGBA", (W, H), (6, 40, 140, 0))
    sh.putalpha(plane.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .22)))
    sky.alpha_composite(sh, (10, 14))
    sky.alpha_composite(plane)
    sky.convert("RGB").save(OUT / "hero_airplane.png", optimize=True)


# ----------------------------------------------------------------- mountains
def ridge(rng, W, base_y, amp, rough, n=7, x_off=0.0):
    """Jagged ridge line (list of points) from midpoint displacement."""
    pts = [(-40, base_y + rng.uniform(-amp, amp) * .2), (W + 40, base_y + rng.uniform(-amp, amp) * .2)]
    disp = amp
    for _ in range(n):
        new = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            new += [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + rng.uniform(-disp, disp))]
        new.append(pts[-1])
        pts = new
        disp *= rough
    return pts


def pine(d, x, base, h, col):
    w = h * .42
    d.rectangle((x - h * .025, base - h * .08, x + h * .025, base + h * .02), fill=col)
    for i in range(5):
        t0 = i / 5
        top = base - h * (1 - t0 * .82) + h * .0
        top = base - h + h * i * .17
        bot = base - h * .08 - (4 - i) * h * .02
        half = w * (.28 + i * .17) / 1.0 * .55
        d.polygon([(x, top), (x - half, top + h * .27), (x + half, top + h * .27)], fill=col)


def make_mountains():
    N = 720
    S = 2
    W = H = N * S
    rng = random.Random(11)
    img = vgrad((W, H), (238, 245, 255), (205, 224, 250)).convert("RGBA")

    # soft sun glow
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W * .15, H * .12, W * .75, H * .55), fill=110)
    img.paste(Image.new("RGBA", (W, H), (255, 255, 255, 255)), (0, 0), glow.filter(ImageFilter.GaussianBlur(120)))

    layers = [  # base_y, amplitude, roughness, top colour, bottom colour
        (.40, 150, .52, (176, 202, 242), (214, 229, 250)),
        (.48, 140, .53, (140, 176, 234), (196, 218, 248)),
        (.57, 120, .54, (98, 144, 222), (168, 199, 242)),
        (.66, 105, .54, (62, 112, 208), (128, 170, 232)),
        (.76, 80, .55, (36, 80, 178), (80, 128, 214)),
    ]
    for base, amp, rough, c0, c1 in layers:
        line = ridge(rng, W, H * base, amp * S, rough)
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(line + [(W + 40, H), (-40, H)], fill=255)
        top = int(min(y for _, y in line))
        g = vgrad((W, H - top), c0, c1)
        fill = Image.new("RGBA", (W, H), c1 + (255,))
        fill.paste(g.convert("RGBA"), (0, top))
        img.paste(fill, (0, 0), m)

    # foreground hills + pine forest
    d = ImageDraw.Draw(img)
    dark = (22, 66, 150, 255)
    deeper = (14, 44, 112, 255)
    fore = Image.new("L", (W, H), 0)
    pts = [(-10, H * .90)]
    for i in range(0, 73):
        x = W * i / 72
        y = H * (.855 - .13 * (1 - i / 72) ** 1.8 + .02 * math.sin(i * .9)) + (1 - i / 72) * 0
        pts.append((x, y + H * .02 * (i / 72)))
    pts += [(W + 10, H), (-10, H)]
    ImageDraw.Draw(fore).polygon(pts, fill=255)
    gradf = vgrad((W, H), (26, 76, 168), (10, 34, 96))
    img.paste(gradf.convert("RGBA"), (0, 0), fore)

    # trees along the ridge: big on the left, smaller to the right
    trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(trees)
    for i in range(34):
        t = i / 33
        x = W * (0.01 + t * .98) + rng.uniform(-8, 8) * S
        ridge_y = H * (.855 - .13 * (1 - t) ** 1.8 + .02 * math.sin(t * 72 * .9)) + H * .02 * t
        h = (190 * (1 - t) ** 1.3 + 46) * S * rng.uniform(.78, 1.12)
        col = lerp((12, 44, 118, 255), (18, 58, 136, 255), t)
        pine(td, x, ridge_y + h * .12, h, col)
    for i in range(14):  # a few tall trees in front-left
        x = W * rng.uniform(0.02, .34)
        h = rng.uniform(190, 270) * S
        pine(td, x, H * rng.uniform(.93, 1.0), h, deeper)
    img.alpha_composite(trees)

    # bottom darkening so the white wordmark stays readable
    shade = vgrad((W, H), (8, 30, 92, 0), (8, 30, 92, 235))
    ramp = Image.new("L", (W, H), 0)
    ramp.paste(Image.linear_gradient("L").resize((W, int(H * .34))), (0, int(H * .66)))
    ramp.paste(255, (0, int(H * 1.0 - 1), W, H))
    shade.putalpha(ramp.point(lambda v: int(v * .78)))
    img.alpha_composite(shade)

    # small airplane + contrail
    cx, cy = W * .70, H * .20
    trail = Image.new("L", (W, H), 0)
    td = ImageDraw.Draw(trail)
    top, bot = [], []
    for i in range(51):
        t = i / 50
        x, y = cx - 40 * S - 280 * S * t, cy + 34 * S + 150 * S * t ** 1.1
        w = 7 * S * (1 - t) ** 1.2
        top.append((x, y - w))
        bot.append((x, y + w))
    td.polygon(top + bot[::-1], fill=190)
    img.paste(Image.new("RGBA", (W, H), (255, 255, 255, 255)), (0, 0), trail.filter(ImageFilter.GaussianBlur(5 * S)))
    pl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(pl).polygon(top_down_plane(cx, cy, 1.25 * S, 50), fill=255)
    sh = pl.filter(ImageFilter.GaussianBlur(6 * S)).point(lambda v: int(v * .25))
    img.paste(Image.new("RGBA", (W, H), (20, 50, 130, 255)), (4 * S, 8 * S), sh)
    img.paste(vgrad((W, H), (66, 132, 255), (24, 84, 216)).convert("RGBA"), (0, 0), pl)

    img = img.resize((N, N), Image.LANCZOS).convert("RGB")
    img.save(OUT / "sidebar_mountains.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    make_logo()
    print("logo ok")
    make_hero()
    print("hero ok")
    make_mountains()
    print("mountains ok")
