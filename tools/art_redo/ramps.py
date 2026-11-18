"""The redo's ramps and small tools: ONE module every area imports, so the same brass is the same brass on the book,
the star view, the compass and the lamp.

Warm hands, cold sky. Everything a hand made is warm (buckskin, rawhide lace, brass, tin, walnut, sepia paper, brown
iron-gall ink, brand red, bone, silk); the night and what is in it stay cold and pale blue. Ramps run dark to light.
An outline is the material's own darkest tone, never black. Light comes from the top left. Nothing here or in any
module that imports it calls random(): texture comes from hand-written tables.
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from pixelkit import Cv, rgb, mix, CLEAR, sprite, trimmed, put_centred  # noqa: E402,F401
from artlib import font, catalog, lang, chart_points  # noqa: E402,F401  (the game's font, catalog, chart layout)

OUT = ROOT / "art/redo"
TEX = OUT / "textures"


def ramp(*cols):
    return [rgb(c) for c in cols]


# ---------------------------------------------------------------------------------------------- warm: made by hand
HIDE = ramp((66, 36, 22), (100, 62, 36), (136, 92, 54), (168, 124, 80), (196, 156, 108), (220, 188, 144))  # buckskin
FLESH = ramp((112, 78, 48), (150, 112, 72), (172, 134, 92), (192, 156, 112))    # the wrap's rough inside
LACE = ramp((46, 22, 14), (82, 42, 24), (122, 70, 40), (164, 108, 66))          # rawhide thong
LEATHER = ramp((46, 20, 14), (74, 34, 22), (104, 52, 32), (138, 76, 46), (172, 108, 68))   # dark saddle leather
BRASS = ramp((58, 36, 12), (108, 74, 24), (160, 116, 40), (206, 164, 70), (242, 216, 140))
VERDIGRIS = ramp((40, 78, 70), (70, 120, 104), (128, 176, 150))
TIN = ramp((54, 48, 44), (98, 92, 84), (146, 140, 128), (194, 188, 172), (236, 232, 218))
IRON = ramp((30, 28, 32), (56, 54, 58), (90, 86, 88), (134, 130, 126))
WALNUT = ramp((40, 24, 16), (62, 38, 24), (88, 56, 34), (118, 80, 50), (150, 108, 70))
SEPIA_OUT = rgb((108, 76, 46))
SEPIA = ramp((166, 134, 90), (192, 162, 114), (208, 184, 136), (222, 202, 156), (234, 218, 178))   # the pages
FLAP_HI = rgb((244, 232, 200))                 # the back of a lifted leaf (warm, never white)
CARD = ramp((150, 124, 88), (206, 188, 150), (232, 218, 184), (244, 234, 206))  # print paper pasted on the page
INKB = ramp((50, 28, 18), (88, 56, 36), (134, 102, 72))    # iron-gall ink: text, notes, faded notes
INK_GHOST = rgb((176, 146, 104))               # ruled lines, the faintest ink
PENCIL = ramp((132, 112, 90), (160, 140, 112))
BRAND = ramp((98, 28, 18), (146, 48, 28), (184, 84, 52))   # the brand, wax, hover
BONE = ramp((126, 108, 84), (184, 168, 138), (222, 212, 188), (244, 238, 222))
THREAD = ramp((128, 104, 74), (204, 186, 150), (238, 228, 200))   # waxed linen
RIBBONS = {
    "constellations": ramp((24, 30, 70), (42, 52, 106), (64, 80, 144), (104, 124, 184), (156, 174, 222)),  # indigo
    "planets": ramp((96, 58, 10), (148, 98, 22), (194, 144, 44), (228, 192, 98), (248, 226, 154)),         # mustard
    "rare": ramp((30, 58, 46), (50, 92, 70), (80, 130, 98), (128, 172, 136), (178, 210, 178)),             # sage
    "fallen": ramp((70, 16, 20), (116, 28, 32), (162, 48, 46), (206, 96, 84), (236, 150, 132)),            # oxblood
    "notes": ramp((44, 30, 58), (72, 50, 92), (104, 76, 126), (146, 116, 164), (194, 168, 206)),            # dusk plum
    "recipes": ramp((40, 44, 50), (66, 72, 80), (98, 106, 114), (142, 150, 156), (190, 196, 198)),          # slate (0.9.0)
}
# fallen is painted but only shown while falling stars are on; notes (0.6.0) is the field notes at the back
SECTIONS = ["constellations", "planets", "rare", "fallen", "recipes", "notes"]   # recipes: 0.9.0

# ---------------------------------------------------------------------------------------------- cold: the sky
NIGHT = ramp((5, 8, 20), (7, 11, 28), (10, 16, 40), (15, 23, 54), (24, 34, 74), (38, 52, 100))
STARLIGHT = ramp((52, 80, 138), (88, 124, 186), (134, 176, 228), (188, 220, 250), (236, 246, 255))
CYAN = ramp((12, 24, 56), (18, 38, 88), (28, 56, 116), (48, 86, 148), (146, 184, 220), (226, 240, 252))  # Prussian blue
STAR_RAMPS = {  # halo, body, light, core
    "blue": ramp((40, 66, 128), (96, 140, 214), (170, 206, 250), (238, 246, 255)),
    "white": ramp((62, 72, 110), (140, 154, 196), (208, 220, 244), (255, 255, 255)),
    "yellow": ramp((96, 78, 44), (186, 158, 92), (240, 222, 150), (255, 250, 226)),
    "orange": ramp((104, 56, 34), (198, 116, 68), (244, 178, 118), (255, 236, 208)),
}
STAR_COLOURS = ["blue", "white", "yellow", "orange"]

# What the star view code should use for its code-drawn rim (spyglass copper, telescope brass), ARGB hex.
RIM_COPPER = ramp((44, 20, 10), (92, 46, 26), (142, 76, 42), (196, 116, 64), (236, 168, 112))
RIM_BRASS = BRASS


def hexs(r):
    return ", ".join("0xFF%02X%02X%02X" % c[:3] for c in r)


# ---------------------------------------------------------------------------------------------- small tools
def lit(dx, dy, r):
    """How much a point on a ball faces the top-left light, -1..1."""
    return (-dx - dy) / (max(r, 1e-6) * 1.41421)


def ball(c, cx, cy, r, rmp, steps=None, outline=True):
    """An exactly round ball lit from the top left: tones by thresholds on the facing, darkest tone as the limb."""
    n = len(rmp)
    steps = steps or [-0.55, -0.15, 0.3, 0.72][: n - 2]
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            if outline and d > r - 1:
                c.p(x, y, rmp[0])
                continue
            # a sphere's facing, not a disc's: the normal tips over towards the limb
            z = math.sqrt(max(0.0, r * r - d * d))
            f = (-dx - dy + z * 1.1) / (r * 1.78)
            k = 1
            for s in steps:
                if f > s:
                    k += 1
            c.p(x, y, rmp[min(n - 1, k)])


def mask_of(c):
    return {(x, y) for y in range(c.h) for x in range(c.w) if c.px[x, y][3]}


def depth_map(mask, diag=True):
    """Distance of every pixel in mask from the outside, in erosion steps (0 = on the boundary)."""
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, 1), (1, -1), (-1, -1)] if diag else [])
    depth, left, k = {}, set(mask), 0
    while left:
        edge = {p for p in left if any((p[0] + dx, p[1] + dy) not in left for dx, dy in nb)}
        for p in edge:
            depth[p] = k
        left -= edge
        k += 1
    return depth


def poly_mask(pts):
    """Pixels whose centre is inside a polygon (even-odd)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    out = set()
    n = len(pts)
    for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        for x in range(int(math.floor(min(xs))), int(math.ceil(max(xs))) + 1):
            px, py, inside = x + 0.5, y + 0.5, False
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def star_points(cx, cy, r_out, r_in, n=5, rot=-90.0):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180.0 / n)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def edge_lit(c, mask, hi, lo, body=None):
    """Bevel a flat shape: boundary pixels open to the top or left get hi, open to the bottom or right get lo."""
    for (x, y) in mask:
        up = (x, y - 1) not in mask or (x - 1, y) not in mask
        dn = (x, y + 1) not in mask or (x + 1, y) not in mask
        if dn:
            c.p(x, y, lo)
        elif up:
            c.p(x, y, hi)
        elif body is not None:
            c.p(x, y, body)


