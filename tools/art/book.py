"""The Star Atlas, painted: the saddlebag journal (the owner's pick, 2026-11-12) with the ledger draft's pasted-in
pictures.

Concept: the field journal of someone who reads the sky out on the frontier, carried in a saddlebag. A soft buckskin
wrap, whipstitched round the edge with a lace, fringe along the foot, a closing flap on the back board with a lace
and a bone toggle. Inside, sepia pages sewn through the spine with a long-stitch, curving down into the gutter over a
thick page block, deckled at the fore-edge. Everything is written in brown iron-gall ink. What's been seen is pasted
in: cyanotype prints of the constellations and photo plates of the planets, held by leather photo corners (the cold
sky on the warm page); what hasn't is a pencil sketch inside empty corners. Finds are marked with a rancher's brand
(the Circle Star) in red-brown; fallen stars earn tin-star badges pinned to the page; dug-up stars go in a claims
ledger. Knotted cotton ribbons mark the sections; the bottom corners curl up to turn the page.

    python tools/art/book.py      -> previews/book/spread_<name>.png (mockups of the real layout at 1:1)

Mockups only for now: the Java has not been touched. The book is built from parts that become textures later (the
base spread, ribbons, curls, prints' frames, badges, stamps); the text is the game's own font at its real widths.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from PIL import Image  # noqa: E402
from artlib import (Cv, rgb, CLEAR, LEATHER, BRASS, PAPER, NIGHT, STARLIGHT, RIBBONS, SECTIONS, ramp, font,  # noqa: E402
                    catalog, lang, chart_points, line_gapped, lit_disc, caps_width, draw_caps)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "previews/book"
F = font()
CAT = catalog()
L = lang()
CON = {c["id"]: c for c in CAT["constellations"]}

# ------------------------------------------------------------------------------------------------ this book's ramps
HIDE = ramp((84, 50, 30), (122, 80, 46), (156, 110, 66), (186, 142, 94), (212, 174, 126))
HIDE_EDGE = rgb((62, 34, 20))                   # the wrap's cut edge, its darkest
SEPIA = ramp((160, 128, 86), (188, 158, 110), (208, 182, 134), (224, 204, 160), (236, 222, 184))
SEPIA_OUT = rgb((110, 78, 48))
INKB = ramp((54, 32, 22), (90, 58, 38), (130, 98, 70))   # brown ink: text, notes, faded notes
PENCILB = rgb((150, 128, 100))
BRAND = rgb((148, 50, 30))
BONE = ramp((140, 120, 92), (190, 174, 144), (224, 214, 190), (244, 238, 222))
LACE = ramp((50, 24, 14), (88, 46, 26), (128, 74, 44), (160, 104, 66))
CYAN = ramp((14, 30, 66), (22, 48, 100), (40, 76, 136), (150, 184, 218), (222, 236, 248))
TIN = ramp((60, 40, 14), (112, 80, 28), (166, 124, 48), (210, 170, 80), (242, 218, 146))   # a brass badge

# ------------------------------------------------------------------------------------------------ the layout
W, H = 344, 236
BX, BY, BW, BH = 4, 18, 320, 194                 # the open wrap (boards)
GX = BX + 160                                    # the gutter: left page ends here, right page starts here
LP, RP = BX + 10, BX + 310                       # pages' outer edges (RP exclusive)
TOP, BOT = BY + 7, BY + 185                      # pages' top and bottom (BOT exclusive)
PW = 150
DIVE = [6, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1]         # how far a page's edge dives into the gutter, by distance
ARCH = 2                                         # how far the middle of a page arches above its outer corner
CONTENT = 132                                    # text width on a page
LX, RX = LP + 9, GX + 9                          # content left edges (right page clears its gutter)

PLAYER = "Steve"
STATE = {"constellations": (5, 24), "planets": (5, 6), "rare": (1, 7), "fallen": (3, None)}
LABEL = {"constellations": L["wildskies.atlas.constellations"], "planets": L["wildskies.atlas.planets"],
         "rare": L["wildskies.atlas.rare"], "fallen": L["wildskies.atlas.fallen"]}


def dip(d):
    """A page's edge, inset from the block's rectangle at distance d from the gutter: deep where the page dives
    into the spine, ARCH less in the middle of the page where it arches up, ARCH at the fore-edge corner."""
    dive = DIVE[d] if d < len(DIVE) else 0
    arch = int(math.floor(ARCH * math.sin(math.pi * min(d, PW) / PW) + 0.5))
    return ARCH + dive - arch


def col_d(x):
    """Distance of column x from the gutter, and which page it is on."""
    return (GX - 1 - x, "l") if x < GX else (x - GX, "r")


def page_top(x):
    return TOP - ARCH + dip(col_d(x)[0])


def page_bot(x):
    return BOT + ARCH - dip(col_d(x)[0])


def best_night(h):
    return int(math.floor(((-h / 360.0 - 0.5) % 1.0) * 48)) % 48 + 1


# ================================================================================================ the wrap
def whipstitch(c, x0, y0, x1, y1):
    """A lace whipstitched over the cut edge: short diagonal laces every 5 px, lit on their upper end."""
    for x in range(x0 + 6, x1 - 6, 5):
        for (yy, s) in ((y0, 1), (y1, -1)):
            c.p(x, yy, LACE[3])
            c.p(x + 1, yy + s, LACE[2])
            c.p(x + 2, yy + 2 * s, LACE[1])
            c.p(x + 3, yy + 2 * s, HIDE[1])
    for y in range(y0 + 6, y1 - 6, 5):
        for (xx, s) in ((x0, 1), (x1, -1)):
            c.p(xx, y, LACE[3])
            c.p(xx + s, y + 1, LACE[2])
            c.p(xx + 2 * s, y + 2, LACE[1])
            c.p(xx + 2 * s, y + 3, HIDE[1])


FRINGE = [8, 10, 9, 11, 8, 10, 12, 9, 10, 8, 11, 9]


def fringe(c, x0, x1, y, skip):
    """Fringe hanging off the foot: 2-px strands every 3 px, lit left, cut to a point, lengths hand-picked."""
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


def flap(c):
    """The closing flap on the back board: a strap of hide out to the right with a rounded end, whipstitched, a lace
    through a hole near its end, wound round it and hanging down to a bone toggle."""
    x0 = BX + BW - 2
    cy = BY + 97
    n = 15
    for i in range(n):
        half = 22 - i * 8 // n                      # tapers from 22 to 15
        if i >= n - 3:                              # the rounded end
            half -= (i - (n - 4)) * 2
        for y in range(cy - half, cy + half + 1):
            edge = y in (cy - half, cy + half) or i == n - 1
            if edge:
                tone = HIDE_EDGE
            elif y == cy - half + 1:
                tone = HIDE[3]
            elif y >= cy + half - 2:
                tone = HIDE[1]
            else:
                tone = HIDE[2]
            c.p(x0 + i, y, tone)
    c.vl(x0, cy - 20, cy + 20, HIDE[1])              # where it bends off the board
    for i in range(2, n - 3, 4):                     # whipstitch along its edges
        half = 22 - i * 8 // n
        c.p(x0 + i, cy - half + 1, LACE[3]), c.p(x0 + i + 1, cy - half + 2, LACE[1])
        c.p(x0 + i, cy + half - 2, LACE[2]), c.p(x0 + i + 1, cy + half - 1, LACE[1])
    hx = x0 + n - 6
    c.art(hx - 1, cy - 1, [".k.", "khk", ".k."], {"k": HIDE_EDGE, "h": LACE[0]})
    for y in range(cy - 9, cy + 10, 3):              # the lace wound round the strap
        c.p(hx + 4, y, LACE[3]), c.p(hx + 4, y + 1, LACE[1])
    lace = [(hx + 2, cy + 2), (hx + 5, cy + 12), (hx + 7, cy + 18), (hx + 6, cy + 24), (hx + 7, cy + 30)]
    for (ax, ay), (bx_, by_) in zip(lace, lace[1:]):
        m = max(abs(bx_ - ax), abs(by_ - ay))
        for t in range(m + 1):
            x = ax + round((bx_ - ax) * t / m)
            y = ay + round((by_ - ay) * t / m)
            if c.get(x, y)[:3] in (HIDE[2][:3], HIDE[1][:3], HIDE[3][:3]) or c.get(x, y)[3] == 0:
                c.p(x, y, LACE[2]), c.p(x + 1, y, LACE[0])
    tx, ty = hx + 5, cy + 31
    c.art(tx, ty, [".oo.", "owbo", "owbo", "owbo", "obbo", "obbo", "owbo", ".oo."],
          {"o": BONE[0], "w": BONE[3], "b": BONE[2]})


def wrap_and_block(c, n_left, n_right):
    """The buckskin wrap, the page block (stacks of n_left / n_right page edges) and the spine; no page faces."""
    fringe(c, BX + 6, BX + BW - 6, BY + BH, (GX - 49, GX + 47) if RIBBON_STYLE == "foot" else (GX - 12, GX + 10))
    x0, y0, x1, y1 = BX, BY, BX + BW, BY + BH
    c.fill(x0, y0, x1, y1, HIDE_EDGE)
    c.fill(x0 + 1, y0 + 1, x1 - 1, y1 - 3, HIDE[2])
    c.hl(x0 + 1, x1 - 2, y0 + 1, HIDE[3])
    c.vl(x0 + 1, y0 + 1, y1 - 4, HIDE[3])
    c.vl(x1 - 2, y0 + 2, y1 - 4, HIDE[1])
    c.hl(x0 + 1, x1 - 2, y1 - 3, HIDE[1])            # the wrap's thickness, seen along the foot
    c.hl(x0 + 2, x1 - 3, y1 - 2, HIDE[0])
    for x, y in ((x0, y0), (x0 + 1, y0), (x0, y0 + 1), (x1 - 1, y0), (x1 - 2, y0), (x1 - 1, y0 + 1),
                 (x0, y1 - 1), (x0 + 1, y1 - 1), (x0, y1 - 2), (x1 - 1, y1 - 1), (x1 - 2, y1 - 1), (x1 - 1, y1 - 2)):
        c.p(x, y, CLEAR)
    for x, y in ((x0 + 1, y0 + 1), (x1 - 2, y0 + 1), (x0 + 1, y1 - 2), (x1 - 2, y1 - 2)):
        c.p(x, y, HIDE_EDGE)
    for x, y in ((x0 + 58, y0), (x0 + 59, y0), (x0 + 214, y0), (x0, y0 + 122), (x1 - 1, y0 + 40), (x0 + 266, y1 - 1)):
        c.p(x, y, CLEAR)                             # nicks in the cut edge
        c.p(x + (1 if x == x0 else -1 if x == x1 - 1 else 0), y + (1 if y == y0 else -1 if y == y1 - 1 else 0), HIDE_EDGE)
    for gx, gy, n in ((20, 4, 5), (92, 4, 4), (178, 4, 6), (248, 4, 4), (296, 4, 3)):
        c.fill(x0 + gx, y0 + gy, x0 + gx + n, y0 + gy + 1, HIDE[1])
        c.p(x0 + gx + n, y0 + gy - 1, HIDE[4])
    for gx, gy, n in ((4, 34, 5), (4, 98, 4), (4, 158, 6), (BW - 5, 52, 4), (BW - 5, 150, 5)):
        c.fill(x0 + gx, y0 + gy, x0 + gx + 1, y0 + gy + n, HIDE[1])
        c.p(x0 + gx - 1, y0 + gy, HIDE[4])
    whipstitch(c, x0 + 1, y0 + 1, x1 - 2, y1 - 4)
    flap(c)
    # the page block: stacked edges along the fore-edges and the foot, following the dip into the gutter
    for x in range(LP - n_left, RP + n_right):
        n = n_left if x < GX else n_right
        if x < LP or x >= RP:
            continue
        for k in range(n):
            tone = SEPIA_OUT if k == n - 1 else (SEPIA[2] if k % 2 == 0 else SEPIA[1])
            c.p(x, page_bot(x) + k, tone)
    for k in range(n_left):
        tone = SEPIA_OUT if k == n_left - 1 else (SEPIA[2] if k % 2 == 0 else SEPIA[1])
        c.vl(LP - 1 - k, page_top(LP) + 1 + k, page_bot(LP) - 1 + k, tone)
        c.p(LP - 1 - k, page_bot(LP) + k, tone)
    for k in range(n_right):
        tone = SEPIA_OUT if k == n_right - 1 else (SEPIA[2] if k % 2 == 0 else SEPIA[1])
        c.vl(RP + k, page_top(RP - 1) + 1 + k, page_bot(RP - 1) - 1 + k, tone)
        c.p(RP + k, page_bot(RP - 1) + k, tone)
    for x in range(LP - n_left + 1, RP + n_right + 1):
        n = n_left if x < GX else n_right
        y = page_bot(min(max(x, LP), RP - 1)) + n
        for j in range(2):
            if c.get(x, y + j)[:3] in (HIDE[2][:3], HIDE[3][:3]):
                c.p(x, y + j, HIDE[1] if j == 0 else HIDE[2])
    for y in range(page_top(RP - 1) + n_right + 1, page_bot(RP - 1) + n_right + 1):
        if c.get(RP + n_right, y)[:3] in (HIDE[2][:3], HIDE[3][:3]):
            c.p(RP + n_right, y, HIDE[1])
    # headbands at head and tail of the spine, showing where the pages dip
    for y, rows in ((TOP - ARCH - 1, 5), (BOT + ARCH - 4, 5)):
        for x in range(GX - 4, GX + 4):
            for j in range(rows):
                if j in (0, rows - 1):
                    tone = HIDE[0]
                elif j == 1:
                    tone = BONE[3] if (x - GX) % 2 else RIBBONS["fallen"][1]
                else:
                    tone = BONE[2] if (x - GX) % 2 else RIBBONS["fallen"][2]
                c.p(x, y + j, tone)


GRAIN = [(3, 4, 3), (21, 9, 2), (40, 3, 4), (55, 13, 2), (11, 19, 2), (30, 24, 3), (47, 28, 2), (6, 33, 4),
         (60, 35, 2), (24, 39, 3), (38, 16, 2), (52, 21, 3)]


def pages(c, stains=()):
    """Both page faces: sepia, a lit top edge that falls into shadow as the page dips into the gutter, stepped
    gutter bands, grain dashes from a hand-placed tile, a deckled fore-edge, the long-stitch in the gutter."""
    for x in range(LP, RP):
        d, side = col_d(x)
        t, b = page_top(x), page_bot(x)
        c.vl(x, t, b - 1, SEPIA[3])
        c.p(x, t, SEPIA[4] if d >= 8 else SEPIA[2])
        c.p(x, b - 1, SEPIA[2])
        if d == 0:
            c.vl(x, t, b - 1, SEPIA[0])
        elif d <= 2:
            c.vl(x, t + 1, b - 2, SEPIA[1])
        elif d <= 6:
            c.vl(x, t + 1, b - 2, SEPIA[2])
        elif 128 <= d <= 145:
            c.p(x, t + 1, SEPIA[4])              # light along the arch near the fore-edge
    for x0, off in ((LP, (0, 0)), (GX, (29, 17))):
        for ty in range(TOP - 42, BOT, 42):
            for tx in range(x0 - 64, x0 + PW, 64):
                for dx, dy, n in GRAIN:
                    gx, gy = tx + (dx + off[0]) % 64, ty + (dy + off[1]) % 42
                    if x0 + 3 <= gx and gx + n < x0 + PW - 3 and col_d(gx)[0] >= 9 and col_d(gx + n)[0] >= 9 \
                            and page_top(gx) + 3 <= gy < page_bot(gx) - 3:
                        c.fill(gx, gy, gx + n, gy + 1, SEPIA[2])
                        c.p(gx + n, gy - 1, SEPIA[4])
    # the fore-edges: the leaves' edges as fine strips inside the outer edge, jogging here and there, deckled
    for x, inward in ((LP, 1), (RP - 1, -1)):
        t0, t1 = page_top(x) + 1, page_bot(x) - 2
        c.vl(x, t0, t1, SEPIA[2])
        c.vl(x + inward, t0 + 1, t1, SEPIA[4])
        c.vl(x + 2 * inward, t0 + 2, t1, SEPIA[2])
        for y, n in ((t0 + 14, 9), (t0 + 61, 6), (t0 + 103, 12), (t0 + 150, 7)):   # where a leaf sits proud
            c.vl(x + 2 * inward, y, y + n, SEPIA[4])
            c.vl(x + 3 * inward, y, y + n, SEPIA[2])
    for x, y in ((LP, TOP + 30), (LP, TOP + 31), (LP, TOP + 82), (LP, TOP + 140), (LP, TOP + 141),
                 (RP - 1, TOP + 50), (RP - 1, TOP + 51), (RP - 1, TOP + 118), (RP - 1, TOP + 160),
                 (LP + 40, None), (LP + 41, None), (LP + 101, None), (GX + 40, None), (GX + 100, None),
                 (GX + 101, None), (LP + 70, 0), (GX + 66, 0), (GX + 67, 0)):
        if y is None:
            y = page_bot(x) - 1
        elif y == 0:
            y = page_top(x)
        c.p(x, y, SEPIA_OUT)
    # long-stitch: thread across the fold at five stations
    for sy in (TOP + 16, TOP + 54, TOP + 90, TOP + 126, TOP + 162):
        c.fill(GX - 2, sy, GX + 2, sy + 1, BONE[2])
        c.fill(GX - 2, sy + 1, GX + 2, sy + 2, BONE[0])
        c.p(GX - 3, sy, SEPIA_OUT), c.p(GX + 2, sy, SEPIA_OUT)
    for x, y, shape in stains:
        c.art(x, y, shape, {"a": SEPIA[1], "b": SEPIA[2], "c": SEPIA[0]})


FOX = [[".b.", "bab", ".b."], ["ab", "b."], [".bb", "bab"], ["b.", "ab", ".b"], ["bb.", "bab", ".bb"]]


FLAP_HI = rgb((246, 236, 208))                    # the back of a lifted leaf, catching the light


def edge_tone(k):
    """The page block seen past a lifted corner: stacked leaf edges, by distance k from the block's edge."""
    return (SEPIA_OUT, SEPIA[2], SEPIA[4], SEPIA[1], SEPIA[3], SEPIA[2])[min(k, 5)]


