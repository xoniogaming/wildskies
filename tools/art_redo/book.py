"""The Star Atlas (gui/atlas.png, 512x512): the saddlebag journal, painted again from its description.

Concept. A stargazer's field journal that lives in a saddlebag. Outside-in: a soft BUCKSKIN wrap seen from its rough
flesh side, its cut edge turned over in a hem and whipstitched with a rawhide lace through punched holes; a sewn-on
fringe band along the foot; a strap from the back board with a lace wound through it down to a carved bone toggle.
On it lies a thick block of SEPIA leaves: both pages arch and dive into the spine, the striped head- and tailband show
in the notches, waxed linen long-stitches run down the valley, the fore-edges are deckled and the stack of leaves grows
on the side you have read (painted per depth). The paper is aged at its edges, with pale fibres in it; stains and
foxing are separate small sprites so they never sit under a line of writing. Everything written is brown iron-gall
ink. What has been seen is PASTED IN: Prussian-blue cyanotypes of the constellations (brushed on, streaky, the one cold
thing on the warm page) and glass-plate photographs of planets and rare sights, held by saddle-leather photo corners;
what hasn't is a pencil sketch in pencilled corners. Finds are burnt in with the Circle Star brand, fallen stars earn
pinned tin stars, and dug-up stars are entered in a ruled claims ledger. Silk ribbons mark the sections: closed ones
are short tabs out of the head, the open one runs down the gutter and out of the foot.

It ties into the kit by its materials: the same buckskin and lace as the item icon, the same brass and tin as the
star view's instruments, and the prints show the star view's own cold sky.

Every part is its own region in the texture so the code can compose any page. Layout numbers are the redesign's
(W, H, BX, BY, BW, BH, GX, LP, RP, TOP, BOT, PW, DIVE, ARCH, CONTENT, RW), so mockups and the later Java agree.
"""
import math

from ramps import (Cv, CLEAR, rgb, mix, sprite, trimmed, put_centred, HIDE, FLESH, LACE, LEATHER, TIN, SEPIA,
                   SEPIA_OUT, FLAP_HI, CARD, INKB, INK_GHOST, PENCIL, BRAND, BONE, THREAD, RIBBONS, SECTIONS, NIGHT,
                   STARLIGHT, CYAN, poly_mask, star_points, moon_is_lit, Packer, centred_by_box, dash_starts)

# ------------------------------------------------------------------------------------------------ the layout
W, H = 344, 236
BX, BY, BW, BH = 4, 18, 320, 194
GX = BX + 160
LP, RP = BX + 10, BX + 310
TOP, BOT = BY + 7, BY + 185
PW = 150
DIVE = [6, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1]
ARCH = 2
CONTENT = 132
LX, RX = LP + 9, GX + 9
RW = 7
CHART_W, CHART_H = 115, 75            # odd, so a star's centre pixel can sit on the chart's centre
MAX_LEAVES = 5
TAB_SLOT = {"l": [GX - 96 + 12 * i for i in range(4)], "r": [GX + 53 + 12 * i for i in range(4)]}
TAB_Y, RUN_Y = 6, 6

ATLAS_W = ATLAS_H = 512
REG, AT = {}, {}                      # name -> (u, v, w, h); name -> where it goes on the spread, if fixed


def dip(d):
    dive = DIVE[d] if d < len(DIVE) else 0
    arch = int(math.floor(ARCH * math.sin(math.pi * min(d, PW) / PW) + 0.5))
    return ARCH + dive - arch


def col_d(x):
    return (GX - 1 - x, "l") if x < GX else (x - GX, "r")


def page_top(x):
    return TOP - ARCH + dip(col_d(x)[0])


def page_bot(x):
    return BOT + ARCH - dip(col_d(x)[0])


# ================================================================================================ the wrap
def board_mask():
    cut = [4, 2, 1, 1]
    m = set()
    for y in range(BY, BY + BH):
        for x in range(BX, BX + BW):
            dy, dx = min(y - BY, BY + BH - 1 - y), min(x - BX, BX + BW - 1 - x)
            if dy < 4 and dx < cut[dy]:
                continue
            m.add((x, y))
    return m


NAP = [(1, 30, 3, 3), (3, 41, 2, 0), (2, 55, 4, 3), (4, 63, 2, 3), (1, 78, 2, 0), (3, 90, 3, 3), (2, 104, 2, 0),
       (4, 117, 4, 3), (1, 131, 3, 3), (3, 143, 2, 0), (2, 158, 3, 3), (4, 170, 2, 0), (1, 183, 3, 3), (3, 195, 2, 3)]


