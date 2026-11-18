"""Shared ramps and plain tools for the Wild Skies redesign ("a frontier stargazer's kit", REDESIGN_PLAN.md).

Warm hands, cold sky: every made thing (leather, brass, walnut, paper, ink, wax, silk) is warm; the night and the
stars stay cold and pale blue. Every sprite, block texture and the telescope model paint from these ramps, so colours
never drift between them. Ramps run dark to light; outlines are a material's darkest tone, never black. Light from the
top left. 3-5 tones a material, texture placed by hand, no random(), alpha 0 or 255.

Also here: the game's own font (glyphs read from Minecraft's ascii.png, widths worked out the way BitmapProvider does)
so mockups show text exactly as the game would draw it, and the Atlas chart layout copied from AtlasRenderer.
"""
import io
import json
import math
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pixelkit import Cv, rgb, CLEAR, sprite, trimmed, put_centred  # noqa: E402,F401

ROOT = pathlib.Path(__file__).resolve().parent.parent
MC_JAR = ROOT / "build/moddev/artifacts/neoforge-21.1.252-client-extra-aka-minecraft-resources.jar"


def ramp(*cols):
    return [rgb(c) for c in cols]


# ------------------------------------------------------------------------------------------------ the shared ramps
LEATHER = ramp((46, 20, 14), (74, 34, 22), (104, 52, 32), (138, 76, 46), (172, 108, 68))
BRASS = ramp((62, 40, 12), (112, 78, 26), (164, 120, 44), (208, 166, 74), (240, 214, 138))
VERDIGRIS = ramp((40, 78, 70), (70, 120, 104), (128, 176, 150))
WALNUT = ramp((40, 24, 16), (62, 38, 24), (88, 56, 34), (118, 80, 50), (150, 108, 70))
PAPER = ramp((176, 150, 108), (204, 180, 134), (222, 204, 162), (236, 222, 188), (246, 236, 210))
PAPER_OUT = rgb((122, 94, 62))          # the page block's outline (paper's own darkest, below the ramp)
INK = ramp((36, 28, 30), (64, 52, 58), (112, 96, 96))
RED_INK = rgb((130, 40, 32))
PENCIL = rgb((150, 136, 120))           # pencil on paper: grid lines, sketches (text uses INK[2])
WAX = ramp((84, 16, 18), (140, 30, 28), (196, 62, 48), (232, 120, 96))
NIGHT = ramp((6, 8, 18), (10, 14, 30), (16, 22, 44), (26, 34, 64), (40, 52, 92))
STARLIGHT = ramp((70, 104, 160), (120, 162, 214), (180, 214, 246), (232, 244, 255))
IRON = ramp((34, 32, 36), (60, 58, 62), (96, 92, 94), (140, 136, 132))

# Silk ribbons, one per Atlas section (constellations, planets, rare sightings, fallen stars): dyed, faded, warm.
RIBBONS = {
    "constellations": ramp((28, 34, 74), (44, 54, 108), (66, 80, 142), (104, 122, 178)),   # indigo
    "planets": ramp((104, 64, 12), (152, 102, 24), (196, 146, 46), (226, 190, 98)),        # mustard
    "rare": ramp((34, 64, 52), (52, 96, 74), (82, 132, 100), (130, 172, 136)),             # sage
    "fallen": ramp((76, 18, 22), (120, 30, 34), (164, 50, 48), (204, 96, 84)),             # oxblood
}
SECTIONS = ["constellations", "planets", "rare", "fallen"]


def argb(c):
    """(r, g, b, a) -> the 0xAARRGGBB the Java draws text with."""
    return (0xFF << 24) | (c[0] << 16) | (c[1] << 8) | c[2]


