"""Star Atlas drafts: four different book ideas, each shown as its contents spread and a constellation spread.

    python tools/drafts/books.py [key ...]     -> previews/drafts/book_<n>_<key>_<0|1>.png

Static mockups only (the Java is not touched). Text is the game's own font at its real widths; the charts use
AtlasRenderer's layout and the real catalog. One example save: 5 of 24 constellations (the Lasso found on night 30 at
new moon, the Horseshoe not yet), every planet (that section finished), 1 rare sighting, 3 fallen stars; tonight is
night 31 of 48 under a half moon. All four use silk ribbons for the sections (the owner's pick over thumb tabs).

1  Field journal      worn oxblood leather, saddle stitching, brass corner caps, warm paper with foxing, ink charts on
                      a pencil grid, wax seals; ribbon tails hang out of the bottom, the open section's down the gutter.
2  Printed almanac    burgundy book cloth with gilt rules, printed pages (double-rule border, red running heads, page
                      numbers), round chart plates with a degree ring, a paper volvelle with a brass rivet and a window
                      onto the night; ribbons out of the head, a gilt star for finds.
3  Cyanotype ledger   walnut boards on a brass hinge, brass corner plates, a strap and clasp; ledger paper with blue
                      rules and a red margin; star charts as cyanotype prints pasted in with photo corners, a red
                      rubber stamp for finds; ribbons with brass tips.
4  Saddlebag journal  a soft buckskin wrap with a cut edge, a lace and a bone toggle, deckle-edged sepia pages sewn
                      through the spine, charts drawn freehand with a compass rose, a rancher's brand stamped in
                      red-brown for finds, a coffee ring; frayed cotton ribbons.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from artlib import (Cv, rgb, CLEAR, LEATHER, BRASS, VERDIGRIS, WALNUT, PAPER, PAPER_OUT, INK, RED_INK, PENCIL,  # noqa: E402
                    NIGHT, STARLIGHT, RIBBONS, SECTIONS, ramp, font, catalog, lang, chart_points, line_gapped,
                    lit_disc, rivet, wax_seal, ribbon_tail, dotted_leader, tally, caps_width, draw_caps)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "previews/drafts"
F = font()
CAT = catalog()
L = lang()
CON = {c["id"]: c for c in CAT["constellations"]}

W, H = 340, 236          # one spread's canvas (book + ribbons + strap + a little room)
STATE = {"constellations": (5, 24), "planets": (6, 6), "rare": (1, 7), "fallen": (3, None)}
LABEL = {s: L["wildskies.atlas." + s] for s in SECTIONS}
LABEL["fallen"] = L["wildskies.atlas.fallen"]
TIPS = L["wildskies.atlas.tips"]
PLAYER = "Steve"
LASSO, LASSO_NAME, LASSO_LEGEND = CON["lasso"], L["wildskies.constellation.lasso"], \
    L["wildskies.constellation.lasso.legend"]
SHOE = CON["horseshoe"]
FOUND_NOTE = "Night 30, new moon"


def best_night(h):
    f = (-h / 360.0 - 0.5) % 1.0
    return int(math.floor(f * 48)) % 48 + 1


SHOE_HINT = f"Highest at midnight around night {best_night(SHOE['h'])} of 48."


def count_text(s, sep="/"):
    a, b = STATE[s]
    return str(a) if b is None else f"{a}{sep}{b}"


def done(s):
    a, b = STATE[s]
    return b is not None and a >= b


# ================================================================================================ shared painters
GRAIN = [(3, 4, 3), (21, 9, 2), (40, 3, 4), (55, 13, 2), (11, 19, 2), (30, 24, 3), (47, 28, 2), (6, 33, 4),
         (60, 35, 2), (24, 39, 3), (38, 16, 2), (52, 21, 3)]          # (dx, dy, length) in a 64 x 42 tile
FOX = [[".b.", "bab", ".b."], ["ab", "b."], [".bb", "bab"], ["b.", "ab", ".b"]]


def paper(c, x0, y0, x1, y1, inner, rmp=PAPER, tile_off=(0, 0), foxing=(), bands=(1, 2, 3)):
    """A page: base tone, lit top edge, a worn outer edge, a stepped gutter shadow on the inner side ('r' or 'l'),
    grain dashes from a hand-placed tile (each with a pale fleck above), foxing at chosen spots."""
    c.fill(x0, y0, x1, y1, rmp[3])
    c.fill(x0, y0, x1, y0 + 1, rmp[4])
    c.fill(x0, y1 - 1, x1, y1, rmp[2])
    ox, oy = tile_off
    for ty in range(y0 - 42, y1, 42):
        for tx in range(x0 - 64, x1, 64):
            for dx, dy, n in GRAIN:
                gx, gy = tx + (dx + ox) % 64, ty + (dy + oy) % 42
                if x0 + 3 <= gx and gx + n < x1 - 8 and y0 + 3 <= gy < y1 - 3:
                    c.fill(gx, gy, gx + n, gy + 1, rmp[2])
                    c.p(gx + n, gy - 1, rmp[4])
    outer = x0 if inner == "r" else x1 - 1
    c.vl(outer, y0 + 1, y1 - 1, rmp[2])
    x = x1 - 1 if inner == "r" else x0
    for tone, w in zip((rmp[0], rmp[1], rmp[2]), bands):
        for _ in range(w):
            c.vl(x, y0, y1 - 1, tone)
            x += -1 if inner == "r" else 1
    for fx, fy, shape in foxing:
        c.art(fx, fy, shape, {"a": rmp[1], "b": rmp[2], "c": rmp[0]})


def stack_edges(c, x0, y0, x1, y1, sides, rmp=PAPER, n=3, out=PAPER_OUT):
    """The page block's edges: n stacked lines on the given sides ('b' bottom, 'l' left, 'r' right)."""
    for k in range(n):
        tone = out if k == n - 1 else (rmp[2] if k % 2 == 0 else rmp[1])
        if "b" in sides:
            c.fill(x0 - (k + 1 if "l" in sides else 0), y1 + k, x1 + (k + 1 if "r" in sides else 0), y1 + k + 1, tone)
        if "l" in sides:
            c.fill(x0 - k - 1, y0 + k + 1, x0 - k, y1 + k, tone)
        if "r" in sides:
            c.fill(x1 + k, y0 + k + 1, x1 + k + 1, y1 + k, tone)


def chart(c, x, y, bw, bh, con, star, line, gap=3, lines=True, margin=20):
    pts = [(x + px, y + py, m) for px, py, m in chart_points(con, bw, bh, margin)]
    if lines:
        for a, b in con["lines"]:
            line_gapped(c, pts[a][:2], pts[b][:2], line, gap)
    for px, py, m in pts:
        star(c, px, py, m)
    return pts


def ink_dot(col, soft):
    """Journal stars: ink dots sized by magnitude, their corners in a lighter ink (ramp steps, not alpha)."""
    def f(c, x, y, m):
        if m <= 1:
            c.art(x - 2, y - 2, ["sccs.", "ccccc", "ccccc", "ccccc", "sccs."], {"c": col, "s": soft})
            c.p(x + 2, y - 2, soft)
            c.p(x + 2, y + 2, soft)
        elif m == 2:
            c.art(x - 1, y - 1, ["scs", "ccc", "scs"], {"c": col, "s": soft})
        else:
            c.art(x - 1, y - 1, [".s.", "scs", ".s."], {"c": col, "s": soft})
    return f


def print_star(col):
    """Printed star symbols, as engraved atlases set them: 8 rays, 4 rays, a point."""
    def f(c, x, y, m):
        if m <= 1:
            c.art(x - 3, y - 3, ["c..c..c", ".c.c.c.", "..ccc..", "ccccccc", "..ccc..", ".c.c.c.", "c..c..c"], {"c": col})
        elif m == 2:
            c.art(x - 2, y - 2, ["..c..", "..c..", "ccccc", "..c..", "..c.."], {"c": col})
            c.p(x - 1, y - 1, col), c.p(x + 1, y - 1, col), c.p(x - 1, y + 1, col), c.p(x + 1, y + 1, col)
        else:
            c.art(x - 1, y - 1, [".c.", "ccc", ".c."], {"c": col})
    return f


