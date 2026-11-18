"""The star view's sprites (gui/sky.png, 256x256), at the slots the current StarViewRenderer already draws.

Concept. You are looking down a brass tube at a cold sky. So there are two families and they never mix:
  * THE SKY, cold: stars are small cut shapes (a point, a plus, a plus with spikes, a long-spiked sparkle) in four
    star colours, each with a darker halo tone on the diagonals so they glow by steps, never by alpha; they twinkle
    by tone only, the silhouette stays. Clusters are knots of single points. Clouds are slate billows with a moonlit
    upper-left edge and a ragged, wispy underside. The comet's head is a small cold ball.
  * THE INSTRUMENT, warm: everything the stargazer's hand put there is brass, iron or saddle leather. The aim mark
    is four engraved brass wedges round an open centre (a surveyor's graticule, not a crosshair); locked, they brighten
    and four corner nicks close in. The tracing ring is a turned brass ring with a notch at the top; a wrong pick is
    the same ring in brand red, broken. The zoom ladder is three brass studs: a lit lens, a dark lens, a blank iron
    one. Messages hang on a stitched saddle-leather tag with brass rivets (dark, because the current code writes on
    it in pale colours); key hints are small walnut key-plates edged in brass.

Ties to the kit: the same BRASS, LEATHER, WALNUT and IRON as the book's corners and the items; the same STARLIGHT as
the prints and the fallen star.
"""
import math
import re

from ramps import (Cv, sprite, mix, ROOT, BRASS, IRON, LEATHER, LACE, WALNUT, BRAND, NIGHT, STARLIGHT, STAR_RAMPS,
                   STAR_COLOURS, SEPIA, SEPIA_OUT, INKB, ball)


def original_regions(tex):
    """The slots the code draws from, read from the backed-up sprite table (never changed by the redo)."""
    out = {}
    src = (ROOT / "art/original/SkySprites.java").read_text(encoding="utf-8")
    for name, t, u, v, w, h in re.findall(r'R\.put\("(\w+)", new int\[\]\{(\d), (\d+), (\d+), (\d+), (\d+)\}', src):
        if int(t) == tex:
            out[name] = (int(u), int(v), int(w), int(h))
    return out


SKY_REG = original_regions(0)

# ------------------------------------------------------------------------------------------------ the stars
STAR_ART = {
    "A": ([ "...b...", "...l...", "..hlh..", "bllcllb", "..hlh..", "...l...", "...b..."],
          [ "...l...", "...c...", "..bcb..", "lcccccl", "..bcb..", "...c...", "...l..."]),
    "B": (["..b..", ".hlh.", "blclb", ".hlh.", "..b.."],
          ["..l..", ".blb.", "lcccl", ".blb.", "..l.."]),
    "C": ([".b.", "blb", ".b."], [".l.", "lcl", ".l."]),
    "D": (["b"], ["l"]),
    "E": (["h"], ["b"]),
}


def stars(c):
    for tier, frames in STAR_ART.items():
        for colour in STAR_COLOURS:
            h, b, l, core = STAR_RAMPS[colour]
            for f in (0, 1):
                u, v, w, hh = SKY_REG["star_%s_%s_%d" % (tier, colour, f)]
                rows = frames[f]
                assert len(rows) == hh and len(rows[0]) == w
                c.art(u, v, rows, {"h": h, "b": b, "l": l, "c": core})


CLUSTERS = {
    "warm": ("yellow", [(5, 5, 3), (6, 5, 2), (3, 4, 2), (8, 4, 1), (5, 2, 2), (4, 7, 2), (7, 7, 1), (2, 6, 1),
                        (5, 9, 0), (1, 3, 0), (9, 8, 0), (6, 0, 0), (0, 8, 0), (9, 2, 0), (3, 1, 0), (7, 9, 0), (10, 6, 0), (4, 10, 0)]),
    "white": ("white", [(5, 5, 3), (5, 4, 2), (3, 6, 2), (7, 3, 2), (8, 6, 1), (2, 3, 1), (5, 7, 1), (6, 9, 1),
                        (0, 5, 0), (10, 4, 0), (4, 1, 0), (9, 9, 0), (1, 8, 0), (8, 1, 0), (3, 10, 0), (10, 7, 0),
                        (7, 5, 1), (6, 0, 0)]),
    "red": ("orange", [(5, 5, 3), (4, 5, 2), (6, 3, 2), (3, 7, 1), (7, 7, 2), (2, 3, 1), (8, 5, 1), (5, 8, 0),
                       (5, 1, 0), (9, 2, 0), (1, 5, 0), (9, 9, 0), (2, 9, 0), (7, 1, 0)]),
}