def corner(c, side):
    """A page's bottom outer corner turned over, built the way vanilla's book (and Patchouli) build theirs: the
    corner folds in along a diagonal crease, its back lighter than the page (it faces the light); where it lifted
    away the stacked edges of the leaves below show; the crease is a soft tan band with a few darker dots, its
    shadow falling on the leaves below; no ink outline anywhere. The flap is shorter than a flat fold (it curls),
    its tip rounded. Decoration only: the page turns on the arrows."""
    fu, fv = 12, 11                                  # the crease meets the foot fu in, the fore-edge fv up
    tip = (9, 10)                                    # where the corner's point lands
    x0 = LP if side == "l" else RP - 1
    y1 = page_bot(x0) - 1

    def P(u, v, col):                                # u: in from the fore-edge, v: up from the foot
        c.p(x0 + u if side == "l" else x0 - u, y1 - v, col)

    def side_of(u, v):                               # < 1 on the corner's side of the crease
        return (u + 0.5) / fu + (v + 0.5) / fv

    def cross(ax, ay, bx, by, px, py):
        return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

    def in_flap(u, v):                               # inside the triangle crease-at-foot, tip, crease-at-edge
        px, py = u + 0.5, v + 0.5
        d1 = cross(fu, 0, tip[0], tip[1], px, py)
        d2 = cross(tip[0], tip[1], 0, fv, px, py)
        d3 = cross(0, fv, fu, 0, px, py)
        return (d1 >= 0 and d2 >= 0 and d3 >= 0) or (d1 <= 0 and d2 <= 0 and d3 <= 0)
    for v in range(fv + 1):                          # the leaves below, where the corner lifted
        for u in range(fu + 1):
            if side_of(u, v) < 1:
                P(u, v, edge_tone(min(u, v)))
    for v in range(fv + 1):                          # the crease's shadow on them: a soft band with darker dots
        for u in range(fu + 1):
            t = side_of(u, v)
            if 0.80 <= t < 1:
                P(u, v, SEPIA[0] if (u + 2 * v) % 5 == 0 else SEPIA[1])
    for v in range(fv + 2):
        for u in range(fu + 2):
            if not in_flap(u, v):
                continue
            t = side_of(u, v)
            free = not in_flap(u + 1, v) or not in_flap(u, v + 1) or not in_flap(u - 1, v) or not in_flap(u, v - 1)
            at_crease = t < 1.09
            near_tip = math.hypot(u + 0.5 - tip[0], v + 0.5 - tip[1]) < 1.6
            if near_tip and free:
                continue                             # the rounded tip
            if at_crease:
                tone = SEPIA[3]
            elif free:
                tone = SEPIA[2]
            elif t < 1.22:
                tone = SEPIA[4]
            else:
                tone = FLAP_HI
            P(u, v, tone)
    for u, v in ((tip[0], tip[1] + 1), (tip[0] + 1, tip[1]), (tip[0] + 1, tip[1] + 1)):
        if not in_flap(u, v):
            P(u, v, SEPIA[2])                        # its shadow on the page, beside the tip