def hand_star(col, soft):
    """Freehand marks: an asterisk, a cross, a dot with a tick."""
    def f(c, x, y, m):
        if m <= 1:
            c.art(x - 2, y - 2, ["s.c.s", ".ccc.", "ccccc", ".ccc.", "s.c.s"], {"c": col, "s": soft})
        elif m == 2:
            c.art(x - 1, y - 1, ["s.s", ".c.", "s.s"], {"c": col, "s": soft})
            c.p(x, y - 1, col), c.p(x, y + 1, col), c.p(x - 1, y, col), c.p(x + 1, y, col)
        else:
            c.art(x - 1, y - 1, ["...", ".cs", "..."], {"c": col, "s": soft})
    return f


def dog_ear(c, x0, y1, side, rmp=PAPER, arrow_col=INK[1], s=13):
    """A folded-down bottom corner; the page-turn arrow lives on the flap. side 'l': the page's outer edge is x0
    (inclusive); 'r': the outer edge is x0 (exclusive)."""
    def X(i):
        return x0 + i if side == "l" else x0 - 1 - i
    for j in range(s):                         # the corner itself is gone: the page under it shows, shaded
        for i in range(s - 1 - j):
            c.p(X(i), y1 - 1 - j, PAPER_OUT if i == 0 or j == 0 else rmp[1])
    for j in range(s):                         # the flap: the back of the page, folded up, lit, outlined
        for i in range(j, s):
            edge = i == j or i == s - 1 or j == 0
            c.p(X(i), y1 - s + j, PAPER_OUT if edge else (rmp[4] if i - j < 3 else rmp[3]))
    for j in range(1, s + 1):                  # the flap's shadow
        c.p(X(s), y1 - s + j - 1, rmp[1])
    ax = X(s - 7) if side == "l" else X(s - 2)
    rows = [".a...", "aaaaa", ".a..."] if side == "l" else ["...a.", "aaaaa", "...a."]
    c.art(ax, y1 - s + 2, rows, {"a": arrow_col})


def moon_phase(c, cx, cy, r, col, hatch, lit_left=False):
    """An ink moon at half phase: outline, the dark half hatched on a 3-px diagonal."""
    c.ring(cx, cy, r - 1, r, col)
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            dark = dx < 0 if not lit_left else dx > 0
            if math.hypot(dx, dy) < r - 1.5 and dark and (x + y) % 3 == 0:
                c.p(x, y, hatch)
    c.vl(int(cx), int(cy - r + 1), int(cy + r - 2), col)


def vignette(c, x, y, col, soft):
    """A small pencil sketch for an empty foot of a page: a mesa on the horizon, a saguaro, a falling star."""
    c.hl(x, x + 69, y + 16, soft)
    c.art(x + 6, y + 9, ["...cccccccc....", "..c........c...", ".c..........c..", "c............cc"],
          {"c": col})
    c.art(x + 44, y + 6, ["..c..", "c.c..", "c.c.c", "ccc.c", "..ccc", "..c..", "..c..", "..c.."], {"c": col})
    c.art(x + 52, y + 0, ["s......", ".s.....", "..cc...", "...ccc.", "....ccc"], {"c": col, "s": soft})


# ================================================================================================ 1. field journal
def stitches(c, x0, y0, x1, y1, thread, hole, step=4, run=2):
    for x in range(x0 + 4, x1 - 3, step):
        for yy in (y0, y1):
            c.fill(x, yy, x + run, yy + 1, thread)
            c.p(x + run, yy, hole)
    for y in range(y0 + 4, y1 - 3, step):
        for xx in (x0, x1):
            c.fill(xx, y, xx + 1, y + run, thread)
            c.p(xx, y + run, hole)


def brass_cap(c, x, y, corner, n=13):
    """A brass corner protector: a triangle, legs n px, with a bevelled inner edge and a rivet. Lit along the edges
    that face the top left."""
    fx = 1 if corner in ("tl", "bl") else -1
    fy = 1 if corner in ("tl", "tr") else -1
    for j in range(n):
        for i in range(n - j):
            d = i + j
            if d == n - 1:
                tone = BRASS[0]
            elif d == n - 2:
                tone = BRASS[1] if corner in ("tl",) else BRASS[1]
            elif d == n - 3 and corner == "tl":
                tone = BRASS[4]
            elif (i == 0 and fx == 1) or (j == 0 and fy == 1):
                tone = BRASS[3] if corner == "tl" else BRASS[2]
            elif (i == 0 and fx == -1) or (j == 0 and fy == -1):
                tone = BRASS[1]
            else:
                tone = BRASS[2]
            c.p(x + fx * i, y + fy * j, tone)
    c.p(x + fx * 1, y + fy * 1, BRASS[4] if corner == "tl" else BRASS[3])
    rivet(c, x + (3 if fx == 1 else -4), y + (3 if fy == 1 else -4))


def leather_cover(c, bx, by, w, h, rmp=LEATHER):
    c.fill(bx, by, bx + w, by + h, rmp[0])
    c.fill(bx + 1, by + 1, bx + w - 1, by + h - 1, rmp[2])
    c.hl(bx + 1, bx + w - 2, by + 1, rmp[3])
    c.vl(bx + 1, by + 1, by + h - 2, rmp[3])
    c.hl(bx + 2, bx + w - 2, by + h - 2, rmp[1])
    c.vl(bx + w - 2, by + 2, by + h - 2, rmp[1])
    # creases: dark dashes with a lit lip, along the margins that show round the pages
    for gx, gy, n in ((22, 4, 4), (58, 5, 3), (101, 4, 5), (134, 5, 3), (190, 4, 4), (231, 5, 3), (279, 4, 5),
                      (30, h - 4, 4), (84, h - 5, 3), (150, h - 4, 4), (220, h - 5, 5), (290, h - 4, 3)):
        c.fill(bx + gx, by + gy, bx + gx + n, by + gy + 1, rmp[1])
        c.p(bx + gx + n, by + gy - 1, rmp[3])
    for gx, gy, n in ((4, 40, 4), (5, 92, 3), (4, 150, 4), (w - 5, 30, 3), (w - 6, 110, 4), (w - 5, 160, 3)):
        c.fill(bx + gx, by + gy, bx + gx + 1, by + gy + n, rmp[1])
        c.p(bx + gx - 1, by + gy + n, rmp[3])
    # scuffed, lighter leather where hands hold it (outer edges, mid height)
    for gx, gy in ((2, 96), (3, 98), (2, 100), (w - 3, 96), (w - 3, 99)):
        c.p(bx + gx, by + gy, rmp[4])


def spine_ends(c, bx, by, w, h, rmp, band=None, depth=4):
    """The spine's head and tail standing proud of the boards (the book's back seen past the open pages)."""
    cx = bx + w // 2
    for sy, top in ((by - depth, True), (by + h, False)):
        c.fill(cx - 9, sy, cx + 9, sy + depth, rmp[0])
        c.fill(cx - 8, sy + (1 if top else 0), cx + 8, sy + depth - (0 if top else 1), rmp[2])
        c.hl(cx - 8, cx + 7, sy + (1 if top else 0), rmp[3])
        if band:
            for k, x in enumerate(range(cx - 7, cx + 7)):
                c.p(x, sy + (2 if top else 1), band[k % 2])


