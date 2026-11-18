"""Comparison sheets for the Star Atlas repaint: before | after at 2x for the same spreads, the new pages with no
"before", the page turn, and close-ups at 4x.

    python tools/art/book_sheet.py   -> previews/book/before_after.png, new_pages.png, closeups.png
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
B = ROOT / "previews/book"
NOW = ROOT / "previews/shots"
BG = (20, 19, 24)
FG = (232, 226, 214)
SUB = (150, 146, 156)
GOLD = (226, 186, 98)
RED = (226, 120, 104)
GREEN = (150, 206, 130)


def font(size, bold=False):
    try:
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def big(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def now(n):
    """The current Atlas from the offline render (GUI scale 2) cut out and brought back to 1x."""
    im = Image.open(NOW / f"atlas_{n}.png").convert("RGBA").crop((310, 166, 970, 554))
    return im.resize((im.width // 2, im.height // 2), Image.NEAREST)


def new(name):
    return Image.open(B / name).convert("RGBA")


def before_after():
    rows = [("Contents", now(0), new("spread_contents.png")),
            ("A constellation found / not found yet", now(1), new("spread_constellation.png")),
            ("Planets", now(13), new("spread_planet.png"))]
    pad, k = 24, 2
    bw = max(r[1].width for r in rows) * k
    aw = max(r[2].width for r in rows) * k
    rh = max(max(r[1].height, r[2].height) for r in rows) * k
    W = pad * 3 + bw + aw
    H = pad + 50 + len(rows) * (rh + 40) + pad
    sh = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sh)
    d.text((pad, pad), "Star Atlas: before / after (2x)", fill=GOLD, font=font(30, True))
    d.text((pad, pad + 40), "BEFORE", fill=RED, font=font(18, True))
    d.text((pad * 2 + bw, pad + 40), "AFTER: the saddlebag journal with pasted-in prints", fill=GREEN, font=font(18, True))
    y = pad + 70
    for title, b, a in rows:
        d.text((pad, y), title, fill=SUB, font=font(16))
        bb, aa = big(b, k), big(a, k)
        sh.paste(bb, (pad, y + 22 + (rh - bb.height) // 2), bb)
        sh.paste(aa, (pad * 2 + bw, y + 22), aa)
        y += rh + 40
    sh.save(B / "before_after.png")
    print("wrote previews/book/before_after.png")


def new_pages():
    pad, k = 24, 2
    fallen = new("spread_fallen.png")
    turns = [new(f"turn_{i}.png") for i in range(4)]
    W = pad * 2 + fallen.width * k
    th = turns[0].height
    H = pad + 44 + fallen.height * k + pad + 30 + 2 * (th + pad) + pad
    W = max(W, pad * 3 + turns[0].width * 2)
    sh = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sh)
    d.text((pad, pad), "Fallen stars and the claims ledger (new, 2x)", fill=GOLD, font=font(26, True))
    f = big(fallen, k)
    sh.paste(f, (pad, pad + 44), f)
    y = pad + 44 + f.height + pad
    d.text((pad, y), "A page turning, four of its frames (1x)", fill=GOLD, font=font(26, True))
    y += 40
    for i, t in enumerate(turns):
        sh.paste(t, (pad + (i % 2) * (t.width + pad), y + (i // 2) * (th + pad)), t)
    sh.save(B / "new_pages.png")
    print("wrote previews/book/new_pages.png")


CROPS = [("spread_contents.png", (142, 16, 44, 40), "The spine: the pages dive in, the headband shows"),
         ("spread_constellation.png", (14, 38, 132, 92), "A cyanotype print in leather photo corners"),
         ("spread_constellation.png", (140, 0, 130, 56), "Ribbon tabs; the open section's runs down the page"),
         ("spread_constellation.png", (138, 176, 64, 60), "...and hangs out of the foot"),
         ("spread_constellation.png", (262, 178, 70, 38), "A lifted corner and the page arrow (mouse on it)"),
         ("spread_fallen.png", (8, 178, 70, 38), "The left page's corner and arrow"),
         ("spread_fallen.png", (26, 62, 124, 40), "Tin-star badges, pinned"),
         ("spread_planet.png", (304, 88, 40, 74), "The flap, its lace and the bone toggle"),
         ("spread_contents.png", (14, 20, 140, 50), "Lettering and the lasso flourish")]


def closeups():
    pad, k = 24, 4
    tiles = [(big(new(f).crop((x, y, x + w, y + h)), k), t) for f, (x, y, w, h), t in CROPS]
    cols = 3
    cw = max(t[0].width for t in tiles)
    chh = max(t[0].height for t in tiles)
    W = pad * (cols + 1) + cw * cols
    H = pad + 44 + ((len(tiles) + cols - 1) // cols) * (chh + 30 + pad)
    sh = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sh)
    d.text((pad, pad), "Close up (4x)", fill=GOLD, font=font(26, True))
    for i, (im, t) in enumerate(tiles):
        x = pad + (i % cols) * (cw + pad)
        y = pad + 44 + (i // cols) * (chh + 30 + pad)
        d.text((x, y), t, fill=SUB, font=font(16))
        sh.paste(im, (x, y + 24), im)
    sh.save(B / "closeups.png")
    print("wrote previews/book/closeups.png")


if __name__ == "__main__":
    before_after()
    new_pages()
    closeups()