ARROW = ["...........a....",
         "...........aa...",
         "...aaaaaaaaaaa..",
         "..aaaaaaaaaaaaa.",
         ".aa........aa...",
         ".aa........a....",
         ".aa.............",
         "..aa............"]


def arrow(c, side, hover=False):
    """The page-turn arrows, inked by hand: a hooked arrow (after vanilla's page arrows) in brown ink, red-brown
    when the mouse is on it. Its own sprite, beside the lifted corner at the foot of the page."""
    rows = ARROW if side == "r" else [r[::-1] for r in ARROW]
    w = len(rows[0])
    y = page_bot(LP if side == "l" else RP - 1) - 12
    x = (LP + 17) if side == "l" else (RP - 17 - w)
    c.art(x, y, rows, {"a": BRAND if hover else INKB[1]})


RIBBON_STYLE = "tabs"                                # "tabs" (the owner's pick) or "foot" (the other draft)
SECTION_MARKS = {"constellations": ["a...a", ".a.a.", "..a..", ".a.a.", "a...a"],
                 "planets": [".aaa.", "a...a", "aaaaa", "a...a", ".aaa."],
                 "rare": ["a....", ".a...", "..aa.", "..aaa", "...aa"],
                 "fallen": ["..a..", ".aaa.", "aaaaa", ".a.a.", "a...a"]}