def journal(open_section, ahead):
    c = Cv(W, H)
    bx, by, w, h = 7, 8, 326, 198
    spine_ends(c, bx, by, w, h, LEATHER, band=(RIBBONS["fallen"][2], PAPER[3]))
    leather_cover(c, bx, by, w, h)
    stitches(c, bx + 3, by + 3, bx + w - 4, by + h - 4, PAPER[1], LEATHER[0])
    for x, y, k in ((bx, by, "tl"), (bx + w - 1, by, "tr"), (bx, by + h - 1, "bl"), (bx + w - 1, by + h - 1, "br")):
        brass_cap(c, x, y, k)
    c.art(bx + w - 8, by + h - 4, ["ab.", "bab"], {"a": VERDIGRIS[1], "b": VERDIGRIS[2]})   # verdigris on old brass
    c.art(bx + 4, by + 7, ["a.", "ba"], {"a": VERDIGRIS[0], "b": VERDIGRIS[1]})
    lp, rp, top, bot = bx + 11, bx + 315, by + 6, by + 187
    stack_edges(c, lp, top, bx + 163, bot, "lb")
    stack_edges(c, bx + 163, top, rp, bot, "rb")
    paper(c, lp, top, bx + 163, bot, "r", foxing=[(lp + 5, bot - 22, FOX[0]), (bx + 148, top + 4, FOX[1]),
                                                  (lp + 9, top + 7, FOX[3])])
    paper(c, bx + 163, top, rp, bot, "l", tile_off=(29, 17),
          foxing=[(rp - 14, bot - 34, FOX[2]), (rp - 10, top + 9, FOX[1])])
    left = [s for s in SECTIONS if s not in ahead and s != open_section]
    for i, s in enumerate(left):
        ribbon_tail(c, bx + 40 + i * 13, bot + 2, bot + 24 - i * 3, RIBBONS[s], w=6)
    for i, s in enumerate(ahead):
        ribbon_tail(c, bx + 246 + i * 13, bot + 2, bot + 25 - (i % 2) * 4, RIBBONS[s], w=6)
    if open_section:
        ribbon_tail(c, bx + 160, by - 3, bot + 32, RIBBONS[open_section], w=6)
        c.vl(bx + 159, top, bot - 1, PAPER[0])
    dog_ear(c, lp, bot, "l")
    dog_ear(c, rp, bot, "r")
    return c, (lp, top, 152), (bx + 163, top, 152)


