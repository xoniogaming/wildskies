"""The Star Atlas item icon, 16x16 (0.8.0). Round 2, owner: "more a redesign not just a repaint, ts too square ...
i want it more book", pointing at Edgy Creatures' guide book: a book lying on a diagonal, seen from above, its page
block showing as thickness, metal corner caps, a ribbon hanging out.
    python tools/art_redo/atlas_icon.py      -> previews/atlas_icon/drafts.png (+ each draft's png)

The journal is built as a slanted cover (a parallelogram: spine bottom left, fore-edge top right) over a page block
three texels thick, rasterised by pixel centres, then outlined in each material's darkest tone and detailed by hand:
brass caps on the three free corners, raised bands on the laced spine, ruled page edges, the indigo ribbon out of the
foot. The drafts differ on the cover:
  A  tin star   a brass sheriff's star pinned to the hide (the Atlas's badges)
  B  print      a cyanotype print pasted on, one star on Prussian blue
  C  strap      the print, and a rawhide strap round the fore-edge to a bone toggle
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ramps import ROOT, HIDE, LACE, SEPIA, SEPIA_OUT, CYAN, BRASS, BONE, RIBBONS  # noqa: E402
from pixelkit import Cv  # noqa: E402

INDIGO = RIBBONS["constellations"]
# the cover's corners: A top left (head of the spine), B top right, C bottom right, D bottom left (foot of the spine).
# Tilted about 13 degrees, so it reads as a book lying on a slant, not a tile.
A, B, C, D = (1.5, 3.5), (12.5, 0.5), (14.5, 9.0), (3.5, 12.0)
THICK = 3                                                  # the page block under the cover


def inside(poly, x, y):
    """Pixel centre (x, y) inside a convex polygon (either winding)."""
    n, sg = len(poly), 0
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        cr = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
        if cr != 0:
            if sg and (cr > 0) != (sg > 0):
                return False
            sg = cr
    return True


def uv(x, y):
    """Cover coordinates of a point: u along the head edge A->B, v down the spine A->D (both 0..1 on the cover)."""
    ex, ey = B[0] - A[0], B[1] - A[1]
    fx, fy = D[0] - A[0], D[1] - A[1]
    det = ex * fy - ey * fx
    px, py = x - A[0], y - A[1]
    return (px * fy - py * fx) / det, (ex * py - ey * px) / det


def down(pt, k=THICK):
    return (pt[0], pt[1] + k)


def journal(cover):
    c = Cv(16, 16)
    mat = {}
    cov = [A, B, C, D]
    tail = [D, C, down(C), down(D)]                       # the page block's foot edge
    fore = [B, C, down(C), down(B)]                       # its fore-edge on the right
    spine = [A, D, down(D), down(A)]
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            if inside(cov, px, py):
                mat[x, y] = "cover"
            elif inside(spine, px, py):
                mat[x, y] = "spine"
            elif inside(tail, px, py) or inside(fore, px, py):
                mat[x, y] = "pages"
    def is_cover(x, y):
        return mat.get((x, y)) == "cover"

    edge = {(x, y) for (x, y), m in mat.items() if m == "cover"
            and not all(is_cover(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    ring = {(x, y) for (x, y), m in mat.items() if m == "cover" and (x, y) not in edge
            and any((x + dx, y + dy) in edge for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for (x, y), m in mat.items():
        u, v = uv(x + 0.5, y + 0.5)
        if m == "cover":
            if (x, y) in edge:                             # the board's bevel: lit head and spine, dark far edges
                t = 4 if u < 0.5 and v < 0.5 or v < 0.15 else 1
            elif (x, y) in ring:                           # a tooled line pressed round the cover
                t = 1 if (x + y) % 2 == 0 or u > 0.6 or v > 0.6 else 2
            else:
                t = 3 if u + v < 0.75 else 2
            c.p(x, y, HIDE[t])
        elif m == "pages":
            c.p(x, y, SEPIA[4])
        else:
            c.p(x, y, HIDE[1])
    for (x, y), m in mat.items():                          # the leaves: a shaded line between them, every 2 rows
        if m == "pages" and mat.get((x, y - 1)) == "pages" and mat.get((x, y + 1)) == "pages":
            c.p(x, y, SEPIA[2])
    filled = set(mat)
    for y in range(16):                                    # outline in the darkest tone of what it touches
        for x in range(16):
            if (x, y) in filled:
                continue
            near = [mat[(x + dx, y + dy)] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in mat]
            if near:
                c.p(x, y, SEPIA_OUT if all(n == "pages" for n in near) else HIDE[0])
    for (x, y), m in mat.items():                          # the back board under the pages, and the seams
        if m == "pages" and (x, y + 1) not in mat:
            c.p(x, y, HIDE[1])
        if m == "pages" and mat.get((x, y - 1)) == "cover":
            c.p(x, y, HIDE[0])
        if m == "spine" and mat.get((x, y - 1)) == "cover":
            c.p(x, y, HIDE[0])
    for (x, y), m in mat.items():                          # raised bands laced across the spine
        if m == "spine" and y % 3 == 1:
            c.p(x, y, LACE[2])
    for pt, (col_a, col_b) in ((A, (BRASS[4], BRASS[3])), (B, (BRASS[4], BRASS[2])), (C, (BRASS[3], BRASS[1])),
                                (D, (BRASS[3], BRASS[1]))):
        x, y = int(pt[0]), int(pt[1])                      # brass caps on the four corners
        for dx, dy in ((0, 0), (1 if pt[0] < 8 else -1, 0), (0, 1 if pt[1] < 6 else -1)):
            if (x + dx, y + dy) in mat:
                c.p(x + dx, y + dy, col_a if (dx, dy) == (0, 0) else col_b)
    for (x, y), col in {(4, 14): INDIGO[3], (4, 15): INDIGO[1], (5, 15): INDIGO[2]}.items():
        c.p(x, y, col)                                     # the ribbon out of the foot
    cover(c, mat)
    return c


def on_cover(c, mat, u0, u1, v0, v1, colour):
    for (x, y), m in mat.items():
        if m != "cover":
            continue
        u, v = uv(x + 0.5, y + 0.5)
        if u0 <= u < u1 and v0 <= v < v1:
            c.p(x, y, colour)


def print_(c, mat):
    """A cyanotype print pasted on the cover, slanted with it: paper mount, Prussian blue, a star."""
    on_cover(c, mat, 0.30, 0.82, 0.18, 0.74, SEPIA[4])
    on_cover(c, mat, 0.38, 0.75, 0.28, 0.65, CYAN[1])
    on_cover(c, mat, 0.38, 0.75, 0.28, 0.36, CYAN[0])
    cu, cv = 0.565, 0.47
    star = None
    for (x, y), m in mat.items():
        u, v = uv(x + 0.5, y + 0.5)
        if m == "cover" and (star is None or (u - cu) ** 2 + (v - cv) ** 2 < star[0]):
            star = ((u - cu) ** 2 + (v - cv) ** 2, x, y)
    _, sx, sy = star
    c.p(sx, sy, CYAN[5])
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c.p(sx + dx, sy + dy, CYAN[4])


def tin_star(c, mat):
    """A brass sheriff's star pinned to the cover (the Atlas's badges), with a little hide tooling round it."""
    on_cover(c, mat, 0.25, 0.85, 0.14, 0.82, HIDE[3])
    cx, cy = 8, 6
    for (dx, dy), col in {(0, -2): BRASS[4], (0, -1): BRASS[3], (-2, 0): BRASS[4], (-1, 0): BRASS[3], (0, 0): BRASS[2],
                          (1, 0): BRASS[3], (2, 0): BRASS[2], (-1, 1): BRASS[3], (1, 1): BRASS[1],
                          (-2, 2): BRASS[2], (2, 2): BRASS[1], (0, 1): BRASS[1]}.items():
        c.p(cx + dx, cy + dy, col)
    c.p(cx, cy, BRASS[0])


def strap(c, mat):
    """The print, and a rawhide strap from under the cover round the fore-edge to a bone toggle."""
    print_(c, mat)
    for (x, y), col in {(13, 3): LACE[2], (13, 4): LACE[2], (14, 4): LACE[1], (14, 5): LACE[1], (15, 5): BONE[3],
                        (15, 6): BONE[1]}.items():
        c.p(x, y, col)


DRAFTS = {"A_tin_star": tin_star, "B_print": print_, "C_strap": strap}


def main():
    out = ROOT / "previews/atlas_icon"
    out.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / "src/main/resources/assets/wildskies/textures/item/star_atlas.png").convert("RGBA")
    ref = ROOT / "previews/atlas_icon/ref_ec_guidebook.png"
    ims = [("now", old)] + ([("ref (ec_ad)", Image.open(ref).convert("RGBA"))] if ref.exists() else [])
    for name, fn in DRAFTS.items():
        c = journal(fn)
        c.im.save(out / f"{name}.png")
        ims.append((name, c.im))
    S = 12
    sheet = Image.new("RGBA", (len(ims) * (16 * S + 24) + 24, 16 * S * 2 + 24 * 3 + 80), (0, 0, 0, 0))
    for i, (name, im) in enumerate(ims):
        x = 24 + i * (16 * S + 24)
        for j, bg in enumerate([(206, 211, 221, 255), (40, 36, 44, 255)]):
            y = 28 + j * (16 * S + 24)
            panel = Image.new("RGBA", (16 * S, 16 * S), bg)
            panel.alpha_composite(im.resize((16 * S, 16 * S), Image.NEAREST))
            sheet.alpha_composite(panel, (x, y))
        slot = Image.new("RGBA", (18, 18), (139, 139, 139, 255))     # as in an inventory slot, 2x and 1x
        slot.alpha_composite(im, (1, 1))
        sheet.alpha_composite(slot.resize((36, 36), Image.NEAREST), (x, 24 * 3 + 16 * S * 2 - 8))
        sheet.alpha_composite(slot, (x + 48, 24 * 3 + 16 * S * 2 + 1))
    bg = Image.new("RGBA", sheet.size, (238, 236, 230, 255))
    bg.alpha_composite(sheet)
    d = ImageDraw.Draw(bg)
    for i, (name, _) in enumerate(ims):
        d.text((24 + i * (16 * S + 24), 4), name, fill=(30, 30, 30, 255), font_size=16)
    bg.save(out / "drafts.png")
    print(out / "drafts.png")


if __name__ == "__main__":
    main()