SHEEN = {k: rgb(tuple(min(255, r[3][i] + 44) for i in range(3))) for k, r in RIBBONS.items()}
RW = 7                                               # a ribbon's width
FOOT_X = {"l": [GX - 16, GX - 25, GX - 34, GX - 43], "r": [GX + 11, GX + 20, GX + 29, GX + 38]}
FOOT_LEN = [17, 21, 15, 19]
WAVE = [0] * 9 + [1] * 30                   # one gentle bend part way down, not a wiggle


def ribbon_strip(c, path, w, r, end="down"):
    """A silk ribbon along a path of (x, y) rows, w px wide: outlined, lit on its left fold, a sheen down the
    middle, shaded on its right; the end at path[-1] cut in a swallow-tail (a V, widest at the very end)."""
    for x, y in path:
        c.p(x, y, r[0])
        c.p(x + w - 1, y, r[0])
        for k in range(1, w - 1):
            c.p(x + k, y, r[3] if k == 1 else r[1] if k == w - 2 else r[2])
    x, y = path[-1]
    sgn = 1 if end == "down" else -1
    mid = (w - 1) / 2
    depth = 3
    for j in range(depth):                               # j = 0 at the very end
        yy = y - sgn * j
        half = depth - 1 - j                             # cut half-width at this row
        for k in range(w):
            if abs(k - mid) <= half + (0.5 if w % 2 == 0 else 0) - 0.5 + (1 if j == 0 else 0) * 0:
                c.p(x + k, yy, CLEAR)
        for k in range(w):                               # outline the cut
            if c.get(x + k, yy)[3] and (not c.get(x + k - 1, yy)[3] or not c.get(x + k + 1, yy)[3]
                                        or not c.get(x + k, yy + sgn)[3]):
                c.p(x + k, yy, r[0])


def silk_row(c, x, y, r, sheen, tone=0):
    """One row of a 7-px silk ribbon: outlined, the sheen just left of the middle (light from the top left), the
    right fold in shade. tone -1 = a row in a dip (darker), +1 = a row lifted over something (lighter)."""
    row = [r[0], r[3], r[2], r[2], r[2], r[1], r[0]]      # silk lies flat: a lit edge, a shaded edge
    if tone < 0:
        row = [r[0], r[2], r[1], r[1], r[1], r[0], r[0]]
    elif tone > 0:
        row = [r[0], sheen, r[3], r[3], r[3], r[2], r[0]]
    for k, col in enumerate(row):
        c.p(x + k, y, col)


def swallow(c, x, y, r, up):
    """Cut a swallow-tail into the ribbon end at row y (the very end), pointing up or down."""
    s_ = -1 if up else 1
    for j, (a, b) in enumerate(((2, 4), (3, 3))):     # rows from the end inwards: clear columns a..b
        yy = y - s_ * j
        for k in range(a, b + 1):
            c.p(x + k, yy, CLEAR)
        c.p(x + a - 1, yy, r[0]), c.p(x + b + 1, yy, r[0])
    c.p(x + 3, y - s_ * 2, r[0])


def tab(c, x, top, length, r, s, open_=False):
    """A ribbon tab out of the head: silk, swallow-tailed, the section's mark stitched on near its end; where it
    comes out from between the leaves it is creased, and it throws a shadow on the page to its right."""
    sheen = SHEEN[s]
    for j in range(length):
        silk_row(c, x, top - j, r, sheen, tone=-1 if j == 0 else 1 if j == 1 else 0)
    for k in range(4):                               # a glint across it
        c.p(x + 1 + k, top - 5 - k, sheen)
        c.p(x + 2 + k, top - 5 - k, r[3])
    swallow(c, x, top - length + 1, r, up=True)
    my = top - length + 5
    c.art(x + 1, my + 1, SECTION_MARKS[s], {"a": r[0]})
    c.art(x + 1, my, SECTION_MARKS[s], {"a": sheen})
    c.p(x + RW, top - 1, HIDE[1]) if c.get(x + RW, top - 1)[:3] in (HIDE[2][:3], HIDE[3][:3]) else None
    c.hl(x + 1, x + RW, top + 1, SEPIA[1]) if not open_ else None