# ------------------------------------------------------------------------------------------------ the game's font
class Font:
    """Minecraft's default font for ASCII, read from the game's own ascii.png (8x8 cells, ascent 7, advance = the
    glyph's last opaque column + 2, space 4), so a mockup's text has the game's exact widths and glyphs."""

    def __init__(self):
        z = zipfile.ZipFile(MC_JAR)
        from PIL import Image
        img = Image.open(io.BytesIO(z.read("assets/minecraft/textures/font/ascii.png"))).convert("RGBA")
        prov = [p for p in json.loads(z.read("assets/minecraft/font/include/default.json"))["providers"]
                if p.get("file", "").endswith("ascii.png")][0]
        self.glyphs, self.adv = {}, {" ": 4}
        px = img.load()
        for row, chars in enumerate(prov["chars"]):
            for col, ch in enumerate(chars):
                if ch == "\x00" or ch == " ":
                    continue
                cells = [(x, y) for y in range(8) for x in range(8) if px[col * 8 + x, row * 8 + y][3]]
                last = max((x for x, _ in cells), default=-1)
                self.glyphs[ch] = cells
                self.adv[ch] = last + 2

    def width(self, s):
        return sum(self.adv.get(ch, 6) for ch in s)

    def draw(self, c, x, y, s, col):
        for ch in s:
            for gx, gy in self.glyphs.get(ch, []):
                c.p(x + gx, y + gy, col)
            x += self.adv.get(ch, 6)
        return x

    def centred(self, c, x0, w, y, s, col):
        self.draw(c, x0 + (w - self.width(s)) // 2, y, s, col)

    def right(self, c, x1, y, s, col):
        self.draw(c, x1 - self.width(s), y, s, col)

    def split(self, s, w):
        """Greedy word wrap like the game's StringSplitter."""
        lines, cur = [], ""
        for word in s.split(" "):
            t = word if not cur else cur + " " + word
            if self.width(t) <= w or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def wrapped(self, c, x0, w, y, s, col, max_lines=9, step=10, centre=True):
        lines = self.split(s, w)[:max_lines]
        for i, l in enumerate(lines):
            if centre:
                self.centred(c, x0, w, y + i * step, l, col)
            else:
                self.draw(c, x0, y + i * step, l, col)
        return len(lines)


_FONT = None


def font():
    global _FONT
    if _FONT is None:
        _FONT = Font()
    return _FONT


# ------------------------------------------------------------------------------------------------ the sky catalog
def catalog():
    return json.loads((ROOT / "src/main/resources/wildskies/catalog.json").read_text(encoding="utf-8"))


def lang():
    return json.loads((ROOT / "src/main/resources/assets/wildskies/lang/en_us.json").read_text(encoding="utf-8"))


def chart_points(con, bw, bh, margin=20):
    """AtlasRenderer.constellation's layout: stars scaled to fit (bw - margin) x (bh - margin), centred on the box,
    y up. Returns [(x, y, mag)] relative to the box's top-left. Keep in step with the Java."""
    xs = [s[0] for s in con["stars"]]
    ys = [s[1] for s in con["stars"]]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = min((bw - margin) / max(1e-3, maxx - minx), (bh - margin) / max(1e-3, maxy - miny))
    out = []
    for x, y, m in con["stars"]:
        px = bw // 2 + int(math.floor((x - (minx + maxx) / 2) * scale + 0.5))
        py = bh // 2 - int(math.floor((y - (miny + maxy) / 2) * scale + 0.5))
        out.append((px, py, m))
    return out


def line_gapped(c, a, b, col, gap=3):
    """A 1-px line from star a to star b that stops gap px short of each (old atlases never let lines touch)."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = int(math.floor(x0 + (x1 - x0) * i / n + 0.5))
        y = int(math.floor(y0 + (y1 - y0) * i / n + 0.5))
        if max(abs(x - x0), abs(y - y0)) > gap and max(abs(x - x1), abs(y - y1)) > gap:
            c.p(x, y, col)


# ------------------------------------------------------------------------------------------------ small painters
def lit_disc(c, cx, cy, r, rmp, light=(-1, -1)):
    """A disc lit from the top left: tone picked from the direction (exact, repeatable), outline the darkest tone."""
    n = len(rmp)
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            if d > r - 1:
                c.p(x, y, rmp[0])
                continue
            lit = (dx * light[0] + dy * light[1]) / (r * 1.414)
            k = 1 + int((lit + 1) / 2 * (n - 1) + 0.25)
            c.p(x, y, rmp[max(1, min(n - 1, k))])


def bevel(c, x0, y0, x1, y1, rmp, base=2, outline=True):
    """A raised rectangle: outline, lit top/left, shaded bottom/right. x1/y1 exclusive."""
    if outline:
        c.fill(x0, y0, x1, y1, rmp[0])
        x0, y0, x1, y1 = x0 + 1, y0 + 1, x1 - 1, y1 - 1
    c.fill(x0, y0, x1, y1, rmp[base])
    c.fill(x0, y0, x1, y0 + 1, rmp[min(len(rmp) - 1, base + 1)])
    c.fill(x0, y0, x0 + 1, y1, rmp[min(len(rmp) - 1, base + 1)])
    c.fill(x0, y1 - 1, x1, y1, rmp[base - 1])
    c.fill(x1 - 1, y0 + 1, x1, y1, rmp[base - 1])


def rivet(c, x, y, rmp=BRASS):
    """2x2: a lit pixel over a dark one."""
    c.p(x, y, rmp[-1])
    c.p(x + 1, y, rmp[2])
    c.p(x, y + 1, rmp[1])
    c.p(x + 1, y + 1, rmp[0])


def wax_seal(c, cx, cy, r=6, rmp=WAX, mark="star"):
    """A pressed wax seal: an uneven blob (a few drips past the disc), lit top left, a sunken mark in the middle."""
    lit_disc(c, cx, cy, r, rmp)
    for dx, dy in ((r - 1, -3), (-r, 2), (2, r - 1)):            # blobs where the wax ran
        c.p(int(cx + dx), int(cy + dy), rmp[0])
        c.p(int(cx + dx) + (1 if dx > 0 else -1 if dx < -1 else 0), int(cy + dy) + (1 if dy > 0 else 0), rmp[1])
    lit_disc(c, cx, cy, r - 2, [rmp[0], rmp[1], rmp[1], rmp[2]], light=(1, 1))   # the pressed well, light inverted
    if mark == "star":
        x, y = int(cx) - 2, int(cy) - 2
        c.art(x, y, ["..a..", ".aba.", "abbba", ".aba.", "a...a"], {"a": rmp[3], "b": rmp[2]})


def ribbon_tail(c, x, y0, y1, rmp, w=5, fork=True):
    """A silk ribbon hanging from y0 to y1 (inclusive), w px wide: outline, a lit left fold, a sheen column, the
    end cut in a swallow-tail."""
    for y in range(y0, y1 + 1):
        c.fill(x, y, x + w, y + 1, rmp[0])
        c.fill(x + 1, y, x + w - 1, y + 1, rmp[2])
        c.p(x + 1, y, rmp[3])
        c.p(x + w - 2, y, rmp[1])
    if fork:
        mid = x + w // 2
        c.p(mid, y1, CLEAR)
        c.p(mid, y1 - 1, rmp[0])
        if w > 4:
            c.p(mid - 1, y1, rmp[0])
            c.p(mid + 1, y1, rmp[0])
    else:
        c.fill(x, y1, x + w, y1 + 1, rmp[0])


def dotted_leader(c, x0, x1, y, col, step=3):
    """Dots from x0 to x1 on row y, every step px, flush with the right end."""
    x = x1
    while x >= x0:
        c.p(x, y, col)
        x -= step


def tally(c, x, y, n, col, h=6):
    """Tally marks: groups of four strokes and a slash, 6 px per group."""
    groups, rest = divmod(n, 5)
    for g in range(groups):
        gx = x + g * 8
        for i in range(4):
            c.vl(gx + i * 1 + i, y, y + h - 1, col)
        c.line(gx - 1, y + h - 2, gx + 7, y + 1, col)
    gx = x + groups * 8
    for i in range(rest):
        c.vl(gx + i * 2, y, y + h - 1, col)


# Display capitals for the painted titles (9 px tall, thick and thin strokes, serifs). Only the letters the titles
# need; the names that change stay in the game's font so they translate.
CAPS = {
    "S": [".xxxxx.", "xx...xx", "xx.....", ".xxxx..", "...xxx.", ".....xx", ".....xx", "xx...xx", ".xxxxx."],
    "T": ["xxxxxxxx", "x..xx..x", "...xx...", "...xx...", "...xx...", "...xx...", "...xx...", "...xx...", "..xxxx.."],
    "A": ["...x....", "..xxx...", "..x.xx..", "..x.xx..", ".x...xx.", ".xxxxxx.", ".x...xx.", "x.....xx", "xx...xxx"],
    "R": ["xxxxxx.", ".xx..xx", ".xx..xx", ".xx..xx", ".xxxxx.", ".xx.xx.", ".xx..xx", ".xx..xx", "xxxx.xxx"],
    "L": ["xxxx...", ".xx....", ".xx....", ".xx....", ".xx....", ".xx....", ".xx...x", ".xx..xx", "xxxxxxx"],
    " ": ["....", "....", "....", "....", "....", "....", "....", "....", "...."],
}


def caps_width(s, gap=1):
    return sum(len(CAPS[ch][0]) + gap for ch in s) - gap


def draw_caps(c, x, y, s, col, gap=1, shadow=None):
    for ch in s:
        rows = CAPS[ch]
        for j, row in enumerate(rows):
            for i, v in enumerate(row):
                if v == "x":
                    if shadow is not None and not c.get(x + i + 1, y + j + 1)[3] == 0:
                        pass
                    c.p(x + i, y + j, col)
        x += len(rows[0]) + gap


def caps_shadowed(c, x, y, s, col, shadow, gap=1):
    """Capitals with a 1-px drop shadow to the lower right (gilt or embossed lettering)."""
    draw_caps(c, x + 1, y + 1, s, shadow, gap)
    draw_caps(c, x, y, s, col, gap)
