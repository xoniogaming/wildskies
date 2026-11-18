"""Contact sheet of the draft constellation figures (tools/drafts/figures.py), each shown twice the way the mod's own
code would draw it:
  - star view (StarViewRenderer.figure + line + the star sprites): the figure as a 2-px rope in NIGHT[4] with a
    NIGHT[5] mark every 6 px, on the NIGHT[1] sky, found-blue lines (4 px short of each star) and stars on top.
    Bright ones at the widest zoom (7.8 px a degree), hidden ones at the Star Lens zoom (half size, as in the sky).
  - the Atlas print (AtlasRenderer.chart): 115 x 75, the figure 1 px in 0xFF305694 under the lines in 0xFF6E98C8,
    clipped 1 px inside the print like the Java.
It also measures, per figure, how much of it runs within 4 px of a line in the star view (a crossing costs a few px,
running along a line a lot) and how many print pixels fall outside the print.

    python tools/drafts/figures_sheet.py   -> previews/figures/sheet.png (2x), crops/NN_<id>.png (4x)
Deterministic; nothing here touches src/.
"""
import math
import pathlib
import re
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from figures import ALL  # noqa: E402
from sky_catalog import BRIGHT, HIDDEN, HIDDEN_SCALE  # noqa: E402
from artlib import font  # noqa: E402

OUT = ROOT / "previews/figures"
NIGHT = [0x050814, 0x070B1C, 0x0A1028, 0x0F1736, 0x18224A, 0x263464]
LINE_FOUND = 0x587CBA
PRINT, CHART_LINE, CHART_FIGURE = 0x1C3874, 0x6E98C8, 0x305694
CHART_W, CHART_H = 115, 75
VIEW_W, VIEW_H = 250, 190
PX_DEG = 7.8                                   # widest zoom, GUI px per degree
LENS_PX_DEG = PX_DEG * 42 / 6.5 * HIDDEN_SCALE  # Star Lens zoom, per written degree of a hidden constellation
COLOURS = ["blue", "white", "yellow", "orange"]
BG, LABEL, SUB = 0x141318, 0xE8E2D6, 0x96929C


def rgba(c):
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255, 255)


def jhash(s):
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    return h - (1 << 32) if h >= 1 << 31 else h


def jround(v):
    return math.floor(v + 0.5)


# ------------------------------------------------------------------------------------------------ sprites
SPRITES = {}
for m in re.finditer(r'R\.put\("([^"]+)", new int\[\]\{(\d+), (\d+), (\d+), (\d+), (\d+)\}\);',
                     (ROOT / "src/main/java/wildskies/client/SkySprites.java").read_text()):
    SPRITES[m.group(1)] = tuple(int(m.group(k)) for k in range(2, 7))
TEX = {0: Image.open(ROOT / "src/main/resources/assets/wildskies/textures/gui/sky.png").convert("RGBA"),
       3: Image.open(ROOT / "src/main/resources/assets/wildskies/textures/gui/atlas.png").convert("RGBA")}


def sprite(img, name, x, y):
    t, u, v, w, h = SPRITES[name]
    img.alpha_composite(TEX[t].crop((u, v, u + w, v + h)), (x, y))


class Canvas:
    """artlib.Font draws through c.p(x, y, colour)."""

    def __init__(self, img):
        self.img = img

    def p(self, x, y, col):
        if 0 <= x < self.img.width and 0 <= y < self.img.height:
            self.img.putpixel((x, y), rgba(col))


# ------------------------------------------------------------------------------------------------ star view
def view(cid, stars, lines, paths, hidden):
    img = Image.new("RGBA", (VIEW_W, VIEW_H), rgba(NIGHT[1]))
    k = LENS_PX_DEG if hidden else PX_DEG
    xs, ys = [s[0] for s in stars], [s[1] for s in stars]
    mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    cx, cy = VIEW_W / 2, VIEW_H / 2

    def proj(x, y):
        return cx + (x - mx) * k, cy - (y - my) * k

    # the figure: StarViewRenderer.figure at full strength
    fig_px = set()
    for path in paths:
        run, prev = 0.0, None
        for b in path:
            q = proj(*b)
            if prev is not None:
                dx, dy = q[0] - prev[0], q[1] - prev[1]
                steps = int(math.ceil(max(abs(dx), abs(dy))))
                ln = math.hypot(dx, dy)
                for i in range(1, steps + 1):
                    run += ln / steps
                    gx = math.floor(prev[0] + dx * i / steps)
                    gy = math.floor(prev[1] + dy * i / steps)
                    col = NIGHT[5] if int(run) % 6 == 0 else NIGHT[4]
                    for kk in range(4):
                        px, py = gx + (kk & 1), gy + (kk >> 1)
                        if 0 <= px < VIEW_W and 0 <= py < VIEW_H:
                            img.putpixel((px, py), rgba(col))
                            fig_px.add((px, py))
            prev = q
    # the lines: StarViewRenderer.line, found colour
    q = [proj(s[0], s[1]) for s in stars]
    line_px = set()
    for a, b in lines:
        A, B = q[a], q[b]
        ax, ay = jround(A[0] - 0.5), jround(A[1] - 0.5)
        dx, dy = jround(B[0] - A[0]), jround(B[1] - A[1])
        steps = max(abs(dx), abs(dy))
        if steps <= 8:
            continue
        for i in range(4, steps - 4 + 1):
            x, y = ax + jround(dx * i / steps), ay + jround(dy * i / steps)
            if 0 <= x < VIEW_W and 0 <= y < VIEW_H:
                img.putpixel((x, y), rgba(LINE_FOUND))
                line_px.add((x, y))
    # the stars: the same sprite pick as StarViewRenderer.constellations, twinkle frame 0
    h = jhash(cid)
    for i, (x, y, mag) in enumerate(stars):
        tier = ("B" if mag <= 2 else "C") if hidden else ("A" if mag <= 1 else "B" if mag == 2 else "C")
        name = f"star_{tier}_{COLOURS[(h + i * 7) % 3]}_0"
        w, hh = SPRITES[name][3], SPRITES[name][4]
        sprite(img, name, jround(q[i][0] - w / 2), jround(q[i][1] - hh / 2))
    # how much of the figure lies within 4 px of a line pixel (crossings cost a little, running along a lot)
    near = sum(1 for (fx, fy) in fig_px
               if any((fx + ddx, fy + ddy) in line_px for ddx in range(-3, 4) for ddy in range(-3, 4)))
    return img, near