def open_ribbon(c, s):
    """The open section's ribbon: out of the head at the spine as a tab (its mark at the end), down the gutter
    between the open pages, over the foot and hanging out with a swallow-tail. It lies in the gutter's shade, lifts
    over each stitch of the long-stitch (a light row, a dark one under it) and throws a shadow on the right-hand
    page beside it."""
    r, sheen = RIBBONS[s], SHEEN[s]
    x = GX - 4
    y_top = BY - 16
    y_end = BY + BH + 17
    stitches = (TOP + 16, TOP + 54, TOP + 90, TOP + 126, TOP + 162)
    in_page = range(page_top(GX) - 1, page_bot(GX) + 1)
    for y in range(y_top, y_end + 1):
        tone = 0
        if y in [st - 1 for st in stitches] or y == page_top(GX) - 2:
            tone = 1
        elif y in [st + 1 for st in stitches] or y == page_top(GX) - 1:
            tone = -1
        elif y in in_page and (y - TOP) % 1 == 0:
            tone = 0
        silk_row(c, x, y, r, sheen, tone)
        if y in in_page:
            c.p(x + RW, y, SEPIA[0])                 # its shadow in the gutter, on the right-hand page
    for gy in (TOP + 30, TOP + 72, TOP + 108, TOP + 144, BY + BH + 6):   # glints where the silk catches the light
        for k in range(4):
            c.p(x + 1 + k, gy + 3 - k, sheen)
            c.p(x + 2 + k, gy + 3 - k, r[3])
    swallow(c, x, y_top, r, up=True)
    swallow(c, x, y_end, r, up=False)
    c.art(x + 1, y_top + 5, SECTION_MARKS[s], {"a": r[0]})
    c.art(x + 1, y_top + 4, SECTION_MARKS[s], {"a": sheen})
    for y in range(BY + BH - 4, BY + BH + 1):        # where it crosses the wrap's edge: a crease, darker
        pass
    silk_row(c, x, BY + BH - 3, r, sheen, -1)
    silk_row(c, x, BY + BH - 2, r, sheen, 1)


def ribbons(c, open_section, ahead):
    """The section ribbons. 'foot': silk ribbons hanging out of the foot of the page block beside the spine, those
    behind the open spread on the left, those ahead on the right, each with a slight wave and a swallow-tail; the
    open section's ribbon lies down the gutter from the headband and hangs out longest. 'tabs': short straight
    ribbons out of the head with the section's mark stitched on."""
    left = [s for s in SECTIONS if s != open_section and s not in ahead]
    right = [s for s in SECTIONS if s in ahead and s != open_section]
    if RIBBON_STYLE == "foot":
        for side, group in (("l", left), ("r", right)):
            for k, s in enumerate(group):
                r = RIBBONS[s]
                x = FOOT_X[side][k]
                y0 = page_bot(x + 3) - 1
                n = BY + BH - y0 + FOOT_LEN[SECTIONS.index(s)]
                path = [(x + WAVE[max(0, j - (BY + BH - y0)) % len(WAVE)] if y0 + j >= BY + BH else x, y0 + j)
                        for j in range(n)]
                ribbon_strip(c, path, 6, r)
                c.hl(x, x + 5, y0, r[0])                 # where it comes out from between the leaves
    else:
        for side, group in (("l", left), ("r", right)):
            for k, s in enumerate(group):
                i = SECTIONS.index(s)
                r = RIBBONS[s]
                x = (GX + 26 + i * 13) if side == "r" else (LP + 60 + i * 13)
                top = page_top(x) - 1
                tab(c, x, top, 16, r, s)
    if open_section and RIBBON_STYLE == "tabs":
        open_ribbon(c, open_section)
    elif open_section:
        r = RIBBONS[open_section]
        x = GX - 2
        y0 = TOP - ARCH + 2
        hang = 23
        path = [(x + (WAVE[(y - BY - BH) % len(WAVE)] if y >= BY + BH else 0), y) for y in range(y0, BY + BH + hang)]
        ribbon_strip(c, path, 5, r)
        c.vl(x - 1, page_top(x - 1), page_bot(x - 1) - 1, SEPIA[0])


def base(spread, open_section, ahead, n_left, n_right, stains=()):
    c = Cv(W, H)
    wrap_and_block(c, n_left, n_right)
    pages(c, stains)
    ribbons(c, open_section, ahead)
    corner(c, "l")
    corner(c, "r")
    if spread > 0:
        arrow(c, "l")
    arrow(c, "r", hover=spread == 1)
    return c


# ================================================================================================ pasted pictures
def photo_corners(c, x0, y0, x1, y1, n=7, empty=False):
    """Leather photo corners slotted over a picture's corners (or drawn in pencil where one will go)."""
    for (cx, cy, fx, fy) in ((x0 - 2, y0 - 2, 1, 1), (x1 + 2, y0 - 2, -1, 1), (x0 - 2, y1 + 2, 1, -1),
                             (x1 + 2, y1 + 2, -1, -1)):
        for j in range(n):
            for i in range(n - j):
                x, y = cx + fx * i, cy + fy * j
                if empty:
                    if i + j == n - 1 or i == 0 or j == 0:
                        c.p(x, y, PENCILB)
                    continue
                if i + j == n - 1 or i == 0 or j == 0:
                    c.p(x, y, LACE[0])
                else:
                    c.p(x, y, LACE[3] if (fx == 1 and i == 1) or (fy == 1 and j == 1) else LACE[2])
        if not empty:                                   # its shadow on the page
            for t in range(n):
                sx, sy = cx + fx * t + (1 if fx == 1 else 0), cy + fy * (n - 1 - t) + 1
                if fx == -1 or True:
                    c.p(cx + fx * (n - 1 - t) + 1, cy + fy * t + (1 if fy == 1 else 0), SEPIA[1]) if False else None


def card(c, x0, y0, w, h):
    """A pasted card: pale paper with a shadow line on the page under its lower and right edges."""
    c.fill(x0 + 1, y0 + h, x0 + w + 1, y0 + h + 1, SEPIA[1])
    c.fill(x0 + w, y0 + 1, x0 + w + 1, y0 + h + 1, SEPIA[1])
    c.fill(x0, y0, x0 + w, y0 + h, PAPER[4])
    c.hl(x0, x0 + w - 1, y0 + h - 1, PAPER[2])
    c.vl(x0 + w - 1, y0, y0 + h - 1, PAPER[2])


def chart(c, x, y, bw, bh, con, star, line, gap=3, lines=True, margin=20):
    pts = [(x + px, y + py, m) for px, py, m in chart_points(con, bw, bh, margin)]
    if lines:
        for a, b in con["lines"]:
            line_gapped(c, pts[a][:2], pts[b][:2], line, gap)
    for px, py, m in pts:
        star(c, px, py, m)
    return pts


def cyan_star(cc, x, y, m):
    if m <= 1:
        cc.art(x - 2, y - 2, [".ddd.", "dwwwd", "dwwwd", "dwwwd", ".ddd."], {"w": CYAN[4], "d": CYAN[3]})
    elif m == 2:
        cc.art(x - 1, y - 1, ["dwd", "www", "dwd"], {"w": CYAN[4], "d": CYAN[3]})
    else:
        cc.art(x - 1, y - 1, [".d.", "dwd", ".d."], {"w": CYAN[4], "d": CYAN[2]})