def clusters(c):
    for name, (colour, pts) in CLUSTERS.items():
        u, v, w, h = SKY_REG["cluster_" + name]
        r = STAR_RAMPS[colour]
        for x, y, t in pts:
            c.p(u + x, v + y, r[t])


def comet_head(c):
    u, v, _, _ = SKY_REG["comet_head"]
    c.art(u, v, ["...h...", ".hbbbh.", ".blllb.", "hblclbh", ".blllb.", ".hbbbh.", "...h..."],
          {"h": STARLIGHT[0], "b": STARLIGHT[1], "l": STARLIGHT[3], "c": STARLIGHT[4]})


# ------------------------------------------------------------------------------------------------ the instrument
RETICLE = ["......LMD......",
           "......LMD......",
           ".......M.......",
           ".......M.......",
           "...............",
           "...............",
           "LL...........LL",
           "MMMM...o...MMMM",
           "DD...........DD",
           "...............",
           "...............",
           ".......M.......",
           ".......M.......",
           "......LMD......",
           "......LMD......"]
RETICLE_LOCK = ["......LMD......",
                "......LMD......",
                "......LMD......",
                "..LM...M...LM..",
                "..M.........D..",
                "...............",
                "LLL.........LLL",
                "MMMM...o...MMMM",
                "DDD.........DDD",
                "...............",
                "..M.........D..",
                "..MD...M...DD..",
                "......LMD......",
                "......LMD......",
                "......LMD......"]


def reticle(c):
    u, v, _, _ = SKY_REG["reticle"]
    c.art(u, v, RETICLE, {"L": BRASS[4], "M": BRASS[3], "D": BRASS[1], "o": BRASS[2]})
    u, v, _, _ = SKY_REG["reticle_lock"]
    c.art(u, v, RETICLE_LOCK, {"L": (255, 244, 196), "M": BRASS[4], "D": BRASS[2], "o": STARLIGHT[4]})


def rings(c):
    for name, rmp, gaps in (("trace_ring", BRASS, False), ("trace_wrong", [BRAND[0], BRAND[0], BRAND[1], BRAND[2],
                                                                           (240, 150, 120, 255)], True)):
        u, v, _, _ = SKY_REG[name]
        for y in range(11):
            for x in range(11):
                dx, dy = x - 5, y - 5
                d = math.hypot(dx, dy)
                if 4.3 <= d <= 5.4:
                    if gaps and abs(abs(dx) - abs(dy)) <= 1 and abs(dx) > 1:
                        continue
                    f = (-dx - dy) / (d * 1.414)
                    c.p(u + x, v + y, rmp[4] if f > 0.5 else rmp[3] if f > -0.2 else rmp[2] if f > -0.7 else rmp[1])
        if not gaps:
            c.p(u + 5, v + 1, BRASS[4])                           # the notch at the top
            c.p(u + 5, v + 9, BRASS[2])


def pips(c):
    """The zoom ladder: three 7-px studs. Lit: brass round a bright lens. Open: brass round a dark lens with a glint.
    Locked: a blank iron stud."""
    for name in ("pip_lit", "pip_open", "pip_locked"):
        u, v, _, _ = SKY_REG[name]
        rmp = IRON if name == "pip_locked" else BRASS
        for y in range(7):
            for x in range(7):
                dx, dy = x - 3, y - 3
                d = math.hypot(dx, dy)
                if d > 3.3:
                    continue
                f = (-dx - dy) / 4.2
                if d > 2.4:
                    c.p(u + x, v + y, rmp[0] if f < -0.45 else rmp[1])
                elif d > 1.5:
                    c.p(u + x, v + y, rmp[-1] if f > 0.3 else rmp[-2] if f > -0.3 else rmp[1])
                elif name == "pip_lit":
                    c.p(u + x, v + y, STARLIGHT[4] if (dx, dy) in ((0, 0), (-1, -1), (0, -1), (-1, 0)) else STARLIGHT[2])
                elif name == "pip_open":
                    c.p(u + x, v + y, STARLIGHT[1] if (dx, dy) == (-1, -1) else NIGHT[3])
                else:
                    c.p(u + x, v + y, IRON[2] if f > 0 else IRON[1])


