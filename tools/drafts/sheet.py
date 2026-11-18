"""Sheets of the Star Atlas drafts for the owner: per idea, both spreads at 2x and three close-ups at 3x; plus an
overview of all four at 1x next to the Atlas as it is now.

    python tools/drafts/sheet.py      -> previews/drafts/idea_<n>.png, previews/drafts/overview.png
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
D = ROOT / "previews/drafts"
BG = (20, 19, 24)
FG = (232, 226, 214)
SUB = (150, 146, 156)
GOLD = (226, 186, 98)

IDEAS = [
    ("journal", "1  Field journal",
     "Worn oxblood leather, saddle stitching, brass corner caps. Ink charts on a pencil grid, wax seals for finds and "
     "finished sections. Ribbon tails hang out of the bottom; the open section's runs down the gutter. Dog-eared "
     "corners turn the page.",
     [(0, (226, 168, 114, 68)), (1, (26, 32, 136, 96)), (1, (24, 158, 140, 24))]),
    ("almanac", "2  Printed almanac",
     "Burgundy book cloth with a gilt rule. Printed pages: double-rule border, red running heads, page numbers, a "
     "pointing hand to turn the page. Round chart plates with a degree ring, a gilt star for finds. Tonight is a "
     "paper star wheel with a brass rivet and a window onto the sky. Ribbons out of the top.",
     [(0, (184, 44, 132, 112)), (1, (24, 36, 140, 96)), (0, (14, 50, 150, 70))]),
    ("ledger", "3  Cyanotype ledger",
     "Walnut boards on a brass hinge, brass corner plates, a strap and clasp. Ledger paper with blue rules and a red "
     "margin. Each chart is a cyanotype print (the cold sky) pasted in with photo corners; finds get a red rubber "
     "stamp; empty corners wait for the ones not found. Ribbons with brass tips.",
     [(1, (24, 32, 128, 92)), (1, (14, 156, 150, 36)), (1, (232, 168, 108, 68))]),
    ("saddlebag", "4  Saddlebag journal",
     "A soft buckskin wrap with a cut edge and fringe, a lace with a bone toggle. Sepia pages sewn through the spine. "
     "Charts drawn freehand with a compass rose, a rancher's brand stamped for finds, the moon's faces in a row, a "
     "coffee ring. Knotted cotton ribbons out of the top.",
     [(1, (14, 36, 140, 96)), (0, (180, 30, 150, 50)), (1, (0, 170, 170, 66))]),
]


def font(size, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def big(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def idea_sheet(n, key, title, desc, crops):
    spreads = [Image.open(D / f"book_{n}_{key}_{i}.png").convert("RGBA") for i in (0, 1)]
    pad = 24
    sw = spreads[0].width * 2
    W = pad * 3 + sw * 2
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = wrap(probe, desc, font(20), W - pad * 2)
    crop_ims = [big(spreads[i].crop((x, y, x + w, y + h)), 3) for i, (x, y, w, h) in crops]
    ch = max(im.height for im in crop_ims)
    H = pad + 40 + len(lines) * 26 + pad + 26 + spreads[0].height * 2 + pad + 26 + ch + pad
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, pad), title, fill=GOLD, font=font(32, True))
    y = pad + 44
    for l in lines:
        d.text((pad, y), l, fill=FG, font=font(20))
        y += 26
    y += pad // 2
    for i, (s, cap) in enumerate(zip(spreads, ("Contents", "A constellation found / not found yet"))):
        x = pad + i * (sw + pad)
        d.text((x, y), cap + "  (2x)", fill=SUB, font=font(18))
        b = big(s, 2)
        sheet.paste(b, (x, y + 26), b)
    y += 26 + spreads[0].height * 2 + pad // 2
    d.text((pad, y), "Close up (3x)", fill=SUB, font=font(18))
    x = pad
    for im in crop_ims:
        sheet.paste(im, (x, y + 26), im)
        x += im.width + pad
    out = D / f"idea_{n}.png"
    sheet.save(out)
    print("wrote", out.relative_to(ROOT))


def overview():
    pad = 20
    ims = [[Image.open(D / f"book_{n}_{key}_{i}.png").convert("RGBA") for i in (0, 1)]
           for n, (key, *_rest) in enumerate(IDEAS, 1)]
    now = Image.open(ROOT / "previews/shots/atlas_1.png").convert("RGBA").crop((300, 160, 980, 560))
    now = now.resize((now.width // 2, now.height // 2), Image.NEAREST)    # the render is at GUI scale 2
    cw, chh = ims[0][0].width, ims[0][0].height
    W = pad * 3 + cw * 2 + pad + now.width
    H = pad + 50 + (chh + 34) * 4 + pad
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, pad), "Star Atlas: four book ideas, at the size they'd be in game (1x)", fill=GOLD,
           font=font(26, True))
    y = pad + 50
    for (key, title, *_r), pair in zip(IDEAS, ims):
        d.text((pad, y), title, fill=FG, font=font(18, True))
        for i, im in enumerate(pair):
            sheet.paste(im, (pad + i * (cw + pad), y + 26), im)
        y += chh + 34
    x = pad * 3 + cw * 2
    d.text((x, pad + 50), "Now", fill=FG, font=font(18, True))
    sheet.paste(now, (x, pad + 76), now)
    sheet.save(D / "overview.png")
    print("wrote previews/drafts/overview.png")


def main():
    for n, (key, title, desc, crops) in enumerate(IDEAS, 1):
        idea_sheet(n, key, title, desc, crops)
    overview()


if __name__ == "__main__":
    main()