def pencil_star(cc, x, y, m):
    if m <= 1:
        cc.art(x - 1, y - 1, ["aaa", "a.a", "aaa"], {"a": PENCILB})
    elif m == 2:
        cc.art(x - 1, y - 1, [".a.", "a.a", ".a."], {"a": PENCILB})
    else:
        cc.p(x, y, PENCILB)


def cyanotype(c, x0, y0, w, h, con):
    """A cyanotype print: the blue brushed onto a pale card with a ragged edge, the stars left white."""
    card(c, x0, y0, w, h)
    ix0, iy0, ix1, iy1 = x0 + 4, y0 + 4, x0 + w - 4, y0 + h - 4
    c.fill(ix0, iy0, ix1, iy1, CYAN[1])
    for x, y, col in ((ix0 + 9, iy0, PAPER[4]), (ix0 + 10, iy0, PAPER[4]), (ix0 + 30, iy0 - 1, CYAN[1]),
                      (ix0 + 31, iy0 - 1, CYAN[1]), (ix0 + 32, iy0 - 1, CYAN[1]), (ix1 - 20, iy0, PAPER[4]),
                      (ix1 - 1, iy0 + 12, PAPER[4]), (ix1, iy0 + 30, CYAN[1]), (ix1, iy0 + 31, CYAN[1]),
                      (ix1 - 1, iy1 - 9, PAPER[4]), (ix0 + 50, iy1, CYAN[1]), (ix0 + 51, iy1, CYAN[1]),
                      (ix0 + 18, iy1 - 1, PAPER[4]), (ix0, iy0 + 20, PAPER[4]), (ix0 - 1, iy0 + 40, CYAN[1]),
                      (ix0 - 1, iy0 + 41, CYAN[1]), (ix1 - 40, iy1, CYAN[1])):
        c.p(x, y, col)
    for x, y, n in ((ix0 + 2, iy0 + 2, 14), (ix1 - 26, iy1 - 3, 20), (ix0 + 40, iy0 + 1, 18)):
        c.hl(x, x + n, y, CYAN[0])
    for x, y, n in ((ix0 + 1, iy0 + 8, 10), (ix1 - 2, iy0 + 40, 12)):
        c.vl(x, y, y + n, CYAN[0])
    chart(c, ix0, iy0, ix1 - ix0, iy1 - iy0, con, cyan_star, CYAN[3], gap=4)