# ---- the message tag and the key plates
def plaque(c):
    """A saddle-leather tag: plaque_l and plaque_r are its rounded ends with a brass rivet each, plaque_m tiles every
    16 px (the stitching repeats every 8). Rows 5..14 are plain for the text the code writes at y+6."""
    L0, L1, L2, L3, L4 = LEATHER
    col = [None, L0, L4, L3, L2, L1, L1, L1, L1, L1, L1, L1, L1, L1, L1, L1, L2, L1, L0, None]   # by row, 20 rows
    col[0], col[19] = L0, L0
    col[1], col[18] = L3, L0
    col[2], col[17] = L2, L1
    col[3], col[16] = L2, L1
    u, v, _, _ = SKY_REG["plaque_m"]
    for x in range(16):
        for y in range(20):
            c.p(u + x, v + y, col[y])
        # stitches, 3 on 5 off: "--SSSo--" in every 8 px, so the tag's middle (a whole number of tiles) starts 2 px
        # after the left end and stops 2 px before the right one (it was "-SSSo---": 1 px at the left, 4 at the right)
        if x % 8 in (2, 3, 4):
            c.p(u + x, v + 3, LACE[3])
            c.p(u + x, v + 16, LACE[3] if x % 8 != 4 else LACE[2])
        if x % 8 == 5:
            c.p(u + x, v + 3, L0)                                # the hole the thread goes down
            c.p(u + x, v + 16, L0)
    inset = [4, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 4]
    for name, flip in (("plaque_l", False), ("plaque_r", True)):
        u, v, _, _ = SKY_REG[name]
        for y in range(20):
            for i in range(6):
                x = 5 - i if flip else i
                if i < inset[y]:
                    continue
                edge = i == inset[y] or (y in (0, 19))
                c.p(u + x, v + y, L0 if edge else col[y])
            if inset[y] == 0 and not flip:
                c.p(u + 1, v + y, L3)                            # the lit end
        rx = u + (1 if flip else 3)
        c.art(rx, v + 9, ["LM", "MD"], {"L": BRASS[4], "M": BRASS[3], "D": BRASS[1]})


def keys(c):
    """Key plates, 13 px tall: walnut faces edged in brass. key_m is one column repeated, so the code can crop it to
    any width; rows 2..10 are plain walnut under the white key name the code writes at y+3."""
    colm = [BRASS[1], BRASS[4], BRASS[3], WALNUT[1], WALNUT[1], WALNUT[1], WALNUT[1], WALNUT[1], WALNUT[1], WALNUT[1],
            WALNUT[0], BRASS[2], BRASS[0]]
    colm[2] = WALNUT[2]
    u, v, _, _ = SKY_REG["key_m"]
    for x in range(4):
        for y in range(13):
            c.p(u + x, v + y, colm[y])
    for name, flip in (("key_l", False), ("key_r", True)):
        u, v, _, _ = SKY_REG[name]
        rows = [".oo", "oLL", "oLM", "oMw", "oMw", "oMw", "oMw", "oMw", "oMw", "oMw", "oMd", "oDD", ".oo"]
        if flip:
            rows = [".oo", "oMM", "oDM", "oDw", "oDw", "oDw", "oDw", "oDw", "oDw", "oDw", "oDd", "oDD", ".oo"]
        pal = {"o": BRASS[0], "L": BRASS[4], "M": BRASS[3], "D": BRASS[2], "w": WALNUT[1], "d": WALNUT[0]}
        for y, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    c.p(u + (2 - i if flip else i), v + y, pal[ch])
        # the plate's top and bottom edges run on from the middle piece
        c.p(u + (0 if flip else 2), v, BRASS[1])
        c.p(u + (0 if flip else 2), v + 12, BRASS[0])


# ------------------------------------------------------------------------------------------------ night clouds
CLOUD = [(13, 18, 36, 255), (21, 28, 52, 255), (32, 41, 70, 255), (48, 60, 94, 255), (70, 86, 124, 255)]
LOBES = [
    ([(11, 13, 9, 5), (22, 9, 10, 7), (36, 10, 12, 8), (50, 12, 10, 6), (58, 14, 5, 3), (30, 14, 26, 4)], 17,
     [(4, 17, 5), (17, 18, 4), (40, 18, 6), (53, 17, 3), (27, 18, 2)]),
    ([(9, 12, 7, 4), (19, 11, 9, 6), (33, 8, 11, 7), (46, 11, 9, 6), (56, 13, 6, 4), (32, 14, 28, 3)], 16,
     [(8, 16, 4), (22, 17, 7), (36, 17, 3), (47, 16, 6), (58, 16, 2)]),
    ([(14, 11, 11, 7), (28, 12, 9, 6), (41, 9, 10, 7), (52, 13, 8, 5), (7, 14, 5, 3), (30, 15, 27, 3)], 17,
     [(3, 17, 3), (12, 18, 6), (30, 17, 5), (44, 18, 4), (55, 17, 5)]),
]