def to_grid(c, rows, pal, x=0, y=0):
    c.art(x, y, rows, pal)
    return c


MOON_LIT = [1.0, 0.75, 0.5, 0.25, 0.0, 0.25, 0.5, 0.75]


def moon_is_lit(phase, u, v):
    """Is the point (u, v) of the unit disc sunlit in vanilla's moon phase (0 full, 1-3 waning: lit on the left,
    4 new, 5-7 waxing: lit on the right)?"""
    k = MOON_LIT[phase]
    w = math.sqrt(max(0.0, 1 - v * v))
    if phase == 0:
        return True
    if phase == 4:
        return False
    return u < w * (2 * k - 1) if phase < 4 else u > -w * (2 * k - 1)


class Packer:
    """Puts sprites on shelves inside fixed free rectangles, in the order given (deterministic), 1 px apart."""

    def __init__(self, rects):
        self.rects = [[x, y, w, h, x, y, 0] for x, y, w, h in rects]   # x, y, w, h, cursor x, shelf y, shelf h

    def place(self, w, h):
        for r in self.rects:
            x0, y0, rw, rh, cx, sy, sh = r
            if cx + w > x0 + rw:            # new shelf
                cx, sy, sh = x0, sy + sh + 1, 0
            if cx + w <= x0 + rw and sy + h <= y0 + rh:
                r[4], r[5], r[6] = cx + w + 1, sy, max(sh, h)
                return cx, sy
        raise ValueError("no room for %dx%d" % (w, h))