def planet_plate(c, x0, y0, size, sprite):
    """A photo plate of a planet: a white-bordered print of the night with the planet in the middle."""
    card(c, x0, y0, size, size)
    c.fill(x0 + 3, y0 + 3, x0 + size - 3, y0 + size - 3, NIGHT[1])
    for dx, dy, col in ((6, 7, STARLIGHT[1]), (size - 10, 9, STARLIGHT[2]), (9, size - 11, STARLIGHT[0]),
                        (size - 8, size - 14, STARLIGHT[1]), (size // 2 + 14, 6, STARLIGHT[0])):
        c.p(x0 + dx, y0 + dy, col)
    sp = Cv(sprite.width, sprite.height)
    sp.im = sprite.convert("RGBA")
    sp.px = sp.im.load()
    c.paste(sp, x0 + (size - sprite.width) // 2, y0 + (size - sprite.height) // 2)


# ================================================================================================ marks
def brand(c, cx, cy, col=BRAND):
    """The Circle Star, a rancher's brand, stamped in red-brown; a little worn."""
    c.ring(cx + 0.5, cy + 0.5, 6, 8, col)
    c.art(cx - 4, cy - 4, ["....a....", "....a....", "...aaa...", "aaaaaaaaa", ".aaaaaaa.", "..aaaaa..",
                           "..aa.aa..", ".aa...aa.", "........."], {"a": col})
    for x, y in ((cx + 7, cy - 2), (cx - 3, cy + 7), (cx - 7, cy - 3)):
        c.p(x, y, SEPIA[3])


def compass_rose(c, x, y, col, soft):
    c.art(x, y, ["......c......", "......c......", ".....ccc.....", ".....ccc.....", "..s..csc..s..",
                 "...s.csc.s...", "sssssc.cssss.", "...s.sss.s...", "..s..sss..s..", ".....sss.....",
                 ".....sss.....", "......s......", "......s......"], {"c": col, "s": soft})
    F.draw(c, x + 4, y - 10, "N", col)


def coffee_ring(c, cx, cy, r):
    for k in range(72):
        a = k * 5
        if 200 < a < 245:
            continue
        x = int(math.floor(cx + math.cos(math.radians(a)) * r))
        y = int(math.floor(cy + math.sin(math.radians(a)) * r))
        c.p(x, y, SEPIA[1])
        if 20 < a < 130:
            c.p(x, y + 1, SEPIA[0])


def tin_star(c, cx, cy, earned=True):
    """A tin-star badge (five points with balls on their tips), pinned to the page; pencil outline if not earned."""
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = 8.4 if k % 2 == 0 else 4.9
        pts.append((cx + 0.5 + math.cos(a) * r, cy + 0.5 + math.sin(a) * r))

    def inside(x, y):
        n, ins = len(pts), False
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                ins = not ins
        return ins
    body = {(x, y) for y in range(cy - 10, cy + 11) for x in range(cx - 10, cx + 11) if inside(x + 0.5, y + 0.5)}
    for k in range(0, 10, 2):
        bx, by = pts[k]
        for y in range(int(by) - 2, int(by) + 2):
            for x in range(int(bx) - 2, int(bx) + 2):
                if math.hypot(x + 0.5 - bx, y + 0.5 - by) <= 1.6:
                    body.add((x, y))
    if not earned:
        for x, y in body:
            if any((x + dx, y + dy) not in body for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.p(x, y, PENCILB)
        return
    for x, y in body:                                  # a clean bevel: lit where the upper left is open
        edge = any((x + ex, y + ey) not in body for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            tone = TIN[0]
        elif (x - 1, y - 1) not in body or (x - 1, y) not in body and (x, y - 1) not in body:
            tone = TIN[4]
        elif (x - 1, y) not in body or (x, y - 1) not in body:
            tone = TIN[3]
        elif (x + 1, y + 1) not in body or (x + 2, y + 2) not in body:
            tone = TIN[1]
        else:
            tone = TIN[2]
        c.p(x, y, tone)
    for x, y in body:                                  # its shadow on the page
        if (x + 1, y + 1) not in body:
            c.p(x + 1, y + 1, SEPIA[1]) if c.get(x + 1, y + 1)[:3] == SEPIA[3][:3] else None
    lit_disc(c, cx + 0.5, cy + 0.5, 2.2, [TIN[0], TIN[1], TIN[2], TIN[3]])
    c.p(cx, cy - 9, LACE[0]), c.p(cx, cy - 10, BONE[2])   # the pin's head above the top point


def vignette(c, x, y):
    """A sketch for the foot of the title page: a mesa on the horizon, a saguaro, a star falling."""
    c.hl(x, x + 75, y + 18, PENCILB)
    c.art(x + 4, y + 10, ["....aaaaaaaaaa.....", "...a..........a....", "..a............a...",
                          ".a..............aa.", "a.................a"], {"a": INKB[2]})
    c.art(x + 50, y + 7, ["..a..", "a.a..", "a.a.a", "aaa.a", "..aaa", "..a..", "..a..", "..a..", "..a.."],
          {"a": INKB[2]})
    c.art(x + 58, y, ["p.......", ".p......", "..pp....", "...aaa..", "....aaa.", ".....aa."],
          {"a": INKB[2], "p": PENCILB})
    c.art(x + 63, y + 6, [".a.", "aaa", ".a."], {"a": INKB[1]})


def moon_faces(c, x, y, tonight=2):
    for k in range(8):
        mx = x + k * 15
        c.ring(mx + 0.5, y + 0.5, 4, 5, INKB[1])
        if k == tonight:
            c.ring(mx + 0.5, y + 0.5, 6, 7, BRAND)
        for yy in range(y - 4, y + 5):
            for xx in range(mx - 4, mx + 5):
                dx = xx - mx
                if math.hypot(dx, yy - y) < 3.6 and ((k < 4 and dx < 2 - k * 1.5) or (k >= 4 and dx > -2 + (k - 4) * 1.5)):
                    c.p(xx, yy, INKB[2])


def tick_box(c, x, y, ticked):
    c.art(x, y, ["aaaaaaa", "a.....a", "a.....a", "a.....a", "a.....a", "a.....a", "aaaaaaa"], {"a": INKB[1]})
    if ticked:
        c.art(x + 1, y - 1, [".....b", "....b.", "b..b..", ".bb...", ".b...."], {"b": INKB[0]})


# ================================================================================================ the spreads
def spread_contents():
    c = base(0, None, SECTIONS, 2, 5, stains=[(LP + 6, TOP + 120, FOX[2]), (RP - 12, TOP + 8, FOX[0])])
    tw = caps_width("STAR ATLAS")
    tx = LX + (CONTENT - tw) // 2
    draw_caps(c, tx, TOP + 12, "STAR ATLAS", INKB[0])
    c.hl(tx + 2, tx + tw + 2, TOP + 25, INKB[1])          # the lasso flourish: the rope runs out into its loop
    c.ring(tx + tw + 7.5, TOP + 23.5, 4, 5, INKB[1])
    F.centred(c, LX, CONTENT, TOP + 32, f"Kept by {PLAYER}", INKB[1])
    icons = {"constellations": [".a...a.", "..a.a..", "...a...", "..a.a..", ".a...a."],
             "planets": ["..aaa..", ".a...a.", "aaaaaaa", ".a...a.", "..aaa.."],
             "rare": ["a......", ".a.....", "..aa...", "...aaa.", "...aaa."],
             "fallen": ["...a...", "..aaa..", "aaaaaaa", "..a.a..", ".a...a."]}
    y = TOP + 54
    for s in SECTIONS:
        a, b = STATE[s]
        c.art(LX + 2, y + 1, icons[s], {"a": INKB[1]})
        F.draw(c, LX + 13, y, LABEL[s], INKB[0])
        ct = f"{a} of {b}" if b else str(a)
        F.right(c, LX + CONTENT, y, ct, INKB[0])
        y += 22
    vignette(c, LX + (CONTENT - 76) // 2, TOP + 146)
    F.centred(c, RX, CONTENT, TOP + 12, "The night of", INKB[1])
    moon_faces(c, RX + 13, TOP + 32)
    F.centred(c, RX, CONTENT, TOP + 44, "Night 31 of 48, half moon", INKB[0])
    c.hl(RX + 40, RX + CONTENT - 41, TOP + 57, PENCILB)
    F.wrapped(c, RX, CONTENT, TOP + 64, L["wildskies.atlas.tips"], INKB[1], 8)
    coffee_ring(c, RX + 108, TOP + 156, 13)
    return c


def spread_constellation():
    c = base(1, "constellations", ["planets", "rare", "fallen"], 3, 5,
             stains=[(LP + 9, TOP + 7, FOX[3]), (RP - 14, TOP + 150, FOX[4])])
    con = CON["lasso"]
    F.centred(c, LX, CONTENT, TOP + 10, L["wildskies.constellation.lasso"], INKB[0])
    px, py, pw_, ph_ = LX + 9, TOP + 26, 114, 78
    cyanotype(c, px, py, pw_, ph_, con)
    photo_corners(c, px, py, px + pw_ - 1, py + ph_ - 1)
    F.wrapped(c, LX, CONTENT, TOP + 114, L["wildskies.constellation.lasso.legend"], INKB[0], 3)
    note = "Night 30, new moon"
    bw_ = 17 + 5 + F.width(note)
    sx = LX + (CONTENT - bw_) // 2
    brand(c, sx + 8, TOP + 157)
    F.draw(c, sx + 22, TOP + 153, note, INKB[1])
    shoe = CON["horseshoe"]
    F.centred(c, RX, CONTENT, TOP + 10, L["wildskies.atlas.unknown"], INKB[2])
    px = RX + 9
    photo_corners(c, px, py, px + pw_ - 1, py + ph_ - 1, empty=True)
    chart(c, px + 4, py + 4, pw_ - 8, ph_ - 8, shoe, pencil_star, PENCILB, lines=False)
    c.art(px + pw_ // 2 - 2, py + ph_ // 2 - 6, [".aaa.", "a...a", "....a", "...a.", "..a..", "..a..", ".....", "..a.."],
          {"a": PENCILB})
    F.wrapped(c, RX, CONTENT, TOP + 114, f"Highest at midnight around night {best_night(shoe['h'])} of 48.",
              INKB[2], 3)
    return c


def planet_sprite(pid):
    im = Image.open(ROOT / "src/main/resources/assets/wildskies/textures/gui/planets.png").convert("RGBA")
    regions = {"ember": (0, 36), "old_gold": (92, 36)}
    if pid in regions:
        u, v = regions[pid]
        return im.crop((u, v, u + 45, v + 45))
    raise KeyError(pid)


def spread_planet():
    c = base(13, "planets", ["rare", "fallen"], 4, 3,
             stains=[(LP + 12, TOP + 160, FOX[1]), (RP - 10, TOP + 20, FOX[2])])
    # left: Old Gold, found (three nights tracked)
    F.centred(c, LX, CONTENT, TOP + 10, L["wildskies.planet.old_gold"], INKB[0])
    size = 57
    px, py = LX + (CONTENT - size) // 2, TOP + 26
    planet_plate(c, px, py, size, planet_sprite("old_gold"))
    photo_corners(c, px, py, px + size - 1, py + size - 1, n=6)
    F.centred(c, LX, CONTENT, TOP + 92, L["wildskies.atlas.nights"], INKB[1])
    bx0 = LX + (CONTENT - (3 * 7 + 2 * 5)) // 2
    for k in range(3):
        tick_box(c, bx0 + k * 12, TOP + 104, True)
    F.wrapped(c, LX, CONTENT, TOP + 118, L["wildskies.planet.old_gold.legend"], INKB[0], 3)
    note = "Night 22, full moon"
    bw_ = 17 + 5 + F.width(note)
    sx = LX + (CONTENT - bw_) // 2
    brand(c, sx + 8, TOP + 157)
    F.draw(c, sx + 22, TOP + 153, note, INKB[1])
    # right: Ember, seen one night of three
    F.centred(c, RX, CONTENT, TOP + 10, L["wildskies.planet.ember"], INKB[0])
    px = RX + (CONTENT - size) // 2
    planet_plate(c, px, py, size, planet_sprite("ember"))
    photo_corners(c, px, py, px + size - 1, py + size - 1, n=6)
    F.centred(c, RX, CONTENT, TOP + 92, L["wildskies.atlas.nights"], INKB[1])
    bx0 = RX + (CONTENT - (3 * 7 + 2 * 5)) // 2
    for k in range(3):
        tick_box(c, bx0 + k * 12, TOP + 104, k == 0)
    F.wrapped(c, RX, CONTENT, TOP + 118, L["wildskies.planet.ember.legend"], INKB[0], 3)
    F.wrapped(c, RX, CONTENT, TOP + 150, "Two more nights to go.", INKB[2], 2)
    return c


CLAIMS = [("12", "Plains", "340 N"), ("19", "Badlands", "1210 SE"), ("27", "Taiga", "880 W")]


def spread_fallen():
    c = base(20, "fallen", [], 6, 2, stains=[(LP + 20, TOP + 150, FOX[0]), (RP - 16, TOP + 12, FOX[4])])
    F.centred(c, LX, CONTENT, TOP + 10, L["wildskies.atlas.fallen"], INKB[0])
    F.centred(c, LX, CONTENT, TOP + 24, "3 dug up", INKB[1])
    marks = [1, 5, 10, 25]
    gap = 32
    x0 = LX + (CONTENT - 3 * gap) // 2
    for k, m in enumerate(marks):
        cx = x0 + k * gap
        tin_star(c, cx, TOP + 52, earned=STATE["fallen"][0] >= m)
        s = str(m)
        F.draw(c, cx - F.width(s) // 2 + 1, TOP + 66, s, INKB[0] if STATE["fallen"][0] >= m else INKB[2])
    c.hl(LX + 40, LX + CONTENT - 41, TOP + 82, PENCILB)
    F.wrapped(c, LX, CONTENT, TOP + 90, L["wildskies.atlas.fallen_hint"], INKB[1], 5)
    compass_rose(c, LX + (CONTENT - 13) // 2, TOP + 152, INKB[1], INKB[2])
    # right: the claims ledger
    F.centred(c, RX, CONTENT, TOP + 10, "Claims", INKB[0])
    cols = (RX + 2, RX + 26, RX + CONTENT)
    hy = TOP + 28
    F.draw(c, cols[0], hy, "Night", INKB[2])
    F.draw(c, cols[1] + 8, hy, "Land", INKB[2])
    F.right(c, cols[2], hy, "From spawn", INKB[2])
    c.hl(RX, RX + CONTENT, hy + 10, INKB[1])
    y = hy + 15
    while y + 10 < BOT - 18:
        k = (y - hy - 15) // 13
        if k < len(CLAIMS):
            n, land, dist = CLAIMS[k]
            F.right(c, cols[0] + 22, y, n, INKB[0])
            F.draw(c, cols[1] + 8, y, land, INKB[0])
            F.right(c, cols[2], y, dist, INKB[0])
            c.art(cols[1] + 1, y + 1, ["..a..", ".aaa.", "aaaaa", ".a.a."], {"a": BRAND})
        c.hl(RX, RX + CONTENT, y + 10, SEPIA[1])
        y += 13
    return c


def leaf(c, theta):
    """One frame of a page turning right to left, theta in degrees (0 = lying on the right, 180 = on the left). The
    leaf is foreshortened by cos(theta), its free edge rises as it stands up (seen from a little in front), the top
    corner lags the bottom one; the front of the leaf darkens as it tilts away, the back is lit as it comes down. It
    casts a shadow under its lower edge."""
    t = math.radians(theta)
    w = int(round((PW - 1) * math.cos(t)))
    lift = int(round(7 * math.sin(t)))
    sgn = 1 if w >= 0 else -1
    front = theta < 90
    ih = (page_top(GX), page_bot(GX))                        # the leaf's spine edge
    rows = {}
    for y in range(ih[0] - lift - 2, ih[1] + 2):
        pass
    top_out, bot_out = TOP - ARCH - lift, BOT + ARCH - lift
    for i in range(abs(w) + 1):
        f = i / max(1, abs(w))
        x = GX + sgn * i - (1 if sgn < 0 else 0)
        yt = int(round(ih[0] + (top_out - ih[0]) * f))
        yb = int(round(ih[1] + (bot_out - ih[1]) * f))
        lag = int(round(4 * f * f))                          # the top corner lags behind
        rows[x] = (yt + (lag if front else 0), yb)
    xs = sorted(rows)
    edge_x = xs[-1] if sgn > 0 else xs[0]
    for x in xs:                                             # the shadow below the leaf
        yt, yb = rows[x]
        for j in range(1, 3 + lift // 3):
            if c.get(x, yb + j)[:3] in (SEPIA[3][:3], SEPIA[2][:3], SEPIA[4][:3]):
                c.p(x, yb + j, SEPIA[1])
    for x in xs:
        yt, yb = rows[x]
        d = abs(x - GX)
        for y in range(yt, yb):
            if front:
                tone = SEPIA[3] if d < abs(w) * 0.55 else SEPIA[2]
            else:
                tone = SEPIA[4] if d > abs(w) * 0.35 else SEPIA[3]
            c.p(x, y, tone)
        c.p(x, yt, SEPIA_OUT)
        c.p(x, yb - 1, SEPIA_OUT)
        if not front:
            c.p(x, yt + 1, SEPIA[4])
    yt, yb = rows[edge_x]
    c.vl(edge_x, yt, yb - 1, SEPIA_OUT)
    for x in xs[:: (1 if sgn > 0 else -1)][:3]:
        c.vl(x, rows[x][0], rows[x][1] - 1, SEPIA[0] if x == GX or x == GX - 1 else SEPIA[1])


def turn_frames():
    out = []
    for theta in (30, 70, 110, 150):
        c = spread_constellation()
        leaf(c, theta)
        out.append(c)
    return out


SPREADS = [("contents", spread_contents), ("constellation", spread_constellation), ("planet", spread_planet),
           ("fallen", spread_fallen)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SPREADS:
        fn().save(str(OUT / f"spread_{name}.png"))
        print("painted", name)
    for k, c in enumerate(turn_frames()):
        c.save(str(OUT / f"turn_{k}.png"))
    print("painted the page turn")


if __name__ == "__main__":
    main()