def clouds(c):
    """Three night clouds, 64x20: billows (hand-picked lobes) cut flat along a base, a moonlit edge on what faces the
    top left, a darker fold where one billow sits in front of the next, a dark underside, and wisps hanging off it."""
    for i, (lobes, base, wisps) in enumerate(LOBES):
        u, v, w, h = SKY_REG["cloud_%d" % i]
        inside = {}
        for y in range(h):
            for x in range(w):
                if y > base:
                    continue
                for k, (cx, cy, rx, ry) in enumerate(lobes):
                    if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                        inside.setdefault((x, y), k)
        for (x, y), k in inside.items():
            cx, cy, rx, ry = lobes[k]
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            rim = math.hypot(nx, ny)
            top = (x, y - 1) not in inside
            left = (x - 1, y) not in inside
            if y >= base - 1:
                t = 0
            elif top or (left and y < cy):
                t = 4 if (nx + ny < -0.2) else 3
            elif (x, y - 2) not in inside or ((x - 1, y - 1) not in inside):
                t = 3 if nx + ny < 0.4 else 2
            elif rim > 0.78 and nx + ny > 0.5 and (x + 1, y + 1) in inside and inside[(x + 1, y + 1)] != k:
                t = 0                                             # the fold between two billows
            elif ny > 0.35:
                t = 1
            else:
                t = 2
            c.p(u + x, v + y, CLOUD[t])
        for (x, y, n) in wisps:
            for j in range(n):
                c.p(u + x + j, v + y, CLOUD[0] if j not in (0, n - 1) else CLOUD[1])
            if n > 3:
                c.p(u + x + 1, v + y + 1, CLOUD[0])
                c.p(u + x + 2, v + y + 1, CLOUD[0])


def paint():
    c = Cv(256, 256)
    stars(c)
    clusters(c)
    comet_head(c)
    reticle(c)
    rings(c)
    pips(c)
    plaque(c)
    keys(c)
    clouds(c)
    return c


# ------------------------------------------------------------------------------------------------ new for the frames
# Sprites the redone star view code draws that the original table never had (free space under the old slots).
NEW_REG = {"set_screw": (0, 96, 7, 7), "brand_star": (8, 96, 12, 10), "num_0": (22, 96, 4, 5), "num_18": (27, 96, 8, 5),
           "num_9": (36, 96, 3, 6), "num_27": (40, 96, 7, 6)}
SKY_REG.update(NEW_REG)
NUMERALS = {  # engraved in the telescope's scale band; sized so each centres on the lens's even centre line
    "num_0": ["####", "#..#", "#..#", "#..#", "####"],
    "num_18": [".#..####", "##..#..#", ".#..####", ".#..#..#", ".#..####"],
    "num_9": ["###", "#.#", "#.#", "###", "..#", "###"],
    "num_27": ["###.###", "..#...#", "..#...#", "###..#.", "#....#.", "###..#."],
}


def frame_parts(c):
    """The telescope's slotted set screw and scale numerals, and the star branded into the Found tag."""
    from ramps import poly_mask, star_points
    u, v, _, _ = NEW_REG["set_screw"]
    sp = Cv(7, 7)
    ball(sp, 3.5, 3.5, 3.5, BRASS)
    for j in range(1, 6):
        sp.p(j, 6 - j, BRASS[0])                                  # the slot
    c.paste(sp, u, v)
    for name, rows in NUMERALS.items():
        u, v, w, h = NEW_REG[name]
        assert len(rows) == h and all(len(r) == w for r in rows), name
        c.art(u, v, rows, {"#": BRASS[0]})
    u, v, w, h = NEW_REG["brand_star"]
    outer = poly_mask(star_points(6.0, 6.3, 6.3, 2.5))             # 12 x 10: even, so it centres on the 20-px tag
    inner = poly_mask(star_points(6.0, 6.3, 3.9, 1.5))
    xs, ys = [p[0] for p in outer], [p[1] for p in outer]
    assert (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1) == (w, h), "brand_star box"
    for p in outer:
        c.p(u + p[0] - min(xs), v + p[1] - min(ys), (30, 12, 8, 255) if p in inner else LEATHER[0])


_paint_slots = paint


def paint():
    c = _paint_slots()
    frame_parts(c)
    return c