def idea_journal():
    out = []
    c, (lx, ty, pw), (rx, _, _) = journal(None, SECTIONS)
    tw = caps_width("STAR ATLAS")
    draw_caps(c, lx + (pw - tw) // 2, ty + 12, "STAR ATLAS", INK[0])
    y = ty + 26
    c.hl(lx + 32, lx + 67, y, INK[1])
    c.hl(lx + 85, lx + 120, y, INK[1])
    c.art(lx + 72, y - 3, ["...a...", "..aba..", "aabbbaa", "..aba..", "...a..."], {"a": INK[1], "b": INK[0]})
    F.centred(c, lx, pw, ty + 32, f"Kept by {PLAYER}", INK[1])
    y = ty + 52
    for s in SECTIONS:
        a, b = STATE[s]
        if done(s):
            wax_seal(c, lx + 16, y + 4, 6)
        else:
            c.ring(lx + 16, y + 4, 4, 5, PENCIL)
        F.draw(c, lx + 26, y, LABEL[s], INK[0])
        ct = count_text(s)
        F.right(c, lx + pw - 12, y, ct, INK[0])
        dotted_leader(c, lx + 28 + F.width(LABEL[s]), lx + pw - 16 - F.width(ct), y + 6, INK[2])
        tally(c, lx + 27, y + 11, a, PENCIL, h=5)
        y += 25
    vignette(c, lx + 42, ty + 150, INK[2], PENCIL)
    F.centred(c, rx, pw, ty + 12, "Tonight", RED_INK)
    moon_phase(c, rx + pw // 2, ty + 38, 12, INK[0], INK[1])
    F.centred(c, rx, pw, ty + 56, "Night 31 of 48, half moon", INK[0])
    c.hl(rx + 44, rx + pw - 45, ty + 70, PENCIL)
    F.wrapped(c, rx + 12, pw - 24, ty + 78, TIPS, INK[1], 8)
    out.append(c)

    c, (lx, ty, pw), (rx, _, _) = journal("constellations", ["planets", "rare", "fallen"])
    gw, gh = 124, 84
    for side, x0 in ((0, lx + 12), (1, rx + 16)):
        for x in range(x0, x0 + gw + 1, 12):
            c.vl(x, ty + 24, ty + 24 + gh, PAPER[2])
        for yy in range(ty + 24, ty + 25 + gh, 12):
            c.hl(x0, x0 + gw, yy, PAPER[2])
    F.centred(c, lx, pw - 4, ty + 10, LASSO_NAME, INK[0])
    chart(c, lx + 12, ty + 24, gw, gh, LASSO, ink_dot(INK[0], INK[1]), INK[1])
    F.wrapped(c, lx + 8, pw - 20, ty + 116, LASSO_LEGEND, INK[0], 3)
    bw_ = 14 + 4 + F.width(FOUND_NOTE)
    sx = lx + (pw - 4 - bw_) // 2
    wax_seal(c, sx + 7, ty + 157, 7)
    F.draw(c, sx + 19, ty + 153, FOUND_NOTE, INK[1])
    F.centred(c, rx + 4, pw - 4, ty + 10, L["wildskies.atlas.unknown"], INK[2])
    chart(c, rx + 16, ty + 24, gw, gh, SHOE, ink_dot(INK[2], PENCIL), PENCIL, lines=False)
    F.wrapped(c, rx + 12, pw - 20, ty + 116, SHOE_HINT, INK[2], 3)
    out.append(c)
    return out


# ================================================================================================ 2. printed almanac
CLOTH = ramp((52, 18, 24), (78, 28, 34), (104, 40, 44), (132, 58, 58))


def cloth_cover(c, bx, by, w, h):
    c.fill(bx, by, bx + w, by + h, CLOTH[0])
    c.fill(bx + 1, by + 1, bx + w - 1, by + h - 1, CLOTH[2])
    c.hl(bx + 1, bx + w - 2, by + 1, CLOTH[3])
    c.vl(bx + 1, by + 1, by + h - 2, CLOTH[3])
    c.hl(bx + 2, bx + w - 2, by + h - 2, CLOTH[1])
    c.vl(bx + w - 2, by + 2, by + h - 2, CLOTH[1])
    for y in range(by + 3, by + h - 3):          # the weave: a sparse staggered lattice of 2-px dashes
        for x in range(bx + 3, bx + w - 4):
            if (x - bx) % 6 == (0 if (y - by) % 4 == 0 else 3) and (y - by) % 2 == 0:
                c.fill(x, y, x + 2, y + 1, CLOTH[1])
    # the gilt rule round the boards, with a corner fleuron
    gx0, gy0, gx1, gy1 = bx + 3, by + 3, bx + w - 4, by + h - 4
    for x in range(gx0, gx1 + 1):
        for yy in (gy0, gy1):
            c.p(x, yy, BRASS[3])
            c.p(x, yy + 1, CLOTH[0])
    for y in range(gy0, gy1 + 1):
        for xx in (gx0, gx1):
            c.p(xx, y, BRASS[3])
            c.p(xx + 1, y, CLOTH[0])
    fl = [".g.", "gwg", ".g."]
    for x, y in ((gx0 - 1, gy0 - 1), (gx1 - 1, gy0 - 1), (gx0 - 1, gy1 - 1), (gx1 - 1, gy1 - 1)):
        c.art(x, y, fl, {"g": BRASS[2], "w": BRASS[4]})


def gilt_star(c, x, y):
    c.art(x - 3, y - 3, ["...a...", "...b...", ".abcba.", "abcwcba", ".abcba.", "...b...", "...a..."],
          {"a": BRASS[1], "b": BRASS[2], "c": BRASS[3], "w": BRASS[4]})


def printed_page(c, x0, y0, pw, ph, head, folio, inner):
    # a double rule round the text block: heavy outside, fine inside
    bx0, by0, bx1, by1 = x0 + 7, y0 + 6, x0 + pw - 8, y0 + ph - 7
    if inner == "r":
        bx1 -= 3
    else:
        bx0 += 3
    for (a, b, cc, d), col in (((bx0, by0, bx1, by1), INK[0]), ((bx0 + 2, by0 + 2, bx1 - 2, by1 - 2), INK[1])):
        c.hl(a, cc, b, col)
        c.hl(a, cc, d, col)
        c.vl(a, b, d, col)
        c.vl(cc, b, d, col)
    if head:
        F.centred(c, bx0, bx1 - bx0 + 1, by0 + 5, head, RED_INK)
        c.hl(bx0 + 2, bx1 - 2, by0 + 15, INK[1])
    if folio:
        f = f"- {folio} -"
        F.centred(c, bx0, bx1 - bx0 + 1, by1 - 11, f, INK[1])
        c.hl(bx0 + 2, bx1 - 2, by1 - 14, INK[1])
        # the page turns on a printer's pointing hand in the outer corner of the foot
        hand = ["..aaaaaaa..", ".abbbbbbbaa", "abbbbbaaaa.", "abbbbbba...", ".abbbbba...", "..aaaaa...."]
        if inner == "r":
            hand = [r[::-1] for r in hand]
            c.art(bx0 + 4, by1 - 11, hand, {"a": INK[0], "b": PAPER[4]})
        else:
            c.art(bx1 - 14, by1 - 11, hand, {"a": INK[0], "b": PAPER[4]})
    return bx0, by0, bx1, by1


def volvelle(c, cx, cy, tonight=31):
    """A paper star wheel: the outer card printed with the 48 nights, the inner disc turned so its pointer stands on
    tonight, a window in it onto tonight's sky, a brass rivet through both."""
    R = 48
    c.disc(cx + 1, cy + 1, R, PAPER[1])                       # its shadow on the page
    c.disc(cx, cy, R, PAPER_OUT)
    c.disc(cx, cy, R - 1, PAPER[4])
    c.ring(cx, cy, R - 9, R - 8, INK[1])
    for k in range(48):
        a = math.radians(k * 7.5 - 90)
        r0 = R - 7 if k % 4 else R - 8
        for rr in range(r0, R - 2):
            c.p(int(math.floor(cx + math.cos(a) * (rr + 0.5))), int(math.floor(cy + math.sin(a) * (rr + 0.5))),
                INK[0] if k % 4 == 0 else INK[1])
    for n, (dx, dy) in ((12, (R - 16, 0)), (24, (0, R - 15)), (36, (-(R - 16), 0)), (48, (0, -(R - 15)))):
        s = str(n)
        F.draw(c, int(cx + dx - F.width(s) / 2 + 0.5), int(cy + dy - 4), s, RED_INK)
    # the inner disc, turned to tonight
    ang = math.radians((tonight - 1) * 7.5 - 90)
    r2 = R - 23
    c.disc(cx + 1, cy + 1, r2, PAPER[2])
    c.disc(cx, cy, r2, INK[1])
    c.disc(cx, cy, r2 - 1, PAPER[3])
    # the window: a wedge from r 9 to r2 - 3, 70 degrees wide, centred on the pointer
    for y in range(int(cy - r2), int(cy + r2) + 1):
        for x in range(int(cx - r2), int(cx + r2) + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            da = (math.atan2(dy, dx) - ang + math.pi) % (2 * math.pi) - math.pi
            if 7 < d < r2 - 3 and abs(da) < math.radians(40):
                edge = d > r2 - 4.2 or d < 8.2 or abs(da) > math.radians(35)
                c.p(x, y, INK[1] if edge else NIGHT[2] if d > 15 else NIGHT[3])
    for rr, aa, col in ((12, -20, STARLIGHT[2]), (16, 14, STARLIGHT[3]), (18, -6, STARLIGHT[1]), (10, 18, STARLIGHT[1]),
                        (17, -26, STARLIGHT[2]), (13, 2, STARLIGHT[1])):
        a = ang + math.radians(aa)
        c.p(int(math.floor(cx + math.cos(a) * rr)), int(math.floor(cy + math.sin(a) * rr)), col)
    # pointer, from the inner disc's rim out to the night ring
    for rr in range(r2 - 2, R - 8):
        c.p(int(math.floor(cx + math.cos(ang) * (rr + 0.5))), int(math.floor(cy + math.sin(ang) * (rr + 0.5))),
            RED_INK)
    lit_disc(c, cx, cy, 3.5, BRASS)
    c.p(int(cx) - 1, int(cy) - 1, BRASS[4])


def almanac_frame(spread):
    c = Cv(W, H)
    bx, by, w, h = 7, 22, 326, 196
    spine_ends(c, bx, by, w, h, CLOTH, band=(RIBBONS["fallen"][2], PAPER[4]), depth=3)
    cloth_cover(c, bx, by, w, h)
    lp, rp, top, bot = bx + 10, bx + 316, by + 7, by + 186
    stack_edges(c, lp, top, bx + 163, bot, "lb", n=2)
    stack_edges(c, bx + 163, top, rp, bot, "rb", n=2)
    paper(c, lp, top, bx + 163, bot, "r", foxing=[(lp + 5, bot - 12, FOX[1])])
    paper(c, bx + 163, top, rp, bot, "l", tile_off=(29, 17), foxing=[(rp - 9, top + 5, FOX[3])])
    # ribbons out of the head, lying on the table above the book; the open section's runs down the gutter
    xs = {"constellations": bx + 196, "planets": bx + 212, "rare": bx + 228, "fallen": bx + 244}
    for s in SECTIONS:
        if s == spread:
            continue
        x = xs[s] if spread is None or SECTIONS.index(s) > SECTIONS.index(spread) else bx + 80 + SECTIONS.index(s) * 16
        r = RIBBONS[s]
        y0 = by - 15 + (SECTIONS.index(s) % 2) * 3
        ribbon_tail(c, x, y0, top, r, w=5)
        c.p(x + 2, y0, CLEAR)              # swallow-tail at the far (top) end
        c.p(x + 1, y0, r[0]), c.p(x + 3, y0, r[0]), c.p(x + 2, y0 + 1, r[0])
    if spread:
        r = RIBBONS[spread]
        ribbon_tail(c, bx + 160, by - 15, bot + 1, r, w=5)
        c.p(bx + 162, by - 15, CLEAR)
        c.p(bx + 161, by - 15, r[0]), c.p(bx + 163, by - 15, r[0]), c.p(bx + 162, by - 14, r[0])
        c.vl(bx + 159, top, bot - 1, PAPER[0])
    return c, (lp, top, 153, 179), (bx + 163, top, 153, 179)


def idea_almanac():
    out = []
    c, (lx, ty, pw, ph), (rx, _, _, _) = almanac_frame(None)
    x0, y0, x1, y1 = printed_page(c, lx, ty, pw, ph, None, "i", "r")
    tw = caps_width("STAR ATLAS")
    draw_caps(c, x0 + (x1 - x0 + 1 - tw) // 2, y0 + 10, "STAR ATLAS", RED_INK)
    F.centred(c, x0, x1 - x0 + 1, y0 + 23, "& Almanac of the Night", INK[0])
    c.hl(x0 + 40, x1 - 40, y0 + 35, INK[1])
    c.art(x0 + (x1 - x0) // 2 - 2, y0 + 33, ["..a..", "aabaa", "..a.."], {"a": INK[1], "b": RED_INK})
    F.centred(c, x0, x1 - x0 + 1, y0 + 40, f"Kept by {PLAYER}", INK[1])
    y = y0 + 62
    for i, s in enumerate(SECTIONS):
        num = ["I", "II", "III", "IV"][i]
        F.right(c, x0 + 25, y, num, RED_INK)
        F.draw(c, x0 + 28, y, LABEL[s], INK[0])
        ct = count_text(s)
        F.right(c, x1 - 5, y, ct, INK[0])
        dotted_leader(c, x0 + 30 + F.width(LABEL[s]), x1 - 9 - F.width(ct), y + 6, INK[2], step=2)
        if done(s):
            gilt_star(c, x0 + 6, y + 3)
        y += 18
    F.centred(c, x0, x1 - x0 + 1, y + 6, "Printed for the Frontier", INK[2])
    x0, y0, x1, y1 = printed_page(c, rx, ty, pw, ph, "TONIGHT", "ii", "l")
    cx = (x0 + x1 + 1) // 2
    volvelle(c, cx, y0 + 70)
    F.centred(c, x0, x1 - x0 + 1, y0 + 123, "Night 31 of 48", INK[0])
    F.centred(c, x0, x1 - x0 + 1, y0 + 134, "half moon", RED_INK)
    out.append(c)

    c, (lx, ty, pw, ph), (rx, _, _, _) = almanac_frame("constellations")
    for side, (px, con, found) in enumerate(((lx, LASSO, True), (rx, SHOE, False))):
        x0, y0, x1, y1 = printed_page(c, px, ty, pw, ph, "CONSTELLATIONS", str(3 + side), "r" if side == 0 else "l")
        cx = (x0 + x1 + 1) // 2
        name = (LASSO_NAME if found else L["wildskies.atlas.unknown"]).upper()
        F.centred(c, x0, x1 - x0 + 1, y0 + 20, name, INK[0] if found else INK[2])
        if found:
            gilt_star(c, x0 + (x1 - x0 + 1 - F.width(name)) // 2 - 7, y0 + 23)
        pcy = y0 + 68
        c.ring(cx, pcy, 37, 38, INK[0])
        c.ring(cx, pcy, 32, 33, INK[1])
        for k in range(36):
            a = math.radians(k * 10)
            for rr in ((33.5, 35.5) if k % 3 else (33.5, 37.5)):
                c.p(int(math.floor(cx + math.cos(a) * rr)), int(math.floor(pcy + math.sin(a) * rr)), INK[1])
        star = print_star(INK[0] if found else INK[2])
        chart(c, cx - 33, pcy - 33, 66, 66, con, star, INK[1], gap=4, lines=found, margin=22)
        if found:
            F.wrapped(c, x0 + 6, x1 - x0 - 11, y0 + 111, LASSO_LEGEND, INK[0], 3)
            F.centred(c, x0, x1 - x0 + 1, y0 + 142, "Found " + FOUND_NOTE.lower(), RED_INK)
        else:
            F.wrapped(c, x0 + 6, x1 - x0 - 11, y0 + 111, SHOE_HINT, INK[2], 3)
    out.append(c)
    return out


# ================================================================================================ 3. cyanotype ledger
RULE = rgb((150, 168, 176))            # the ledger's blue rules (a cold line on warm paper)
MARGIN = rgb((190, 112, 96))           # its red margin
CYAN = ramp((14, 30, 66), (22, 48, 100), (40, 76, 136), (150, 184, 218), (222, 236, 248))


def walnut_board(c, x0, y0, x1, y1):
    c.fill(x0, y0, x1, y1, WALNUT[0])
    c.fill(x0 + 1, y0 + 1, x1 - 1, y1 - 1, WALNUT[2])
    c.hl(x0 + 1, x1 - 2, y0 + 1, WALNUT[4])
    c.vl(x0 + 1, y0 + 1, y1 - 2, WALNUT[3])
    c.hl(x0 + 2, x1 - 2, y1 - 2, WALNUT[1])
    c.vl(x1 - 2, y0 + 2, y1 - 2, WALNUT[1])
    # grain: long dashes running along the board, hand-placed starts per row, repeating every 70 px
    starts = [(3, 9, 2), (14, 22, 1), (31, 12, 3), (47, 16, 1), (58, 8, 3)]
    for y in range(y0 + 3, y1 - 3, 2):
        k = (y - y0) // 2
        for base in range(x0 - 70, x1, 70):
            s, n, t = starts[k % len(starts)]
            a = base + s + (k * 13) % 70
            for x in range(max(a, x0 + 3), min(a + n, x1 - 3)):
                c.p(x, y, WALNUT[t if t < 3 else 3])


def corner_plate(c, x, y):
    c.fill(x, y, x + 9, y + 9, BRASS[0])
    c.fill(x + 1, y + 1, x + 8, y + 8, BRASS[2])
    c.hl(x + 1, x + 7, y + 1, BRASS[3])
    c.vl(x + 1, y + 1, y + 7, BRASS[3])
    c.hl(x + 2, x + 7, y + 7, BRASS[1])
    c.vl(x + 7, y + 2, y + 7, BRASS[1])
    rivet(c, x + 3, y + 3)


def ledger_frame(spread):
    c = Cv(W, H)
    bx, by, w, h = 4, 8, 318, 196
    walnut_board(c, bx, by, bx + 160, by + h)
    walnut_board(c, bx + 158, by, bx + w, by + h)
    for x, y in ((bx + 2, by + 2), (bx + w - 11, by + 2), (bx + 2, by + h - 11), (bx + w - 11, by + h - 11)):
        corner_plate(c, x, y)
    # the strap and clasp, lying open on the right
    sy = by + 86
    c.fill(bx + w - 3, sy, bx + w + 14, sy + 10, LEATHER[0])
    c.fill(bx + w - 3, sy + 1, bx + w + 13, sy + 9, LEATHER[2])
    c.hl(bx + w - 3, bx + w + 12, sy + 1, LEATHER[3])
    c.hl(bx + w - 3, bx + w + 12, sy + 8, LEATHER[1])
    c.fill(bx + w + 5, sy - 2, bx + w + 12, sy + 12, BRASS[0])
    c.fill(bx + w + 6, sy - 1, bx + w + 11, sy + 11, BRASS[2])
    c.vl(bx + w + 6, sy - 1, sy + 10, BRASS[3])
    c.fill(bx + w + 8, sy + 2, bx + w + 10, sy + 8, LEATHER[0])
    c.vl(bx + w + 8, sy + 2, sy + 7, LEATHER[1])
    for k in range(3):
        c.p(bx + w + 1 + k * 0, sy + 3 + k * 2, LEATHER[0])
    lp, rp, top, bot = bx + 9, bx + w - 9, by + 6, by + 186
    stack_edges(c, lp, top, bx + 160, bot, "lb")
    stack_edges(c, bx + 160, top, rp, bot, "rb")
    for x0, x1, inner, off in ((lp, bx + 160, "r", (0, 0)), (bx + 160, rp, "l", (29, 17))):
        paper(c, x0, top, x1, bot, inner, tile_off=off)
        for y in range(top + 25, bot - 3, 10):
            c.hl(x0 + (1 if inner == "r" else 7), x1 - (7 if inner == "r" else 2), y, RULE)
        m = x0 + 16 if inner == "r" else x0 + 20
        c.vl(m, top + 1, bot - 2, MARGIN)
        c.vl(m + 2, top + 1, bot - 2, MARGIN)
        c.hl(x0 + 1, x1 - 2, top + 21, MARGIN) if False else None
    # the brass hinge at head and tail of the spine
    for hy in (by + 1, by + h - 5):
        for k, x in enumerate(range(bx + 150, bx + 168, 3)):
            col = BRASS[2] if k % 2 == 0 else BRASS[1]
            c.fill(x, hy, x + 3, hy + 4, BRASS[0])
            c.fill(x, hy + 1, x + 3, hy + 3, col)
            c.hl(x, x + 2, hy + 1, BRASS[3] if k % 2 == 0 else BRASS[2])
    # ribbons with brass tips, out of the bottom
    order = SECTIONS
    for i, s in enumerate(order):
        if s == spread:
            continue
        right = spread is None or SECTIONS.index(s) > SECTIONS.index(spread)
        x = (bx + 238 + i * 12) if right else (bx + 44 + i * 12)
        y1 = bot + 21 - (i % 2) * 4
        ribbon_tail(c, x, bot + 1, y1 - 3, RIBBONS[s], w=5, fork=False)
        c.fill(x, y1 - 3, x + 5, y1 + 1, BRASS[0])
        c.fill(x + 1, y1 - 3, x + 4, y1, BRASS[2])
        c.p(x + 1, y1 - 3, BRASS[4])
    if spread:
        s = spread
        x, y1 = bx + 157, bot + 26
        ribbon_tail(c, x, by - 1, y1 - 3, RIBBONS[s], w=5, fork=False)
        c.fill(x, y1 - 3, x + 5, y1 + 1, BRASS[0])
        c.fill(x + 1, y1 - 3, x + 4, y1, BRASS[2])
        c.p(x + 1, y1 - 3, BRASS[4])
        c.vl(x - 1, top, bot - 1, PAPER[0])
    dog_ear(c, lp, bot, "l", arrow_col=RED_INK)
    dog_ear(c, rp, bot, "r", arrow_col=RED_INK)
    return c, (lp, top, 151), (bx + 160, top, 151)


def photo_corners(c, x0, y0, x1, y1, col, edge, n=6):
    for (cx, cy, fx, fy) in ((x0 - 2, y0 - 2, 1, 1), (x1 + 1, y0 - 2, -1, 1), (x0 - 2, y1 + 1, 1, -1),
                             (x1 + 1, y1 + 1, -1, -1)):
        for j in range(n):
            for i in range(n - j):
                c.p(cx + fx * i, cy + fy * j, edge if i + j == n - 1 or i == 0 or j == 0 else col)


def cyanotype(c, x0, y0, w, h, con):
    """A blueprint print pasted in: a pale card, the blue brushed on with a ragged edge, the stars left white."""
    c.fill(x0, y0, x0 + w, y0 + h, PAPER[4])
    c.hl(x0, x0 + w - 1, y0 + h - 1, PAPER[2])
    c.vl(x0 + w - 1, y0, y0 + h - 1, PAPER[2])
    ix0, iy0, ix1, iy1 = x0 + 4, y0 + 4, x0 + w - 4, y0 + h - 4
    c.fill(ix0, iy0, ix1, iy1, CYAN[1])
    # brush edge: bites out of the blue and overruns into the card, hand-placed
    for x, y, col in ((ix0 + 9, iy0, PAPER[4]), (ix0 + 10, iy0, PAPER[4]), (ix0 + 30, iy0 - 1, CYAN[1]),
                      (ix0 + 31, iy0 - 1, CYAN[1]), (ix0 + 32, iy0 - 1, CYAN[1]), (ix1 - 20, iy0, PAPER[4]),
                      (ix1 - 1, iy0 + 12, PAPER[4]), (ix1, iy0 + 30, CYAN[1]), (ix1, iy0 + 31, CYAN[1]),
                      (ix1 - 1, iy1 - 9, PAPER[4]), (ix0 + 50, iy1, CYAN[1]), (ix0 + 51, iy1, CYAN[1]),
                      (ix0 + 18, iy1 - 1, PAPER[4]), (ix0, iy0 + 20, PAPER[4]), (ix0 - 1, iy0 + 40, CYAN[1]),
                      (ix0 - 1, iy0 + 41, CYAN[1]), (ix1 - 40, iy1, CYAN[1])):
        c.p(x, y, col)
    # deeper blue where the brush went twice, along the edges
    for x, y, n in ((ix0 + 2, iy0 + 2, 14), (ix1 - 26, iy1 - 3, 20), (ix0 + 40, iy0 + 1, 18)):
        c.hl(x, x + n, y, CYAN[0])
    for x, y, n in ((ix0 + 1, iy0 + 8, 10), (ix1 - 2, iy0 + 40, 12)):
        c.vl(x, y, y + n, CYAN[0])

    def star(cc, x, y, m):
        if m <= 1:
            cc.art(x - 2, y - 2, [".ddd.", "dwwwd", "dwwwd", "dwwwd", ".ddd."], {"w": CYAN[4], "d": CYAN[3]})
        elif m == 2:
            cc.art(x - 1, y - 1, ["dwd", "www", "dwd"], {"w": CYAN[4], "d": CYAN[3]})
        else:
            cc.art(x - 1, y - 1, [".d.", "dwd", ".d."], {"w": CYAN[4], "d": CYAN[2]})
    chart(c, ix0, iy0, ix1 - ix0, iy1 - iy0, con, star, CYAN[3], gap=4)


def rubber_stamp(c, x, y, word, col, worn=()):
    w = F.width(word) + 7
    for yy in (y, y + 1, y + 13, y + 14):
        c.hl(x, x + w - 1, yy, col)
    for xx in (x, x + 1, x + w - 2, x + w - 1):
        c.vl(xx, y, y + 14, col)
    F.draw(c, x + 4, y + 4, word, col)
    for px, py in worn:
        c.p(x + px, y + py, CLEAR) if False else c.p(x + px, y + py, PAPER[3])
    return w


def idea_ledger():
    out = []
    c, (lx, ty, pw), (rx, _, _) = ledger_frame(None)
    tw = caps_width("STAR ATLAS")
    draw_caps(c, lx + 20 + (pw - 24 - tw) // 2, ty + 7, "STAR ATLAS", INK[0])
    F.draw(c, lx + 21, ty + 37, f"Kept by {PLAYER}", INK[1])
    F.right(c, lx + pw - 8, ty + 37, "Vol. I", INK[1])
    F.draw(c, lx + 21, ty + 57, "Section", RED_INK)
    F.right(c, lx + pw - 8, ty + 57, "Found", RED_INK)
    y = ty + 67
    for s in SECTIONS:
        F.draw(c, lx + 21, y, LABEL[s], INK[0])
        F.right(c, lx + pw - 8, y, count_text(s, " of "), INK[0])
        if done(s):
            c.art(lx + 7, y + 1, ["....a", "...a.", "a.a..", ".a..."], {"a": RED_INK})
        y += 10
        tally(c, lx + 22, y + 2, STATE[s][0], PENCIL, h=6)
        y += 10
    F.draw(c, rx + 25, ty + 17, "Tonight", RED_INK)
    F.right(c, rx + pw - 8, ty + 17, "half moon", INK[1])
    F.draw(c, rx + 25, ty + 37, "Night 31 of 48", INK[0])
    lines = F.split(TIPS, pw - 34)
    for i, l in enumerate(lines):
        F.draw(c, rx + 25, ty + 67 + i * 10, l, INK[1])
    out.append(c)

    c, (lx, ty, pw), (rx, _, _) = ledger_frame("constellations")
    F.draw(c, lx + 21, ty + 17, LASSO_NAME, INK[0])
    F.right(c, lx + pw - 8, ty + 17, "No. 1", INK[2])
    px, py, pw_, ph_ = lx + 24, ty + 28, 112, 76
    cyanotype(c, px, py, pw_, ph_, LASSO)
    photo_corners(c, px, py, px + pw_ - 1, py + ph_ - 1, INK[1], INK[0])
    lines = F.split(LASSO_LEGEND, pw - 30)
    for i, l in enumerate(lines[:3]):
        F.draw(c, lx + 21, ty + 117 + i * 10, l, INK[0])
    F.draw(c, lx + 21, ty + 147, FOUND_NOTE, INK[1])
    rubber_stamp(c, lx + pw - 46, ty + 157, "FOUND", RED_INK, worn=((5, 0), (6, 0), (20, 14), (0, 9), (33, 1)))
    F.draw(c, rx + 25, ty + 17, L["wildskies.atlas.unknown"], INK[2])
    F.right(c, rx + pw - 8, ty + 17, "No. 2", INK[2])
    px = rx + 30
    photo_corners(c, px, py, px + pw_ - 1, py + ph_ - 1, PAPER[1], PAPER_OUT)
    chart(c, px + 4, py + 4, pw_ - 8, ph_ - 8, SHOE, ink_dot(PENCIL, PAPER[1]), PENCIL, lines=False)
    lines = F.split(SHOE_HINT, pw - 30)
    for i, l in enumerate(lines[:3]):
        F.draw(c, rx + 25, ty + 117 + i * 10, l, INK[2])
    out.append(c)
    return out


# ================================================================================================ 4. saddlebag journal
HIDE = ramp((92, 56, 32), (128, 84, 48), (160, 112, 68), (190, 144, 96), (214, 176, 128))
SEPIA = ramp((164, 132, 88), (190, 160, 112), (210, 184, 136), (226, 206, 162), (238, 224, 186))
SEPIA_OUT = rgb((112, 80, 50))
BROWN_INK = ramp((58, 34, 22), (92, 60, 40), (132, 100, 72))
BRAND = rgb((150, 52, 30))
BONE = ramp((150, 130, 100), (196, 180, 150), (228, 218, 196), (246, 240, 226))


def hide_cover(c, bx, by, w, h):
    """A soft buckskin wrap: an uneven cut edge (notches and bumps placed by hand), wrinkles with a lit lip."""
    c.fill(bx, by, bx + w, by + h, HIDE[0])
    c.fill(bx + 1, by + 1, bx + w - 1, by + h - 1, HIDE[2])
    c.hl(bx + 1, bx + w - 2, by + 1, HIDE[3])
    c.vl(bx + 1, by + 1, by + h - 2, HIDE[3])
    c.hl(bx + 2, bx + w - 2, by + h - 2, HIDE[1])
    c.vl(bx + w - 2, by + 2, by + h - 2, HIDE[1])
    # rounded corners
    for x, y in ((bx, by), (bx + 1, by), (bx, by + 1), (bx + w - 1, by), (bx + w - 2, by), (bx + w - 1, by + 1),
                 (bx, by + h - 1), (bx + 1, by + h - 1), (bx, by + h - 2), (bx + w - 1, by + h - 1),
                 (bx + w - 2, by + h - 1), (bx + w - 1, by + h - 2)):
        c.p(x, y, CLEAR)
    for x, y in ((bx + 1, by + 1), (bx + w - 2, by + 1), (bx + 1, by + h - 2), (bx + w - 2, by + h - 2)):
        c.p(x, y, HIDE[0])
    # notches in the cut edge
    for x, y in ((bx + 60, by), (bx + 61, by), (bx + 212, by), (bx + w - 1, by + 70), (bx + w - 1, by + 71),
                 (bx + 130, by + h - 1), (bx, by + 120), (bx + 270, by + h - 1), (bx + 271, by + h - 1)):
        c.p(x, y, CLEAR)
        c.p(x + (1 if x == bx else -1 if x == bx + w - 1 else 0), y + (1 if y == by else -1 if y == by + h - 1 else 0),
            HIDE[0])
    for gx, gy, n in ((20, 3, 5), (90, 4, 4), (176, 3, 6), (250, 4, 4), (300, 3, 3), (40, h - 4, 5), (120, h - 5, 4),
                      (200, h - 4, 6), (284, h - 5, 4)):
        c.fill(bx + gx, by + gy, bx + gx + n, by + gy + 1, HIDE[1])
        c.p(bx + gx + n, by + gy - 1, HIDE[4])
        c.p(bx + gx - 1, by + gy + 1, HIDE[1])
    for gx, gy, n in ((3, 30, 5), (4, 100, 4), (3, 160, 6), (w - 4, 40, 4), (w - 5, 140, 5)):
        c.fill(bx + gx, by + gy, bx + gx + 1, by + gy + n, HIDE[1])
        c.p(bx + gx - 1, by + gy, HIDE[4])


FRINGE = [7, 9, 8, 10, 7, 9, 11, 8, 9, 7, 10, 8]


def fringe(c, x0, x1, y, skip):
    """Buckskin fringe hanging off the bottom edge: 2-px strands every 3 px, lit left, lengths from a hand-picked
    list, each cut to a point."""
    k = 0
    for x in range(x0, x1 - 1, 3):
        if skip[0] <= x <= skip[1]:
            continue
        n = FRINGE[k % len(FRINGE)]
        k += 1
        c.vl(x, y, y + n - 1, HIDE[3])
        c.vl(x + 1, y, y + n - 2, HIDE[1])
        c.p(x, y + n - 1, HIDE[2])
        c.p(x + 1, y, HIDE[2])


def saddlebag_frame(spread):
    c = Cv(W, H)
    bx, by, w, h = 6, 18, 322, 198
    fringe(c, bx + 6, bx + w - 6, by + h - 1, (bx + w // 2 - 12, bx + w // 2 + 10))
    hide_cover(c, bx, by, w, h)
    # the lace: from under the back board, out to the right, wound once, a bone toggle and a brass bead
    ly = by + 96
    for x in range(bx + w - 4, bx + w + 6):
        c.p(x, ly, LEATHER[0]), c.p(x, ly + 1, LEATHER[2])
    c.art(bx + w + 2, ly - 6, ["..bbb..", ".b...b.", "b.....b", "b......", "b......", ".b.....", "..b...."],
          {"b": LEATHER[1]})
    c.art(bx + w + 4, ly + 2, ["k", "k", "k", "k", "k"], {"k": LEATHER[1]})
    c.art(bx + w + 2, ly + 7, [".aaa.", "abbba", ".aaa."], {"a": BRASS[0], "b": BRASS[3]})
    c.art(bx + w + 1, ly + 10, [".ooooo.", "obbbbbo", "owwwbbo", ".ooooo."],
          {"o": BONE[0], "b": BONE[2], "w": BONE[3]})
    lp, rp, top, bot = bx + 8, bx + w - 8, by + 7, by + 188
    for x0, x1, inner, off, fox in ((lp, bx + 161, "r", (0, 0), [(lp + 6, top + 120, FOX[2])]),
                                    (bx + 161, rp, "l", (29, 17), [(rp - 12, top + 8, FOX[0])])):
        c.fill(x0 - (2 if inner == "r" else 0), top + 2, x1 + (2 if inner == "l" else 0), bot + 2, SEPIA_OUT)
        paper(c, x0, top, x1, bot, inner, rmp=SEPIA, tile_off=off, foxing=fox)
    # deckle: bites out of the outer and bottom edges
    for x, y in [(lp, top + 30), (lp, top + 31), (lp, top + 80), (lp, top + 140), (lp, top + 141), (lp + 40, bot - 1),
                 (lp + 41, bot - 1), (lp + 100, bot - 1), (rp - 1, top + 50), (rp - 1, top + 51), (rp - 1, top + 120),
                 (bx + 200, bot - 1), (bx + 260, bot - 1), (bx + 261, bot - 1), (bx + 80, top), (bx + 230, top),
                 (bx + 231, top)]:
        c.p(x, y, SEPIA_OUT)
    # long-stitch through the spine: thread crossing the fold at five stations
    for sy in (top + 14, top + 52, top + 90, top + 128, top + 166):
        c.fill(bx + 159, sy, bx + 163, sy + 1, BONE[2])
        c.fill(bx + 159, sy + 1, bx + 163, sy + 2, BONE[0])
        c.p(bx + 158, sy, SEPIA_OUT), c.p(bx + 163, sy, SEPIA_OUT)
    # cotton ribbons out of the head, knotted, frayed at the far end
    for i, s_ in enumerate(SECTIONS):
        if s_ == spread:
            continue
        right = spread is None or SECTIONS.index(s_) > SECTIONS.index(spread)
        x = (bx + 200 + i * 12) if right else (bx + 60 + i * 12)
        r = RIBBONS[s_]
        y0 = by - 14 + (i % 2) * 4
        ribbon_tail(c, x, y0, top, r, w=4, fork=False)
        c.fill(x - 1, y0 + 5, x + 5, y0 + 7, r[0])     # a knot
        c.fill(x, y0 + 5, x + 4, y0 + 6, r[2])
        c.fill(x, y0, x + 4, y0 + 1, CLEAR)            # the frayed end
        c.p(x, y0, r[1]), c.p(x + 2, y0, r[2]), c.p(x + 1, y0 - 1, r[1])
    if spread:
        r = RIBBONS[spread]
        x = bx + 159
        ribbon_tail(c, x, by - 15, bot, r, w=4, fork=False)
        c.fill(x - 1, by - 10, x + 5, by - 8, r[0])
        c.fill(x, by - 10, x + 4, by - 9, r[2])
        c.fill(x, by - 15, x + 4, by - 14, CLEAR)
        c.p(x + 1, by - 15, r[1]), c.p(x + 3, by - 16, r[2])
    dog_ear(c, lp, bot, "l", rmp=SEPIA, arrow_col=BROWN_INK[1])
    dog_ear(c, rp, bot, "r", rmp=SEPIA, arrow_col=BROWN_INK[1])
    return c, (lp, top, 153), (bx + 161, top, 153)


def brand(c, cx, cy, col):
    """The Circle Star: a rancher's brand, stamped in red-brown ink; a little worn."""
    c.ring(cx, cy, 6, 8, col)
    c.art(cx - 4, cy - 4, ["....a....", "....a....", "...aaa...", "aaaaaaaaa", ".aaaaaaa.", "..aaaaa..",
                           "..aa.aa..", ".aa...aa.", "........."], {"a": col})
    for x, y in ((cx + 7, cy - 2), (cx - 3, cy + 7), (cx - 7, cy - 3)):
        c.p(x, y, SEPIA[3])


def compass_rose(c, x, y, col, soft):
    """A hand-drawn compass rose, 13 x 13, north inked, the other points in a lighter ink; N above it."""
    c.art(x, y, ["......c......", "......c......", ".....ccc.....", ".....ccc.....", "..s..csc..s..",
                 "...s.csc.s...", "sssssc.cssss.", "...s.sss.s...", "..s..sss..s..", ".....sss.....",
                 ".....sss.....", "......s......", "......s......"], {"c": col, "s": soft})
    F.draw(c, x + 4, y - 10, "N", col)


def coffee_ring(c, cx, cy, r):
    for k in range(64):
        a = math.radians(k * 360 / 64)
        if 200 < k * 360 / 64 < 250:
            continue
        x, y = int(math.floor(cx + math.cos(a) * r)), int(math.floor(cy + math.sin(a) * r))
        c.p(x, y, SEPIA[1])
        if 20 < k * 360 / 64 < 120:
            c.p(x, y + 1, SEPIA[0])


def idea_saddlebag():
    out = []
    ink, ink1, ink2 = BROWN_INK
    c, (lx, ty, pw), (rx, _, _) = saddlebag_frame(None)
    tw = caps_width("STAR ATLAS")
    tx = lx + (pw - tw) // 2
    draw_caps(c, tx, ty + 12, "STAR ATLAS", ink)
    # a lasso flourish under the title: the rope runs out and ends in its loop
    c.hl(tx + 2, tx + tw + 2, ty + 25, ink1)
    c.ring(tx + tw + 7, ty + 23, 4, 5, ink1)
    F.centred(c, lx, pw, ty + 32, f"Kept by {PLAYER}", ink1)
    y = ty + 54
    icons = {
        "constellations": [".a...a.", "..a.a..", "...a...", "..a.a..", ".a...a."],
        "planets": ["..aaa..", ".a...a.", "aaaaaaa", ".a...a.", "..aaa.."],
        "rare": ["a......", ".a.....", "..aa...", "...aaa.", "...aaa."],
        "fallen": ["...a...", "..aaa..", "aaaaaaa", "..a.a..", ".a...a."],
    }
    for s in SECTIONS:
        c.art(lx + 12, y + 1, icons[s], {"a": ink1})
        F.draw(c, lx + 24, y, LABEL[s], ink)
        a, b = STATE[s]
        ct = f"{a} of {b}" if b else str(a)
        F.right(c, lx + pw - 12, y, ct, ink)
        if done(s):
            brand(c, lx + pw - 12 - F.width(ct) - 13, y + 3, BRAND)
        y += 22
    compass_rose(c, lx + (pw - 13) // 2, ty + 148, ink1, ink2)
    F.centred(c, rx, pw, ty + 12, "The night of", ink1)
    # the moon's eight faces in a row, tonight's ringed
    for k in range(8):
        mx = rx + 22 + k * 15
        c.ring(mx, ty + 34, 4, 5, ink1)
        if k == 2:
            c.ring(mx, ty + 34, 6, 7, BRAND)
        for yy in range(ty + 30, ty + 39):
            for xx in range(mx - 4, mx + 5):
                dx = xx + 0.5 - mx
                if math.hypot(dx, yy + 0.5 - ty - 34) < 3.6 and ((k < 4 and dx < 2.2 - k * 1.6) or
                                                                   (k >= 4 and dx > -2.2 + (k - 4) * 1.6)):
                    c.p(xx, yy, ink2)
    F.centred(c, rx, pw, ty + 46, "Night 31 of 48, half moon", ink)
    F.wrapped(c, rx + 12, pw - 24, ty + 66, TIPS, ink1, 8)
    coffee_ring(c, rx + 118, ty + 158, 13)
    out.append(c)

    c, (lx, ty, pw), (rx, _, _) = saddlebag_frame("constellations")
    F.centred(c, lx, pw - 4, ty + 10, LASSO_NAME, ink)
    chart(c, lx + 14, ty + 24, 122, 84, LASSO, hand_star(ink, ink2), ink1, gap=3)
    compass_rose(c, lx + 10, ty + 30, ink1, ink2)
    F.wrapped(c, lx + 8, pw - 20, ty + 114, LASSO_LEGEND, ink, 3)
    bw_ = 18 + 4 + F.width(FOUND_NOTE)
    sx = lx + (pw - 4 - bw_) // 2
    brand(c, sx + 8, ty + 156, BRAND)
    F.draw(c, sx + 21, ty + 152, FOUND_NOTE, ink1)
    F.centred(c, rx + 4, pw - 4, ty + 10, L["wildskies.atlas.unknown"], ink2)
    chart(c, rx + 18, ty + 24, 122, 84, SHOE, hand_star(ink2, SEPIA[1]), ink2, lines=False)
    c.art(rx + 76, ty + 50, [".aaa.", "a...a", "....a", "...a.", "..a..", "..a..", ".....", "..a.."], {"a": ink2})
    F.wrapped(c, rx + 12, pw - 20, ty + 114, SHOE_HINT, ink2, 3)
    coffee_ring(c, rx + 40, ty + 150, 12)
    out.append(c)
    return out


IDEAS = [("journal", "Field journal", idea_journal), ("almanac", "Printed almanac", idea_almanac),
         ("ledger", "Cyanotype ledger", idea_ledger), ("saddlebag", "Saddlebag journal", idea_saddlebag)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]
    for n, (key, title, fn) in enumerate(IDEAS, 1):
        if only and key not in only:
            continue
        for i, s in enumerate(fn()):
            s.save(str(OUT / f"book_{n}_{key}_{i}.png"))
        print("painted", n, key)


if __name__ == "__main__":
    main()