def dash_starts(n, on, off, margin):
    """Where each dash of a dashed line of length n starts: whole dashes only, the same margin at both ends, so the
    line is its own mirror image and never ends on a stub; slack goes on the gaps nearest the middle, +1 each; a short
    run that can't come out even grows its margins. Twin of client/Dash.java (and curseforge brandkit.dash_run)."""
    def at(mg):
        if n < on + 2 * mg:
            return None
        m = (n - 2 * mg + off) // (on + off)
        r = g = 0
        while m > 0:
            r = n - 2 * mg - m * on - (m - 1) * off
            g = m - 1
            if r == 0 or ((r % 2 == 0 or g % 2 == 1) and r - r % 2 <= 2 * (g // 2)):
                break
            if m == 1:
                return [mg + r // 2] if r % 2 == 0 else None
            m -= 1
        if m <= 0:
            return None
        gaps = [off] * g
        if g:
            c = g // 2
            if r % 2:
                gaps[c] += 1
                r -= 1
            for i in range(g // 2):
                if r <= 0:
                    break
                gaps[c - 1 - i] += 1
                gaps[c + i + g % 2] += 1
                r -= 2
        s, x = [], mg
        for d in range(m):
            s.append(x)
            x += on + (gaps[d] if d < g else 0)
        return s
    for mg in range(margin, margin + on + off):
        s = at(mg)
        if s is not None:
            return s
    return [margin + (n - 2 * margin - on) // 2] if n >= on + 2 * margin else []


def centred_by_box(c):
    """The same picture moved so its visible box has equal room on every side (to within the 1 px parity allows)."""
    b = c.bbox()
    dx = ((c.w - 1 - b[2]) - b[0]) // 2
    dy = ((c.h - 1 - b[3]) - b[1]) // 2
    o = Cv(c.w, c.h)
    o.paste(c, dx, dy)
    return o
