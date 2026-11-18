"""One picture for the question about constellation figures: the chart as it is now, a chart without a figure (the
drafts), and the same chart with a figure drawn behind the stars (REDESIGN_PLAN item 6), in the field-journal look.

    python tools/drafts/figure_question.py   -> previews/drafts/figure_question.png
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from PIL import Image, ImageDraw  # noqa: E402
from artlib import Cv, PAPER, INK, chart_points  # noqa: E402
import books  # noqa: E402
from sheet import font, BG, FG, GOLD, SUB  # noqa: E402

ROOT = books.ROOT


def card(with_figure):
    c = Cv(150, 104)
    books.paper(c, 0, 0, 150, 104, "r", bands=(0, 0, 0))
    gx, gy, gw, gh = 13, 10, 124, 84
    for x in range(gx, gx + gw + 1, 12):
        c.vl(x, gy, gy + gh, PAPER[2])
    for yy in range(gy, gy + gh + 1, 12):
        c.hl(gx, gx + gw, yy, PAPER[2])
    if with_figure:
        pts = [(gx + x, gy + y) for x, y, _ in chart_points(books.LASSO, gw, gh)]
        # the rope: a loop round the seven loop stars, then the rope running out through the tail stars
        loop = pts[:7]
        cx = sum(p[0] for p in loop) / 7
        cy = sum(p[1] for p in loop) / 7
        rx = max(abs(p[0] - cx) for p in loop) + 5
        ry = max(abs(p[1] - cy) for p in loop) + 5
        for k in range(160):
            a = k / 160 * 2 * math.pi
            for dr in (0, 1):
                x = int(math.floor(cx + math.cos(a) * (rx + dr)))
                y = int(math.floor(cy + math.sin(a) * (ry + dr)))
                c.p(x, y, PAPER[0] if (k // 4) % 2 == 0 else PAPER[1])
        t0 = (pts[4][0] + 4, pts[4][1] + 4)
        for a, b in ((t0, (pts[7][0] + 3, pts[7][1] + 3)), ((pts[7][0] + 3, pts[7][1] + 3), (pts[8][0] + 4, pts[8][1] + 5))):
            n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
            for i in range(n + 1):
                x = int(round(a[0] + (b[0] - a[0]) * i / n))
                y = int(round(a[1] + (b[1] - a[1]) * i / n))
                c.p(x, y, PAPER[0] if (i // 3) % 2 == 0 else PAPER[1])
                c.p(x + 1, y, PAPER[1])
    books.chart(c, gx, gy, gw, gh, books.LASSO, books.ink_dot(INK[0], INK[1]), INK[1])
    return c


def main():
    now = Image.open(ROOT / "previews/shots/atlas_1.png").convert("RGBA").crop((352, 230, 580, 378))
    a = card(False).im
    b = card(True).im
    k = 3
    tiles = [(now, "Now", 1.5), (a, "A: stars and lines only (the drafts)", k), (b, "B: a figure drawn behind (the old plan)", k)]
    pad = 24
    ims = [(im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST), t) for im, t, s in tiles]
    W = pad * (len(ims) + 1) + sum(im.width for im, _ in ims)
    H = pad + 44 + 30 + max(im.height for im, _ in ims) + pad
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, pad), "Constellation charts: what did \"out redo them all\" mean?", fill=GOLD, font=font(28, True))
    x = pad
    for im, t in ims:
        d.text((x, pad + 48), t, fill=SUB, font=font(18))
        sheet.paste(im, (x, pad + 76), im if im.mode == "RGBA" else None)
        x += im.width + pad
    sheet.save(ROOT / "previews/drafts/figure_question.png")
    print("wrote previews/drafts/figure_question.png")


if __name__ == "__main__":
    main()