def wrap(c):
    """The buckskin wrap from its flesh side: outline, a 3-px hem (grain side turned over, lit top-left), the lace
    whipstitched over the edge through punched holes, the rough inside with its nap, creases at the spine."""
    m = board_mask()
    left, e = set(m), {}
    for k in range(5):
        edge = {p for p in left if any((p[0] + dx, p[1] + dy) not in left
                                       for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
        for p in edge:
            e[p] = k
        left -= edge
    x1, y1 = BX + BW - 1, BY + BH - 1
    for (x, y) in m:
        k = e.get((x, y), 5)
        tl = (y - BY == k) or (x - BX == k)
        if k == 0:
            col = HIDE[0]
        elif k == 1:
            col = HIDE[5] if tl else HIDE[2]
        elif k == 2:
            col = HIDE[4] if tl else HIDE[3]
        elif k == 3:
            col = HIDE[1] if tl else HIDE[4]
        elif k == 4:
            col = FLESH[0] if tl else FLESH[2]
        else:
            col = FLESH[1]
        c.p(x, y, col)
    for dx, y, n, t in NAP:                                   # the nap of the rough side, hand-placed
        c.vl(BX + 5 + dx, y, y + n - 1, FLESH[t])
        c.vl(x1 - 5 - dx, y + 7, y + 7 + n - 1, FLESH[t])
    # the lace, top and bottom: the left board every 6 px from 7 px in, the right board its mirror image (it ran on
    # from the left 8 px in, so the right corners' last stitch sat 7 px in; 7 everywhere lets the sides match too)
    left_x = [x for x in range(BX + 7, GX, 6) if abs(x + 2 - GX) >= 9]
    for x in left_x + [BX + x1 - (x + 4) for x in left_x]:
        c.p(x, BY, LACE[2])
        c.hl(x, x + 1, BY + 1, LACE[3])
        c.hl(x + 1, x + 2, BY + 2, LACE[2])
        c.hl(x + 2, x + 3, BY + 3, LACE[1])
        c.p(x + 4, BY + 4, HIDE[0])
        c.p(x, y1 - 4, HIDE[0])
        c.hl(x + 1, x + 2, y1 - 3, LACE[3])
        c.hl(x + 2, x + 3, y1 - 2, LACE[2])
        c.hl(x + 3, x + 4, y1 - 1, LACE[1])
        c.p(x + 4, y1, LACE[0])
    for y in [BY + s for s in dash_starts(BH, 5, 1, 7)]:     # and the sides, 7 px in at both ends like the top and
        c.p(BX, y, LACE[2])                                   # foot (the strap covers part of the right)
        c.vl(BX + 1, y, y + 1, LACE[3])
        c.vl(BX + 2, y + 1, y + 2, LACE[2])
        c.vl(BX + 3, y + 2, y + 3, LACE[1])
        c.p(BX + 4, y + 4, HIDE[0])
        if not 96 <= y <= 132:
            c.p(x1 - 4, y, HIDE[0])
            c.vl(x1 - 3, y + 1, y + 2, LACE[3])
            c.vl(x1 - 2, y + 2, y + 3, LACE[2])
            c.vl(x1 - 1, y + 3, y + 4, LACE[1])
            c.p(x1, y + 4, LACE[0])
    for yy in (BY + 1, BY + 2, BY + 3, y1 - 3, y1 - 2, y1 - 1):   # the fold at the spine: two creases in the hem
        c.p(GX - 3, yy, HIDE[1])
        c.p(GX - 2, yy, HIDE[5])
        c.p(GX + 1, yy, HIDE[1])
        c.p(GX + 2, yy, HIDE[5])


FRINGE = [8, 10, 7, 9, 10, 8, 6, 9, 10, 7, 9, 8, 10, 9, 7, 10, 8]
FRINGE_CURL = {3, 8, 14}


def fringe(c):
    """A fringe band sewn under the foot: a 3-row strip with its stitches, then strands cut from it, each 2 px wide
    and lit on its left, lengths from a hand-made list, a few curling at the tip; parted where the ribbon hangs."""
    y0 = BY + BH
    x0, x1 = BX + 5, BX + BW - 6
    for x in range(x0, x1 + 1):
        c.p(x, y0, HIDE[1])
        c.p(x, y0 + 1, HIDE[3])
        c.p(x, y0 + 2, HIDE[2])
    c.p(x0, y0, CLEAR)
    c.p(x1, y0, CLEAR)
    c.vl(x0, y0 + 1, y0 + 2, HIDE[0])
    c.vl(x1, y0 + 1, y0 + 2, HIDE[0])
    for x in [x0 + 1 + s for s in dash_starts(x1 - x0 - 1, 3, 2, 2)]:   # 3 px from each end (were 3 and 4)
        c.hl(x, x + 1, y0 + 1, LACE[3])
        c.p(x + 2, y0 + 1, LACE[1])
    k = 0
    for x in range(x0 + 1, x1 - 1, 3):
        n = FRINGE[k % len(FRINGE)]
        curl = (k % len(FRINGE)) in FRINGE_CURL
        k += 1
        if GX - 6 <= x <= GX + 5:
            continue
        ys = y0 + 3
        for j in range(n):
            sx = x + (1 if curl and j >= n - 3 else 0)
            c.p(sx, ys + j, HIDE[4] if j else HIDE[2])
            if j < n - 1:
                c.p(sx + 1, ys + j, HIDE[2] if j else HIDE[1])
        c.p(x + (1 if curl else 0), ys + n - 1, HIDE[3])


STRAP_W = [9, 12, 14, 15, 16, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 17, 17, 16,
           15, 14, 12, 9]
LACE_DX = [0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2]


def strap(c):
    """The closing strap from the back board: a rounded tongue of buckskin, stitched round its edge, a punched hole
    near its end with the lace through it, hanging down to a carved bone toggle."""
    x0, cy = BX + BW, BY + 97
    m = set()
    for j, wd in enumerate(STRAP_W):
        for i in range(wd):
            m.add((x0 + i, cy - 15 + j))
    for (x, y) in m:
        open_dn = (x, y + 1) not in m or (x + 1, y) not in m
        open_up = (x, y - 1) not in m
        j = y - (cy - 15)
        if open_dn or open_up:
            col = HIDE[0]
        elif (x, y - 2) not in m:
            col = HIDE[5]
        elif j >= 22:
            col = HIDE[2]
        elif j >= 12:
            col = HIDE[3]
        else:
            col = HIDE[4]
        c.p(x, y, col)
    for (x, y) in m:                                           # a stitch line 3 px inside the edge
        near = [(dx, dy) for dx in (-3, 0, 3) for dy in (-3, 0, 3) if (x + dx, y + dy) not in m]
        far = any((x + dx, y + dy) not in m for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2))
        if near and not far and x > x0 + 2 and (x + y) % 4 == 0:
            c.p(x, y, LACE[1])
            c.p(x - 1, y, HIDE[5])
    c.vl(x0, cy - 13, cy + 13, HIDE[1])                        # in the board's shadow
    hx, hy = x0 + 12, cy - 1
    c.fill(hx, hy, hx + 2, hy + 2, HIDE[0])
    c.p(hx - 1, hy, HIDE[5])
    for k, dx in enumerate(LACE_DX):
        y = hy + 1 + k
        c.p(hx + dx, y, LACE[3])
        c.p(hx + dx + 1, y, LACE[1])
        if (hx + dx + 2, y) in m:
            c.p(hx + dx + 2, y, HIDE[2])
    tx, ty = hx - 2, hy + 1 + len(LACE_DX)
    c.art(tx, ty, [".aaaaaaa.",
                   "adccLLcba",
                   "abbbllbba",
                   ".aaaaaaa."], {"a": BONE[0], "b": BONE[1], "c": BONE[2], "d": BONE[3], "L": LACE[2], "l": LACE[0]})


# ================================================================================================ the page block
FIBRE = [(12, 7, 3), (47, 5, 2), (88, 9, 4), (126, 6, 2), (30, 15, 2), (66, 17, 3), (108, 14, 2), (139, 19, 3),
         (9, 26, 4), (52, 24, 2), (81, 29, 2), (119, 27, 3), (24, 36, 3), (70, 38, 2), (97, 34, 4), (135, 39, 2),
         (14, 47, 2), (43, 45, 3), (86, 49, 2), (112, 46, 2), (33, 57, 4), (61, 55, 2), (101, 59, 3), (131, 56, 2),
         (8, 66, 2), (49, 68, 3), (77, 64, 2), (121, 69, 4), (21, 77, 3), (58, 75, 2), (93, 79, 2), (138, 76, 3),
         (36, 86, 2), (72, 88, 4), (106, 85, 2), (127, 89, 2), (11, 96, 3), (45, 94, 2), (84, 98, 3), (116, 95, 2),
         (27, 106, 2), (63, 108, 3), (99, 104, 2), (134, 109, 4), (16, 116, 4), (51, 114, 2), (79, 118, 2),
         (109, 115, 3), (38, 126, 2), (68, 128, 3), (95, 124, 2), (129, 129, 2), (7, 136, 3), (44, 134, 2),
         (87, 138, 4), (118, 135, 2), (25, 146, 2), (59, 148, 3), (103, 144, 2), (137, 149, 3), (13, 156, 3),
         (48, 154, 2), (74, 158, 2), (113, 155, 4), (34, 166, 2), (90, 168, 3), (125, 164, 2)]
AGE_TOP = [1, 1, 2, 2, 1, 0, 1, 1, 2, 3, 2, 1, 1, 0, 0, 1, 2, 2, 1, 1, 0, 1, 1, 2, 1, 0, 1, 2, 3, 3, 2, 1, 1, 0, 1, 1, 2]
AGE_SIDE = [1, 2, 2, 1, 1, 0, 1, 2, 3, 2, 2, 1, 0, 0, 1, 1, 2, 1, 1, 0, 1, 2, 2, 3, 2, 1, 1, 0, 1, 1, 1, 2, 1, 0, 0, 1,
            2, 2, 1, 1, 2]
STITCH_Y = [TOP + 13 + i * 34 for i in range(5)]
STITCH_LEN = 18
HOLE = rgb((78, 50, 30))
SPINE = [rgb((38, 20, 12)), HIDE[0]]


def pages(c):
    """Both page faces. Light from the top left: the left page falls away into a broad stepped shadow at the gutter,
    the right page rises out of a narrow one. Edges are aged a tone darker in an uneven band; pale fibres lie in the
    paper (a hand-made table, the same on every run)."""
    for x in range(LP, RP):
        d, side = col_d(x)
        t, b = page_top(x), page_bot(x)
        fore = (x - LP) if side == "l" else (RP - 1 - x)
        for y in range(t, b):
            if y == t or y == b - 1 or fore == 0:
                col = SEPIA_OUT
            else:
                k = 3
                if y - t <= 1 + AGE_TOP[(x * 3 + 5) % len(AGE_TOP)] // 2 or b - 1 - y <= 1 + AGE_TOP[x % len(AGE_TOP)]:
                    k = 2
                if fore <= 1 + AGE_SIDE[(y + (9 if side == "r" else 0)) % len(AGE_SIDE)]:
                    k = 2
                if side == "l":
                    g = 0 if d <= 1 else 1 if d <= 4 else 2 if d <= 9 else 3
                else:
                    g = 0 if d == 0 else 1 if d <= 2 else 2 if d <= 5 else 3
                k = min(k, g)
                if y == t + 1 and k == 3:
                    k = 4                                       # the top edge catches the light
                if fore == 1 and side == "l" and k >= 2:
                    k = 4
                col = SEPIA[k]
            c.p(x, y, col)
    for side, x0 in (("l", LP), ("r", GX)):
        for i, (fx, fy, n) in enumerate(FIBRE):
            if side == "r":
                fx, fy = (fx * 7 + 31) % 136 + 7, (fy + 81) % 170 + 4
            for j in range(n):
                x, y = x0 + fx + j, TOP + fy
                if c.get(x, y) == SEPIA[3]:
                    c.p(x, y, SEPIA[4])
            if i % 5 == 0 and c.get(x0 + fx + 1, TOP + fy + 1) == SEPIA[3]:
                c.p(x0 + fx + 1, TOP + fy + 1, SEPIA[4])


def spine(c):
    """The notches at head and foot with the head- and tailband, the foot's leaf edges and the page block's shadow,
    and the long-stitches down the valley."""
    for x in range(LP, RP):
        d, side = col_d(x)
        b = page_bot(x)
        c.p(x, b, SEPIA[1] if (x // 7) % 3 else SEPIA[3])       # two leaf edges under the foot
        c.p(x, b + 1, SEPIA_OUT)
        if d > 10:
            c.p(x, b + 2, HIDE[0] if side == "r" or d > 60 else FLESH[0])
        else:
            for y in range(BY + 5, page_top(x)):
                c.p(x, y, SPINE[0] if d <= 5 else SPINE[1])
            for y in range(b + 2, BY + BH - 4):
                c.p(x, y, SPINE[0] if d <= 5 else SPINE[1])
    band = {"o": BRAND[0], "r": BRAND[1], "R": BRAND[2], "t": THREAD[0], "c": THREAD[1], "C": THREAD[2]}
    rows = ["RRCCRRCC", "rrccrrcc", "rrccrrcc", "ootTootT".replace("T", "t")]
    c.art(GX - 4, BY + 5, rows, band)
    c.art(GX - 4, BY + BH - 9, rows, band)
    for y in range(page_top(GX), page_bot(GX)):                # the valley
        c.p(GX - 1, y, SEPIA_OUT)
        c.p(GX, y, SEPIA[0])
    for y0 in STITCH_Y:
        c.hl(GX - 1, GX, y0 - 1, HOLE)
        c.hl(GX - 1, GX, y0 + STITCH_LEN, HOLE)
        c.vl(GX - 1, y0, y0 + STITCH_LEN - 1, THREAD[2])
        c.vl(GX, y0, y0 + STITCH_LEN - 1, THREAD[1])
        c.p(GX - 1, y0 + STITCH_LEN - 1, THREAD[1])
        c.p(GX, y0 + STITCH_LEN - 1, THREAD[0])
    c.vl(RP, page_top(RP - 1) + 1, page_bot(RP - 1) + 1, HIDE[0])   # the block's shadow on the wrap


def base():
    c = Cv(W, H)
    wrap(c)
    strap(c)
    fringe(c)
    pages(c)
    spine(c)
    return c


# ---- the stack of leaves, per depth
JOG = {1: [(60, 74)], 2: [(120, 150)], 3: [(40, 52), (160, 170)], 4: [(90, 110)], 5: [(30, 44), (130, 142)]}
DECKLE = [(34, 37), (52, 53), (71, 76), (98, 99), (117, 121), (140, 141), (156, 160), (181, 183)]


def leaves(b, side, k):
    """The fore-edge with k more leaves under the page: each leaf a 1-px strip, alternately light and dark, a little
    shorter the deeper it lies, some sitting proud for a stretch; the top leaf's edge is deckled."""
    c = b.copy()
    sgn = -1 if side == "l" else 1
    px = LP if side == "l" else RP - 1                          # the page's own edge column
    t0, b0 = page_top(px), page_bot(px) + 1                     # the stack runs to the foot's leaf edges
    for i in range(1, k + 1):
        x = px + sgn * i
        t, bt = t0 + i // 2, b0 - i // 2
        tone = (SEPIA[4] if i % 2 else SEPIA[1]) if side == "l" else (SEPIA[2] if i % 2 else SEPIA[0])
        for y in range(t, bt + 1):
            col = tone
            for (a, z) in JOG.get(i, []):
                yy = y - TOP + (0 if side == "l" else 11)
                if a <= yy <= z:
                    col = SEPIA[4] if side == "l" else SEPIA[3]
                    if yy in (a, z):
                        col = SEPIA[0]
            c.p(x, y, col)
        c.p(x, t, SEPIA_OUT)
        c.p(x, bt, SEPIA_OUT)
    if k:
        x = px + sgn * (k + 1)
        c.vl(x, t0 + (k + 1) // 2, b0 - (k + 1) // 2, SEPIA_OUT)
        if side == "r" and k < MAX_LEAVES:
            c.vl(x + 1, t0 + (k + 1) // 2 + 1, b0 - (k + 1) // 2 + 1, HIDE[0])
    for (a, z) in DECKLE:
        for yy in range(a, z + 1):
            y = TOP + yy + (0 if side == "l" else 6)
            c.p(px, y, SEPIA[1] if k else (FLESH[0] if side == "l" else HIDE[0]))
            c.p(px - sgn, y, SEPIA_OUT)
    x0 = LP - 6 if side == "l" else RP - 2
    return c.crop(x0, BY + 4, 8, 187), (x0, BY + 4)


# ---- the folded corners
def corner(b, side):
    """A bottom outer corner folded in along a diagonal crease, the way vanilla's book has it: the flap is the leaf's
    pale back, its tip a little short of flat and rounded; the crease is a soft tan line with darker dots; where the
    corner was, the leaf below shows, with the stack's edges along its two sides. No ink outline."""
    n, s = 9, 12
    cv = Cv(s, s)
    for y in range(s):
        for x in range(s):
            u = x                                               # distance from the fore-edge
            v = s - 1 - y                                       # distance from the foot
            if u + v < n:                                       # where the corner was: the leaf below
                col = SEPIA[2]
                if u == 0 or v == 0:
                    col = SEPIA_OUT
                elif u == 1 or v == 1:
                    col = SEPIA[4]
                elif u == 2 or v == 2:
                    col = SEPIA[1]
                elif u + v >= n - 2:
                    col = SEPIA[1]                              # in the flap's shadow
            elif u <= n and v <= n and not (u + v > 2 * n - 3):  # the flap (its tip cut short and rounded)
                col = FLAP_HI
                if u + v == n:
                    col = SEPIA[1] if (u % 3) else SEPIA[0]     # the crease
                elif u + v == n + 1:
                    col = SEPIA[4]
                elif u == n or v == n:
                    col = SEPIA[4]
            else:
                col = None
                if (u == n + 1 and v <= n - 1) or (v == n + 1 and 1 <= u <= n - 1) or (u == n and v == n - 1) \
                        or (u == n - 1 and v == n):
                    col = SEPIA[2]                              # the flap's shadow on the page
            if col is not None:
                cv.p(x, y, col)
    if side == "r":
        cv = cv.flip_h()
    x0 = LP if side == "l" else RP - s
    full = b.crop(x0, BOT - s, s, s)
    full.paste(cv, 0, 0)
    return full, (x0, BOT - s)


ARROW = ["..xxxxxxxx....x.....",
         ".xxo.....x....xx....",
         ".xx...........xxx...",
         ".xx...........xxxx..",
         ".xxxxxxxxxxxxxxxxxx.",
         ".oxxxxxxxxxxxxxxxxx.",
         "..............xxxx..",
         "..............xxx...",
         "..............xx....",
         "..............x....."]


def arrow(side, hover):
    """The page-turn arrow, inked: a hooked shaft two pixels thick and a solid head; brand red under the mouse."""
    pal = {"x": BRAND[1], "o": BRAND[2]} if hover else {"x": INKB[0], "o": INKB[2]}
    cv = trimmed(sprite(ARROW, pal))
    return cv if side == "r" else cv.flip_h()


# ================================================================================================ ribbons
MARKS = {"constellations": ["..x..", "..x..", "xx.xx", "..x..", "..x.."],
         "planets": [".xxx.", "x...x", "x.x.x", "x...x", ".xxx."],
         "rare": ["..x..", ".x.x.", "x...x", ".x.x.", "..x.."],
         "fallen": ["....x", "...x.", "xxx..", "xxx..", "xxx.."],
         "notes": ["...xx", "..x.x", ".x.x.", "xxx..", "x...."],       # a quill
         "recipes": ["xxxx.", "x..x.", "x..xx", "x...x", "x.x.x"]}      # a page torn at the foot
SILK = [0, 3, 2, 2, 2, 1, 0]


def silk_row(c, x, y, r, shift=0, cols=range(7)):
    for i in cols:
        k = SILK[i]
        if 0 < i < 6:
            k = max(1, min(4, k + shift))
        c.p(x + i, y, r[k])


def swallow(c, x, y, r, up):
    """A swallow-tail cut into three rows ending at y (the very end)."""
    for j, gap in enumerate((5, 3, 1)):
        yy = y + j if up else y - j
        lo = (7 - gap) // 2
        for i in range(lo, lo + gap):
            c.p(x + i, yy, CLEAR)
        c.p(x + lo - 1, yy, r[0])
        c.p(x + lo + gap, yy, r[0])
    c.p(x + 3, y + 3 if up else y - 3, r[0])


def mark(c, x, y, s):
    r = RIBBONS[s]
    for j, row in enumerate(MARKS[s]):
        for i, ch in enumerate(row):
            if ch == "x":
                c.p(x + 1 + i, y + j, THREAD[2])


def tab(s):
    """A closed section's ribbon: a short silk tab out of the head, swallow-tailed, its mark stitched in linen."""
    r = RIBBONS[s]
    h = BY + 5 - TAB_Y                                          # down to the page tops
    c = Cv(RW, h)
    for y in range(h):
        silk_row(c, 0, y, r, shift=-1 if y >= h - 3 else 0)
    swallow(c, 0, 0, r, True)
    mark(c, 0, 5, s)
    c.p(1, 12, r[4])
    c.p(2, 11, r[4])
    return c


GLINT_Y = [44, 79, 117, 151, 186]


def run(s):
    """The open section's ribbon, its whole length painted: out of the head at the spine with its mark, down the
    valley over the long-stitches (a light row where it climbs each, a dark row where it drops off), glints where the
    silk catches the light, its shadow on the right-hand page, over the hem and the fringe band, and a hanging
    swallow-tail with one soft fold."""
    r = RIBBONS[s]
    y_end = 232
    c = Cv(RW + 1, y_end - RUN_Y + 1)
    for y in range(RUN_Y, y_end + 1):
        shift = 0
        if page_top(GX) - 4 <= y < page_top(GX) + 2 or page_bot(GX) - 2 <= y < page_bot(GX) + 3:
            shift = -1                                          # diving into the notch, climbing out of it
        for y0 in STITCH_Y:
            if y == y0 - 1:
                shift = 1
            if y == y0 + STITCH_LEN:
                shift = -1
        if y == BY + BH - 1:
            shift = 1                                           # bent over the wrap's edge
        if y in (BY + BH, BY + BH + 1, 223):
            shift = -1
        if y == 222:
            shift = 1
        silk_row(c, 0, y - RUN_Y, r, shift)
        if page_top(GX) + 1 <= y < page_bot(GX) - 1:
            c.p(RW, y - RUN_Y, SEPIA[0])                        # its shadow on the right page
    for gy in GLINT_Y:
        for i in range(3):
            c.p(4 - i, gy - RUN_Y + i, r[4])
        c.p(2, gy - RUN_Y, r[3])
    swallow(c, 0, 0, r, True)
    swallow(c, 0, y_end - RUN_Y, r, False)
    mark(c, 0, 5, s)
    return c


# ================================================================================================ pasted pictures
BRUSH_L = [0, 1, 1, 2, 1, 0, -1, 0, 1, 2, 2, 1, 0, 0, 1, -1, 0, 1, 1, 2, 1, 0, 0, -1, 0, 1, 2, 1, 1, 0, 1, 2, 2, 1, 0]
BRUSH_R = [1, 2, 1, 0, 0, 1, 2, 2, 1, 0, -1, 0, 1, 1, 2, 1, 0, 1, 2, 2, 1, 0, 0, 1, -1, 0, 1, 2, 1, 0, 1]
STREAKS = [(6, 3, 30, 3), (50, 2, 22, 1), (84, 4, 24, 3), (2, 9, 14, 1), (96, 10, 16, 3), (10, 16, 9, 3),
           (100, 20, 12, 1), (3, 27, 8, 3), (104, 31, 9, 3), (5, 38, 7, 1), (101, 42, 11, 1), (4, 49, 10, 3),
           (98, 53, 13, 3), (2, 58, 12, 1), (92, 61, 18, 1), (8, 66, 26, 3), (60, 68, 30, 1), (14, 71, 40, 1),
           (70, 72, 34, 3), (30, 6, 12, 1), (40, 69, 10, 3), (22, 12, 8, 1)]


def card(w, h):
    """A print pasted on the page: warm card, lit top-left, with a 1-px shadow on the page to its right and below."""
    c = Cv(w + 1, h + 1)
    c.fill(0, 0, w, h, CARD[0])
    c.fill(1, 1, w - 1, h - 1, CARD[2])
    c.hl(1, w - 2, 1, CARD[3])
    c.vl(1, 1, h - 2, CARD[3])
    c.hl(2, w - 2, h - 2, CARD[1])
    c.vl(w - 2, 2, h - 2, CARD[1])
    c.vl(w, 2, h, SEPIA[1])
    c.hl(2, w, h, SEPIA[1])
    return c


def cyanotype():
    """A cyanotype: Prussian blue brushed across the card in strokes that run past the picture's edge on one row and
    stop short on the next, thin and streaky in places, pooled dark along the foot, two small misses in the coat.
    The middle is kept calm for the stars (drawn 1:1 by the code from chart_points)."""
    w, h, m = CHART_W + 8, CHART_H + 8, 4
    c = card(w, h)
    for j in range(CHART_H):
        l, r_ = BRUSH_L[j % len(BRUSH_L)], BRUSH_R[(j * 2 + 3) % len(BRUSH_R)]
        x0, x1 = m - l, m + CHART_W - 1 + r_
        c.hl(x0, x1, m + j, CYAN[2])
        c.p(x0, m + j, CYAN[3])
        c.p(x1, m + j, CYAN[1])
    c.hl(m + 1, m + CHART_W - 2, m, CYAN[3])
    c.hl(m, m + CHART_W - 1, m + CHART_H - 1, CYAN[1])
    c.hl(m + 3, m + CHART_W - 9, m + CHART_H - 2, CYAN[1])
    for x, y, n, t in STREAKS:
        c.hl(m + x, m + x + n - 1, m + y, CYAN[t])
    for x, y in ((113, 0), (114, 0), (114, 1), (112, 0), (0, 73), (0, 74), (1, 74), (0, 72)):
        c.p(m + x, m + y, CARD[2])
    return c


PLATE_STARS = [(4, 5, 1), (9, 2, 0), (2, 12, 0), (-5, 3, 1), (-9, 7, 0), (-3, 13, 0), (3, -6, 0), (8, -3, 1),
               (-4, -4, 0), (-10, -8, 1), (-2, -12, 0), (13, 4, 0)]
PLATE_NICKS = [(0, 7), (0, 8), (-1, 21), (17, 0), (18, 0), (-13, -1), (31, -1), (-1, -16)]


def plate(inner):
    """A glass-plate photograph: a square of night with a pale card border, the emulsion nicked at its edge here and
    there, a few faint stars in the corners; the planet or the nebula is drawn in the middle, 1:1."""
    b = 3
    w = inner + 2 * b
    c = card(w, w)
    c.fill(b - 1, b - 1, w - b + 1, w - b + 1, CARD[1])
    c.fill(b, b, w - b, w - b, NIGHT[1])
    mid = (w - 1) / 2
    for y in range(b, w - b):
        for x in range(b, w - b):
            if math.hypot(x - mid, y - mid) > inner * 0.66:
                c.p(x, y, NIGHT[0])
    for x, y, t in PLATE_STARS:
        c.p(b + (x if x >= 0 else inner + x), b + (y if y >= 0 else inner + y), STARLIGHT[t])
    for x, y in PLATE_NICKS:
        c.p(b + (x if x >= 0 else inner + x), b + (y if y >= 0 else inner + y), CARD[1])
    return c


def photo_corner(which, pencil=False):
    """A photo corner, 9 px: a triangle of saddle leather with a slit line, bevelled by the light; or its outline in
    pencil where a picture is still to come."""
    n = 9
    c = Cv(n, n)
    m = {(x, y) for y in range(n) for x in range(n) if x + y < n}
    slit = {(x, y) for (x, y) in m if x + y == n - 4 and 1 <= x and 1 <= y}
    if "r" in which:
        m = {(n - 1 - x, y) for (x, y) in m}
        slit = {(n - 1 - x, y) for (x, y) in slit}
    if "b" in which:
        m = {(x, n - 1 - y) for (x, y) in m}
        slit = {(x, n - 1 - y) for (x, y) in slit}
    for (x, y) in m:
        up = (x, y - 1) not in m or (x - 1, y) not in m
        dn = (x, y + 1) not in m or (x + 1, y) not in m
        if pencil:
            if up or dn:
                c.p(x, y, PENCIL[0] if (x + y) % 4 else PENCIL[1])
            continue
        c.p(x, y, LEATHER[0] if dn else LEATHER[4] if up else LEATHER[1] if (x, y) in slit else LEATHER[2])
        if not up and not dn and (x - 1, y - 1) in slit:
            c.p(x, y, LEATHER[3])
    return c


QMARK = [".xxx.", "x...x", "....x", "...x.", "..x..", ".....", "..x.."]


def dashed_ring(c, cx, cy, r, col, step=20, th=0.75):
    """2 on 1 off by angle. 360 / step must divide by 3 so the ring closes on the pattern (step 18 gave 20 steps:
    two dashes ran together into one long dash where the ring closed)."""
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if abs(math.hypot(dx, dy) - r) <= th / 2 + 0.2:
                a = math.degrees(math.atan2(dy, dx)) % 360
                if int(a // step) % 3 != 2:
                    c.p(x, y, col)


def sketch(size, kind):
    """What isn't found yet, in pencil: a dashed circle (a planet), a dashed swirl (a rare sight), and a '?'."""
    c = Cv(size, size)
    m = size / 2
    if kind == "rare":
        for i in range(0, 300):
            a = math.radians(i * 2.2)
            r = 4 + i * (m - 7) / 300
            if (i // 9) % 3 != 2:
                c.p(int(m + math.cos(a) * r), int(m + math.sin(a) * r * 0.8), PENCIL[1] if i % 2 else PENCIL[0])
    else:
        dashed_ring(c, m, m, m - 1.5, PENCIL[0])
    c.fill(size // 2 - 4, size // 2 - 5, size // 2 + 5, size // 2 + 6, CLEAR)
    c.art(size // 2 - 2, size // 2 - 3, QMARK, {"x": PENCIL[0]})
    return c


COMET_REACH = [30, 34, 38, 41, 44, 46, 44, 45, 42, 39, 40, 36, 31, 27, 22]


def comet_picture():
    """The Wanderer's Comet for its plate: a bright head low on the left and a tail streaming up to the right,
    brightest along its spine, in stepped cold tones, each strand ending at its own hand-picked length. No outline."""
    c = Cv(63, 63)
    hx, hy = 14.5, 47.5
    ax, ay = math.cos(math.radians(-36)), math.sin(math.radians(-36))
    faint = mix(NIGHT[1], STARLIGHT[0], 0.5)
    for y in range(63):
        for x in range(63):
            dx, dy = x + 0.5 - hx, y + 0.5 - hy
            t = dx * ax + dy * ay
            s = -dx * ay + dy * ax
            if t < 0:
                continue
            half = 1.5 + t * 0.13
            if abs(s) > half:
                continue
            strand = int(round(s + 7))
            reach = COMET_REACH[max(0, min(len(COMET_REACH) - 1, strand))]
            if t > reach:
                continue
            e = abs(s) / half
            left = t / reach
            k = 3 if (left < 0.22 and e < 0.55) else 2 if (left < 0.5 and e < 0.6) else 1 if (left < 0.8 and e < 0.85) else 0
            c.p(x, y, [faint, STARLIGHT[0], STARLIGHT[1], STARLIGHT[2]][k])
    c.art(12, 45, [".bcb.", "bcdcb", "cdddc", "bcdcb", ".bcb."],
          {"b": STARLIGHT[2], "c": STARLIGHT[3], "d": STARLIGHT[4]})
    for x, y, t in ((50, 50, 1), (8, 12, 0), (30, 56, 0), (22, 20, 0), (58, 30, 0)):
        c.p(x, y, STARLIGHT[t])
    return c


def shower_picture():
    """'Wish upon a Star' for its plate: five meteors falling the same way from one corner, each a bright head and
    a stepped tail of its own length."""
    c = Cv(63, 63)
    for (x, y, n) in ((44, 6, 16), (26, 10, 22), (52, 24, 12), (12, 26, 14), (34, 34, 20)):
        for i in range(n):
            f = i / n
            col = STARLIGHT[3] if f < 0.15 else STARLIGHT[2] if f < 0.35 else STARLIGHT[1] if f < 0.6 else \
                STARLIGHT[0] if f < 0.85 else mix(NIGHT[1], STARLIGHT[0], 0.45)
            px, py = x - 2 - i + n, y + n - 1 - i
            c.p(px, py, col)
            if f < 0.3:
                c.p(px - 1, py, col)
        hx, hy = x - 3, y + n
        c.art(hx - 1, hy - 1, [".c.", "cdc", ".c."], {"c": STARLIGHT[3], "d": STARLIGHT[4]})
    for x, y, t in ((6, 6, 1), (58, 50, 0), (20, 56, 1), (48, 46, 0), (8, 48, 0), (57, 12, 0)):
        c.p(x, y, STARLIGHT[t])
    return c


def chart_star(m, pencil=False):
    """Chart stars by magnitude (1 brightest): pale cyan on the print, pencil rings where it isn't found."""
    if pencil:
        rows = {1: [".xxx.", "x...x", "x...x", "x...x", ".xxx."], 2: [".x.", "xxx", ".x."]}.get(m, [".x.", "x.x", ".x."])
        return sprite(rows, {"x": PENCIL[0]})
    rows = {1: ["..a..", ".aba.", "abbba", ".aba.", "..a.."], 2: [".a.", "aba", ".a."]}.get(m, ["a"])
    return sprite(rows, {"a": CYAN[4], "b": CYAN[5]})


# ================================================================================================ marks and awards
BRAND_WORN = [(2, 3), (3, 2), (11, 12), (12, 11), (12, 4), (7, 14)]


def brand():
    """The Circle Star, burnt in: a heavy ring round a solid five-point star, darker where the iron sat longest
    (lower right), worn through at a few chosen spots."""
    c = Cv(15, 15)
    for y in range(15):
        for x in range(15):
            dx, dy = x - 7, y - 7
            d = math.hypot(dx, dy)
            if 5.4 < d <= 7.3:
                c.p(x, y, BRAND[0] if dx + dy > 5 else BRAND[1])
    for (x, y) in poly_mask(star_points(7.5, 7.9, 4.7, 1.9)):
        c.p(x, y, BRAND[1])
    c.p(7, 7, BRAND[0])
    c.p(7, 8, BRAND[0])
    for x, y in BRAND_WORN:
        if c.solid(x, y):
            c.p(x, y, BRAND[2])
    return c


def tin_star(earned):
    """A tin star: five points, each split by a ridge into a lit and a shaded facet, balls on the tips, a domed boss.
    Not earned: the same shape pencilled on the page with two pin-holes, solid, dimmed by colour."""
    s = 25
    c = Cv(s, s)
    cx = cy = s / 2
    m = poly_mask(star_points(cx, cy, 9.2, 4.0))
    tips = star_points(cx, cy, 9.0, 4.0)[::2]
    for (tx, ty) in tips:
        for y in range(s):
            for x in range(s):
                if math.hypot(x + 0.5 - tx, y + 0.5 - ty) <= 1.6:
                    m.add((x, y))
    for (x, y) in m:
        edge = any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if not earned:
            if edge:
                c.p(x, y, PENCIL[0] if (x + 2 * y) % 5 else PENCIL[1])
            continue
        if edge:
            c.p(x, y, TIN[0])
            continue
        a = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx))
        i = round((a + 90) / 72.0)
        axis = -90 + i * 72
        delta = (a - axis + 180) % 360 - 180
        na = math.radians(axis + (90 if delta > 0 else -90))
        f = math.cos(na) * -0.707 + math.sin(na) * -0.707
        c.p(x, y, TIN[4] if f > 0.5 else TIN[3] if f > 0 else TIN[2] if f > -0.6 else TIN[1])
    if earned:
        for (tx, ty) in tips:
            c.p(int(tx), int(ty), TIN[4])
        for y in range(s):
            for x in range(s):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= 3.0:
                    f = (-(x + 0.5 - cx) - (y + 0.5 - cy)) / 4.2
                    c.p(x, y, TIN[1] if d > 2.1 else TIN[4] if f > 0.3 else TIN[3] if f > -0.3 else TIN[2])
    return trimmed(c)


def tick_box(ticked):
    c = sprite([".xxxxxxxxo",
                "x........x",
                "x........x",
                "x........x",
                "x........x",
                "x........x",
                "x........x",
                "x........x",
                "x........x",
                "oxxxxxxxx."], {"x": INKB[1], "o": INKB[2]})
    if ticked:
        c.art(0, 0, ["..........",
                     "..........",
                     ".......tt.",
                     "......ttT.",
                     ".....ttT..",
                     ".tt.ttT...",
                     ".tTtttT...",
                     "..tttT....",
                     "...tT.....",
                     ".........."], {"t": BRAND[1], "T": BRAND[0]})
    return c


def moon_face(phase):
    """A moon phase in ink, 9 px: an inked rim, the dark part washed in faded ink, the lit part left pale."""
    c = Cv(9, 9)
    for y in range(9):
        for x in range(9):
            dx, dy = x - 4, y - 4
            d = math.hypot(dx, dy)
            if d > 4.4:
                continue
            if d > 3.4:
                c.p(x, y, INKB[1])
            else:
                c.p(x, y, FLAP_HI if moon_is_lit(phase, dx / 3.6, dy / 3.6) else INKB[2])
    return c


def tonight_mark():
    return sprite(["x.......x", "xx.....xx", ".xxxxxxx."], {"x": BRAND[1]})


def compass_rose():
    """A compass rose in ink, 27 px: a thin ring, four long solid points that taper, four short ones between."""
    s = 27
    c = Cv(s, s)
    m = s // 2
    for y in range(s):
        for x in range(s):
            d = math.hypot(x - m, y - m)
            if 7.5 <= d < 8.5:
                c.p(x, y, INKB[2])
    for i in range(3, 6):                                       # the short points on the diagonals
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            c.p(m + sx * i, m + sy * i, INKB[1])
    for i in range(0, 14):                                      # the long points
        hw = 2 if i < 3 else 1 if i < 8 else 0
        for j in range(-hw, hw + 1):
            for (x, y) in ((m + j, m - i), (m - j, m + i), (m + i, m + j), (m - i, m - j)):
                c.p(x, y, INKB[0] if j <= 0 else INKB[1])
    c.fill(m - 1, m - 1, m + 2, m + 2, FLAP_HI)
    c.p(m, m, INKB[0])
    return c


def vignette():
    """The title page's sketch, in ink: a telescope on its tripod on a low rise, a mesa off to the right, a thin
    moon and three stars over it. Drawn with a pen: solid darks, one lighter ink for what is far away."""
    c = Cv(96, 28)
    far, ink = INKB[2], INKB[0]
    for x0, x1 in ((2, 20), (23, 47), (50, 58), (88, 94)):      # the ground, broken like a pen line
        c.hl(x0, x1, 26, INKB[1])
    for x, y in ((6, 25), (7, 24), (8, 25), (44, 25), (45, 24), (53, 25), (54, 24), (55, 25)):
        c.p(x, y, INKB[1])                                      # grass tufts
    for (x0, y0, x1, y1) in ((60, 26, 64, 17), (64, 17, 79, 16), (79, 16, 81, 19), (81, 19, 86, 20), (86, 20, 89, 26)):
        c.line(x0, y0, x1, y1, far)                             # the mesa
    for x, y0, y1 in ((67, 19, 22), (71, 18, 24), (75, 19, 21), (83, 21, 24)):
        c.vl(x, y0, y1, far)
    c.hl(58, 91, 26, far)
    for (x0, y0, x1, y1) in ((30, 15, 25, 26), (31, 15, 31, 26), (32, 15, 37, 26)):   # the tripod
        c.line(x0, y0, x1, y1, ink)
    c.hl(27, 35, 22, INKB[1])
    for i in range(18):                                         # the tube, 3 px thick, pointing up to the right
        x, y = 22 + i, 19 - (i * 10) // 17
        c.vl(x, y - 1, y + 1, ink)
    c.vl(40, 7, 11, ink)
    c.vl(41, 7, 10, ink)
    c.p(21, 20, ink)
    c.p(20, 21, ink)
    c.fill(29, 13, 34, 16, ink)
    c.art(68, 3, [".xx..", "xx...", "xx...", "xx...", ".xx.."], {"x": ink})   # a thin moon
    for (x, y) in ((50, 5), (84, 8), (12, 9)):
        c.art(x - 1, y - 1, [".x.", "xxx", ".x."], {"x": INKB[1]})
    c.p(58, 11, far)
    c.p(30, 3, far)
    c.p(92, 3, far)
    return c


# ---- stains, as their own small sprites (never under writing)
FOX = [[".bb.", "baab", ".bb."], [".b.", "bab", "baa", ".bb"], ["..bb.", ".baab", "baab.", ".bb.."], ["ba", "bb"]]


def fox(i):
    return sprite(FOX[i], {"a": SEPIA[1], "b": SEPIA[2]})


def stain_ring():
    """A ring left by a tin cup: most of a circle, two tones, heavier at the bottom."""
    c = Cv(19, 19)
    for y in range(19):
        for x in range(19):
            dx, dy = x + 0.5 - 9.5, y + 0.5 - 9.5
            d = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 360
            if 7.6 < d <= 9.0 and not (200 < a < 232 or 296 < a < 318):
                c.p(x, y, SEPIA[1] if (30 < a < 150 and d > 8.2) else SEPIA[2])
    return c


# ================================================================================================ lettering
TITLE = {
    "S": ["..xxxxx.x", ".xxxxxxxx", "xxx...xxx", "xxx.....x", "xxxx.....", ".xxxxxx..", "..xxxxxx.", ".....xxxx",
          "x.....xxx", "xxx...xxx", "xxxxxxxx.", "x.xxxxx.."],
    "T": ["xxxxxxxxx", "xxxxxxxxx", "xx.xxx.xx", "x..xxx..x", "...xxx...", "...xxx...", "...xxx...", "...xxx...",
          "...xxx...", "...xxx...", ".xxxxxxx.", ".xxxxxxx."],
    "A": ["....xxx....", "....xxx....", "...xxxxx...", "...x.xxx...", "..xx.xxx...", "..x...xxx..", ".xx...xxx..",
          ".xxxxxxxx..", ".x.....xxx.", "xx.....xxx.", "xxxx..xxxxx", "xxxx..xxxxx"],
    "R": ["xxxxxxxx..", "xxxxxxxxx.", ".xxx..xxxx", ".xxx...xxx", ".xxx..xxxx", ".xxxxxxxx.", ".xxxxxxx..",
          ".xxx.xxx..", ".xxx..xxx.", ".xxx..xxx.", "xxxxx.xxxx", "xxxxx..xxx"],
    "L": ["xxxxx....", "xxxxx....", ".xxx.....", ".xxx.....", ".xxx.....", ".xxx.....", ".xxx.....", ".xxx....x",
          ".xxx...xx", ".xxx..xxx", "xxxxxxxxx", "xxxxxxxxx"],
    " ": ["....."] * 12,
}
SMALL = {
    "C": [".xxxx.", "xx..xx", "xx....", "xx....", "xx....", "xx..xx", ".xxxx."],
    "O": [".xxxx.", "xx..xx", "xx..xx", "xx..xx", "xx..xx", "xx..xx", ".xxxx."],
    "N": ["xx..xx", "xxx.xx", "xxx.xx", "xxxxxx", "xx.xxx", "xx.xxx", "xx..xx"],
    "S": [".xxxx.", "xx..xx", "xx....", ".xxxx.", "....xx", "xx..xx", ".xxxx."],
    "T": ["xxxxxx", "x.xx.x", "..xx..", "..xx..", "..xx..", "..xx..", ".xxxx."],
    "E": ["xxxxxx", ".xx..x", ".xx...", ".xxxx.", ".xx...", ".xx..x", "xxxxxx"],
    "L": ["xxxx..", ".xx...", ".xx...", ".xx...", ".xx...", ".xx..x", "xxxxxx"],
    "A": ["..xx..", ".xxxx.", "xx..xx", "xx..xx", "xxxxxx", "xx..xx", "xx..xx"],
    "I": ["xxxx", ".xx.", ".xx.", ".xx.", ".xx.", ".xx.", "xxxx"],
    "P": ["xxxxx.", ".xx.xx", ".xx.xx", ".xxxx.", ".xx...", ".xx...", "xxxx.."],
    "R": ["xxxxx.", ".xx.xx", ".xx.xx", ".xxxx.", ".xx.xx", ".xx.xx", "xxx.xx"],
    "G": [".xxxx.", "xx..xx", "xx....", "xx.xxx", "xx..xx", "xx..xx", ".xxxx."],
    "H": ["xx..xx", "xx..xx", "xx..xx", "xxxxxx", "xx..xx", "xx..xx", "xx..xx"],
    "F": ["xxxxxx", ".xx..x", ".xx...", ".xxxx.", ".xx...", ".xx...", "xxxx.."],
    "D": ["xxxxx.", ".xx.xx", ".xx.xx", ".xx.xx", ".xx.xx", ".xx.xx", "xxxxx."],
}
HEADINGS = {"constellations": "CONSTELLATIONS", "planets": "PLANETS", "rare": "RARE SIGHTINGS",
            "fallen": "FALLEN STARS", "notes": "FIELD NOTES", "recipes": "FORGOTTEN RECIPES"}


def lettering(text, table, space, col, lo=None):
    """Painted capitals. The width comes out even (so it can centre in an even column): if it would be odd, the
    word space, or failing that the gap after an I, is a pixel wider."""
    def build(sp, igap):
        parts, x = [], 0
        for ch in text:
            if ch == " ":
                x += sp
                continue
            rows = table[ch]
            parts.append((x, rows))
            x += len(rows[0]) + (igap if ch == "I" else 1)
        return parts, x - 1
    parts, w = build(space, 1)
    if w % 2:
        parts, w = build(space + 1, 1) if " " in text else build(space, 2)
    if w % 2:
        raise ValueError("lettering %r has an odd width" % text)
    h = len(table[text[0]])
    c = Cv(w, h)
    for x, rows in parts:
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == "x":
                    c.p(x + i, j, lo if lo is not None and j == h - 1 else col)
    return c


def title_rule(w):
    """The rule under the title: two tapering pen strokes meeting a small solid star."""
    c = Cv(w, 7)
    m = w // 2
    c.hl(4, m - 8, 3, INKB[0])
    c.hl(m + 7, w - 5, 3, INKB[0])
    c.hl(10, m - 8, 4, INKB[1])
    c.hl(m + 7, w - 11, 4, INKB[1])
    c.hl(0, 3, 3, INKB[2])
    c.hl(w - 4, w - 1, 3, INKB[2])
    c.art(m - 4, 0, ["...xx...", "...xx...", "xxxxxxxx", ".xxxxxx.", "..xxxx..", ".xxxxxx.", ".xx..xx."], {"x": INKB[0]})
    return c


def flag(s):
    r = RIBBONS[s]
    return sprite(["ooooo", "ohmso", "ohmso", "ohmso", "ohmso", "oh.so", "o...o"],
                  {"o": r[0], "h": r[3], "m": r[2], "s": r[1]})


# ================================================================================================ the claims ledger
LEDGER_COLS = (31,)                    # the double rule after 'Night'
LEDGER_ROW = 12


def ledger_head():
    c = Cv(CONTENT, 16)
    c.hl(0, CONTENT - 1, 0, INKB[1])
    c.hl(1, CONTENT - 3, 2, INKB[2])
    c.hl(0, CONTENT - 1, 15, INKB[1])
    c.hl(2, CONTENT - 2, 13, INKB[2])
    for y in range(16):
        c.p(LEDGER_COLS[0], y, BRAND[2])
        c.p(LEDGER_COLS[0] + 2, y, BRAND[2])
    return c


def ledger_row():
    c = Cv(CONTENT, LEDGER_ROW)
    for x in range(CONTENT):
        if x not in (40, 41, 97):                               # the pen skipped
            c.p(x, LEDGER_ROW - 1, INK_GHOST)
    for y in range(LEDGER_ROW):
        c.p(LEDGER_COLS[0], y, BRAND[2])
        c.p(LEDGER_COLS[0] + 2, y, BRAND[2])
    return c


# ================================================================================================ a page turning
def turn_frame(b, theta):
    """One frame of a leaf sweeping from the right page to the left (theta 0 = lying right, 180 = lying left),
    painted, not scaled: foreshortened, its free edge rising towards you, the front darkening as it tilts, the pale
    back lit as it comes down, a narrow solid shadow beside it. Returns the frame cropped and where it goes."""
    c = Cv(W, H)
    cs, sn = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    wpx = int(round((PW - 2) * abs(cs)))
    right = cs > 0
    rise, drop, bow = int(round(8 * sn)), int(round(5 * sn)), 2
    y_top0, y_bot0 = page_top(GX) - 1, page_bot(GX)
    cols = {}
    for i in range(wpx + 1):
        f = i / max(1, wpx)
        x = GX + i if right else GX - 1 - i
        t = y_top0 + (TOP - rise - y_top0) * f - bow * math.sin(math.pi * f)
        bt = y_bot0 + (BOT - 1 + drop - y_bot0) * f + bow * 0.5 * math.sin(math.pi * f)
        cols[x] = (int(round(t)), int(round(bt)), f)
    for x, (t, bt, f) in cols.items():
        if right:                                               # the front, falling into shade
            k = (0 if f < 0.15 else 1 if f < 0.55 else 2) if theta < 60 else (0 if f < 0.35 else 1)
        else:                                                   # the back, lit
            k = (3 if f < 0.3 else 4 if f < 0.75 else 5) if theta < 125 else (3 if f < 0.1 else 4 if f < 0.45 else 5)
        col = (SEPIA + [FLAP_HI])[k]
        for y in range(t, bt + 1):
            c.p(x, y, col)
        c.p(x, t, SEPIA_OUT)
        c.p(x, bt, SEPIA_OUT)
        if 0.2 < f < 0.9 and bt - t > 12:
            c.p(x, t + 1, (SEPIA + [FLAP_HI])[min(5, k + 1)])
    xf = GX + wpx if right else GX - 1 - wpx
    t, bt, _ = cols[xf]
    c.vl(xf, t, bt, SEPIA_OUT)
    inner = xf - 1 if right else xf + 1
    if inner in cols:
        c.vl(inner, cols[inner][0] + 1, cols[inner][1] - 1, FLAP_HI if not right else SEPIA[3])
    for (fx, fy, n) in FIBRE[::3]:                              # a few fibres, so the leaf is paper too
        x = (GX + int(fx * abs(cs))) if right else (GX - 1 - int(fx * abs(cs)))
        y = TOP + fy
        if x in cols and cols[x][0] + 3 < y < cols[x][1] - 3 and c.get(x, y) in SEPIA[2:4]:
            c.p(x, y, SEPIA[SEPIA.index(c.get(x, y)) + 1])
    if right:                                                   # its shadow on the right page, beyond the free edge
        for j, tone in enumerate((0, 1, 2)):
            x = xf + 1 + j
            if x < RP - 1:
                c.vl(x, max(page_top(x) + 1, t + 6 + 3 * j), page_bot(x) - 2, SEPIA[tone])
    else:                                                       # the leaf stands in the light: shade right of the gutter
        n = int(round(11 * sn * sn))
        for j in range(n):
            x = GX + j
            c.vl(x, page_top(x) + 1, page_bot(x) - 2, SEPIA[0] if j < n // 3 else SEPIA[1] if j < 2 * n // 3 else SEPIA[2])
    bb = c.bbox()
    return c.crop(bb[0], bb[1], bb[2] - bb[0] + 1, bb[3] - bb[1] + 1), (bb[0], bb[1])


TURN_ANGLES = [34, 74, 106, 146]


# ================================================================================================ the texture
def paint():
    """Paints every region into the 512x512 texture and fills REG / AT."""
    a = Cv(ATLAS_W, ATLAS_H)

    def put(name, cv, u, v, at=None):
        for y in range(cv.h):
            for x in range(cv.w):
                if a.px[u + x, v + y][3] and cv.px[x, y][3]:
                    raise ValueError("%s lands on another region at %d,%d" % (name, u + x, v + y))
        a.paste(cv, u, v)
        REG[name] = (u, v, cv.w, cv.h)
        if at is not None:
            AT[name] = at

    b = base()
    put("book", b, 0, 0, (0, 0))
    x = W + 1
    for side in "lr":
        for k in range(MAX_LEAVES + 1):
            cv, at = leaves(b, side, k)
            put("leaves_%s_%d" % (side, k), cv, x, 0, at)
            x += 9
    for s in SECTIONS:
        put("run_" + s, run(s), x, 0, (GX - 4, RUN_Y))
        x += 9
    runs_end = x
    x = 0
    for i, th in enumerate(TURN_ANGLES):
        cv, at = turn_frame(b, th)
        put("turn_%d" % i, cv, x, 237, at)
        x += cv.w + 1
    turn_end = x
    mid_x = max(turn_end, W + 1)
    put("print_cyan", cyanotype(), mid_x, 237)
    put("plate_rare", plate(73), mid_x, 323)
    put("plate_planet", plate(55), mid_x + 81, 323)
    put("ledger_head", ledger_head(), mid_x, 404)
    put("ledger_row", ledger_row(), mid_x, 421)

    pk = Packer([(0, 436, 240, 76), (241, 436, 271, 76), (runs_end, 0, 512 - runs_end, 236), (mid_x + 125, 237, 512 - mid_x - 125, 85),
                 (mid_x + 144, 323, 512 - mid_x - 144, 80), (mid_x + 133, 404, 512 - mid_x - 133, 30)])
    items = [("rare_comet", centred_by_box(comet_picture())), ("rare_shower", centred_by_box(shower_picture())),
             ("sketch_rare", centred_by_box(sketch(63, "rare"))),
             ("sketch_planet", sketch(45, "planet")), ("vignette", vignette()), ("rose", compass_rose()),
             ("badge_on", tin_star(True)), ("badge_off", tin_star(False)), ("unknown", sketch(21, "planet")),
             ("stain_ring", stain_ring())]
    title = lettering("STAR ATLAS", TITLE, 5, INKB[0], lo=INKB[1])
    items += [("title", title), ("title_rule", title_rule(title.w))]
    items += [("head_" + s, lettering(HEADINGS[s], SMALL, 4, INKB[0])) for s in SECTIONS]
    items += [("brand", brand())]
    items += [("corner_" + sd, corner(b, sd)[0]) for sd in "lr"]
    items += [("arrow_%s%s" % (sd, "_on" if hv else ""), arrow(sd, hv)) for sd in "lr" for hv in (False, True)]
    items += [("tab_" + s, tab(s)) for s in SECTIONS]
    items += [("tick_on", tick_box(True)), ("tick_off", tick_box(False))]
    items += [("moonface_%d" % p, moon_face(p)) for p in range(8)]
    items += [("tonight", tonight_mark())]
    items += [("pc_" + w_, photo_corner(w_)) for w_ in ("tl", "tr", "bl", "br")]
    items += [("pc_%s_empty" % w_, photo_corner(w_, True)) for w_ in ("tl", "tr", "bl", "br")]
    items += [("flag_" + s, flag(s)) for s in SECTIONS]
    items += [("cy_star_%d" % m, chart_star(m)) for m in (1, 2, 3)]
    items += [("pn_star_%d" % m, chart_star(m, True)) for m in (1, 2, 3)]
    items += [("qmark", sprite(QMARK, {"x": PENCIL[0]}))]
    items += [("fox_%d" % i, fox(i)) for i in range(4)]
    for name, cv in items:
        u, v = pk.place(cv.w, cv.h)
        put(name, cv, u, v)
    AT["corner_l"], AT["corner_r"] = corner(b, "l")[1], corner(b, "r")[1]
    AT["arrow_l"] = AT["arrow_l_on"] = (LP + 15, BOT - 14)
    AT["arrow_r"] = AT["arrow_r_on"] = (RP - 15 - REG["arrow_r"][2], BOT - 14)
    return a


def get(a, name):
    u, v, w, h = REG[name]
    return a.crop(u, v, w, h)