# ------------------------------------------------------------------------------------------------ Atlas print
def chart(stars, lines, paths):
    img = Image.new("RGBA", (CHART_W, CHART_H), rgba(PRINT))
    xs, ys = [s[0] for s in stars], [s[1] for s in stars]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = min((CHART_W - 20) / max(1e-3, maxx - minx), (CHART_H - 20) / max(1e-3, maxy - miny))
    midx, midy = (minx + maxx) / 2, (miny + maxy) / 2

    def pt(x, y):
        return (CHART_W // 2 + math.floor((x - midx) * scale + 0.5), CHART_H // 2 - math.floor((y - midy) * scale + 0.5))

    clipped = 0

    def segment(a, b, gap, col):
        nonlocal clipped
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = max(1, abs(dx), abs(dy))
        for kk in range(gap, n - gap + 1):
            px = a[0] + int(dx * kk / n + (0.5 if dx >= 0 else -0.5))
            py = a[1] + int(dy * kk / n + (0.5 if dy >= 0 else -0.5))
            if 1 <= px < CHART_W - 1 and 1 <= py < CHART_H - 1:
                img.putpixel((px, py), rgba(col))
            elif col == CHART_FIGURE:
                clipped += 1

    for path in paths:
        prev = None
        for o in path:
            p = pt(*o)
            if prev is not None:
                segment(prev, p, 0, CHART_FIGURE)
            prev = p
    pts = [pt(s[0], s[1]) for s in stars]
    for a, b in lines:
        segment(pts[a], pts[b], 3, CHART_LINE)
    for i, s in enumerate(stars):
        name = "cy_star_" + str(min(3, max(1, s[2])))
        w = SPRITES[name][3]
        sprite(img, name, pts[i][0] - w // 2, pts[i][1] - w // 2)
    return img, clipped


# ------------------------------------------------------------------------------------------------ sheet
def entries():
    out = [("lasso", "The Lasso", BRIGHT[0][5], BRIGHT[0][6], False, "in game")]
    for c in BRIGHT[1:]:
        out.append((c[0], c[1], c[5], c[6], False, None))
    for c in HIDDEN:
        out.append((c[0], c[1], c[4], c[5], True, None))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "crops").mkdir(exist_ok=True)
    f = font()
    cols, pad, gap = 4, 10, 6
    cell_w, cell_h = VIEW_W + gap + CHART_W, 14 + VIEW_H
    W = pad + cols * (cell_w + pad)
    rows = math.ceil(len(entries()) / cols)
    H = pad + 14 + rows * (cell_h + pad)
    sheet = Image.new("RGBA", (W, H), rgba(BG))
    c = Canvas(sheet)
    f.draw(c, pad, pad, "Wild Skies: draft constellation figures (not in the game). Left: star view when found. "
                        "Right: the Atlas print.", LABEL)
    report = []
    for n, (cid, name, stars, lines, hidden, note) in enumerate(entries()):
        paths = ALL[cid](stars)
        v, near = view(cid, stars, lines, paths, hidden)
        ch, clipped = chart(stars, lines, paths)
        x0 = pad + (n % cols) * (cell_w + pad)
        y0 = pad + 14 + (n // cols) * (cell_h + pad)
        tag = "Ref" if note else str(n)
        f.draw(c, x0, y0, f"{tag}. {name}", LABEL)
        f.right(c, x0 + cell_w, y0, "in the game already" if note else ("hidden, Star Lens" if hidden else "bright"), SUB)
        sheet.alpha_composite(v, (x0, y0 + 12))
        sheet.alpha_composite(ch, (x0 + VIEW_W + gap, y0 + 12))
        crop = sheet.crop((x0, y0, x0 + cell_w, y0 + 12 + VIEW_H))
        crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST).save(OUT / "crops" / f"{n:02d}_{cid}.png")
        report.append(f"{tag:>3} {cid:15s} near-lines {near:4d} px   print clipped {clipped:3d} px")
    sheet.resize((W * 2, H * 2), Image.NEAREST).save(OUT / "sheet.png")
    print("\n".join(report))
    print("sheet", W * 2, "x", H * 2)


if __name__ == "__main__":
    main()
