"""Blocks, items, particles and the beam (16x16, vanilla's own habits: 6 to 13 colours, clusters not speckle,
a dark coloured outline on items, light from the top left).

Concept. What a fallen star leaves behind, and what the stargazer carries.
  * THE CRATER is cold. Starstone is blue-black stone in soft horizontal runs like vanilla's deepslate, with pale
    flecks that are small SHAPES (an elbow, a plus, a wedge), not dots. Its bricks have real mortar, a lit top edge
    and a shaded foot. Stardust is a pale blue sand in short diagonal runs. The Astral Vein is a ragged crust of
    starstone with a bright vein branching through it to all four sides, so veins join from tile to tile. The Star
    Crystal is a cluster of crossed shards, each with a lit and a shaded facet. The Fallen Star is a pitted iron
    meteorite whose seams pulse by tone, never by position.
  * THE KIT is warm. The Star Lamp is an iron lantern frame with brass corners round a cold star. The compass is a
    brass pocket compass, lid hinged open behind it, a night-blue dial and a needle tipped with a star (only the needle
    moves). The Star Lens is a brass lens cell with a blue glint; the Nebula Filter a square glass slide in a brass
    frame; the Star Atlas the buckskin journal itself, lace down its spine, the Circle Star on its cover.

Ties to the kit: BRASS, IRON, HIDE, LACE, BRAND and STARLIGHT are the book's and the star view's own ramps.
"""
import math

from ramps import (Cv, ramp, BRASS, IRON, HIDE, LACE, SEPIA, SEPIA_OUT, BRAND, STARLIGHT, NIGHT, poly_mask)

STONE = ramp((9, 11, 22), (15, 18, 34), (22, 27, 48), (31, 38, 64), (43, 53, 84))
FLECK = ramp((82, 118, 180), (146, 186, 234), (220, 238, 255))
DUST = ramp((60, 84, 130), (96, 122, 168), (124, 152, 196), (152, 180, 218), (182, 206, 236), (212, 230, 248))
METEOR = ramp((14, 14, 22), (26, 26, 38), (40, 40, 56), (58, 58, 78), (80, 82, 104))
GLOW = ramp((40, 78, 150), (70, 120, 200), (140, 188, 242), (226, 242, 255))
CRYSTAL = ramp((34, 60, 120), (76, 116, 186), (128, 170, 228), (184, 216, 250), (236, 246, 255))
GLASS_N = ramp((38, 28, 78), (72, 52, 132), (120, 90, 190), (178, 150, 240), (232, 220, 255))


def tile(rows, pal, w=16):
    c = Cv(w, len(rows))
    for j, row in enumerate(rows):
        row = row.ljust(w, ".")
        assert len(row) == w, (len(row), row)
        for i, ch in enumerate(row):
            if ch != ".":
                c.p(i, j, pal[ch])
    return c


def pal_of(rmp, extra=None):
    p = {str(i): col for i, col in enumerate(rmp)}
    p.update(extra or {})
    return p


# ------------------------------------------------------------------------------------------------ blocks
def starstone():
    return tile(["2223322211222332",
                 "1222221122233221",
                 "22112222ab222211",
                 "332222223b322222",
                 "2233221122222331",
                 "1222211222332222",
                 "2222332222211222",
                 "22b2223332222112",
                 "2abc222221122222",
                 "32b3322222223322",
                 "2222211222332221",
                 "1122222211222222",
                 "2223322222a22233",
                 "22222211223ab322",
                 "33221122222b2211",
                 "2222233221122222"], pal_of(STONE, {"a": FLECK[0], "b": FLECK[1], "c": FLECK[2]}))


def starstone_bricks():
    return tile(["4444444444444430",
                 "3222232222122210",
                 "32232222a2222210",
                 "322222223b222110",
                 "3222122222223210",
                 "3221222232222210",
                 "2111111111111110",
                 "0000000000000000",
                 "4444443044444444",
                 "2222221032232222",
                 "2212221032222232",
                 "222ab21032222122",
                 "2222b21032212222",
                 "2322221032222222",
                 "1111111021111111",
                 "0000000000000000"], pal_of(STONE, {"a": FLECK[0], "b": FLECK[1]}))


def stardust():
    return tile(["3332332233433323",
                 "3233322333322333",
                 "3322433332233432",
                 "2333332233333223",
                 "3334333322333333",
                 "3223323333432233",
                 "3332233433322333",
                 "4333332233333324",
                 "3322333332243333",
                 "3333432233332233",
                 "2233333322333343",
                 "3332233333432233",
                 "3433322433322333",
                 "3323333322333322",
                 "3332243333233433",
                 "2233333224333332"], pal_of(DUST))


def astral_vein():
    return tile([".....12vVv21....",
                 "....122vVv221...",
                 "...1223vVv3221..",
                 "..12233vVvv3221.",
                 ".122vvvVVvvv2211",
                 "1223vVVVWVVvv221",
                 "22vvVVvvVvvVvv32",
                 "vvVVvv3vVv3vVVvv",
                 "VVvv3223vV32vvVV",
                 "vv32221vVv2223vv",
                 "2232211vVVv32221",
                 ".12221vvVvVv221.",
                 "..1223vVv3vv21..",
                 "...122vVv2221...",
                 "....12vVv21.....",
                 ".....2vVv2......"], pal_of(STONE, {"v": GLOW[1], "V": GLOW[2], "W": GLOW[3]}))


SHARDS = [((12.5, 15.5), (13.6, 4.5), 2.0), ((3.5, 15.5), (2.2, 6.5), 1.8), ((8.0, 15.5), (7.4, 0.8), 2.6),
          ((5.6, 15.5), (5.0, 10.0), 1.5), ((10.4, 15.5), (10.6, 8.6), 1.6)]


def star_crystal():
    """A crossed cluster: five shards drawn back to front, each a tall kite split down its ridge into a lit left
    facet and a shaded right one, outlined in the crystal's darkest blue, on a nub of starstone."""
    c = Cv(16, 16)
    for (bx, by), (tx, ty), hw in SHARDS:
        ln = math.hypot(tx - bx, ty - by)
        ax, ay = (tx - bx) / ln, (ty - by) / ln
        nx, ny = -ay, ax
        sh = ln * 0.72                                          # where the shoulders are
        pts = [(bx - nx * hw * 0.8, by - ny * hw * 0.8), (bx + ax * sh - nx * hw, by + ay * sh - ny * hw), (tx, ty),
               (bx + ax * sh + nx * hw, by + ay * sh + ny * hw), (bx + nx * hw * 0.8, by + ny * hw * 0.8)]
        m = {(x, y) for (x, y) in poly_mask(pts) if 0 <= x < 16 and 0 <= y < 16}
        for (x, y) in m:
            edge = any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, -1)))
            side = (x + 0.5 - bx) * nx + (y + 0.5 - by) * ny
            t = ((x + 0.5 - bx) * ax + (y + 0.5 - by) * ay) / ln
            if edge:
                col = CRYSTAL[0]
            elif side > 0.15:
                col = CRYSTAL[1] if t < 0.55 else CRYSTAL[2]
            elif t > 0.7:
                col = CRYSTAL[4]
            else:
                col = CRYSTAL[3] if side > -hw * 0.5 or t > 0.4 else CRYSTAL[2]
            c.p(x, y, col)
    for x, col in ((1, 1), (2, 2), (3, 3), (4, 2), (5, 3), (6, 2), (7, 3), (8, 2), (9, 3), (10, 2), (11, 3), (12, 2),
                   (13, 2), (14, 1)):
        c.p(x, 15, STONE[col])
    for x in range(3, 13):
        if c.get(x, 14) == CRYSTAL[0]:
            c.p(x, 14, STONE[1])
    return c


FALLEN = ["2233221e22112233",
          "232211es21122322",
          "22100es222332211",
          "3210esse22322212",
          "221es22se2211222",
          "ssse2112ses22332",
          "ee22100122sse221",
          "22332101232eesss",
          "2322211233221eee",
          "2211223322100122",
          "221223se21000122",
          "32222es221001332",
          "2233es2222113322",
          "221es22332222211",
          "22es221122332212",
          "22se223321122233"]


def fallen_star():
    """Four frames, 16x64: the same pitted meteorite, its seams stepping dim, bright, white-hot, bright."""
    c = Cv(16, 64)
    for f, (core, edge) in enumerate(((GLOW[1], GLOW[0]), (GLOW[2], GLOW[1]), (GLOW[3], GLOW[2]), (GLOW[2], GLOW[1]))):
        c.paste(tile(FALLEN, pal_of(METEOR, {"s": core, "e": edge})), 0, f * 16)
    return c


def star_lamp():
    g = {"1": STARLIGHT[0], "2": STARLIGHT[1], "3": STARLIGHT[2], "4": STARLIGHT[3], "5": STARLIGHT[4]}
    g.update({"o": IRON[0], "i": IRON[1], "I": IRON[2], "h": IRON[3], "b": BRASS[1], "B": BRASS[3], "y": BRASS[4]})
    return tile(["obBIIIIIIIIIIBbo",
                 "bByhhhhhhhhhhyBb",
                 "ByoiiiiiiiiiioBb",
                 "Ihi1122332211iIo",
                 "Ihi1223553221iIo",
                 "Ihi2233553322iIo",
                 "Ihi2334554332iIo",
                 "Ihi3555555553iIo",
                 "Ihi3555555553iIo",
                 "Ihi2334554332iIo",
                 "Ihi2233553322iIo",
                 "Ihi1223553221iIo",
                 "Ihi1122332211iIo",
                 "ByoiiiiiiiiiioBb",
                 "bBIIIIIIIIIIIIBb",
                 "obbooooooooooobo"], g)


def nebula_glass():
    p = pal_of(GLASS_N, {"L": GLASS_N[2], "D": GLASS_N[0], "*": GLASS_N[4]})
    return tile(["LLLLLLLLLLLLLLLD",
                 "L..............D",
                 "L......1221....D",
                 "L...1223332....D",
                 "L..1233..2321..D",
                 "L..122....232*.D",
                 "L.........1221.D",
                 "L....112...121.D",
                 "L..1123321..12.D",
                 "L.122333221....D",
                 "L.1232*23321...D",
                 "L..1221.12321..D",
                 "L.*.......1221.D",
                 "L..........11..D",
                 "L..............D",
                 "LDDDDDDDDDDDDDDD"], p)


# ------------------------------------------------------------------------------------------------ items
def star_shard():
    return tile(["",
                 "...........00",
                 "..........0430",
                 ".........04320",
                 "........043210",
                 ".......0433210",
                 "......04332100",
                 ".....0433210",
                 "....0433210",
                 "...04332100",
                 "..0433210",
                 "..032210",
                 "..02110",
                 "..0000",
                 "",
                 ""], pal_of(CRYSTAL))


def stardust_item():
    return tile(["",
                 "",
                 ".........5",
                 "....5.......4",
                 "",
                 ".......00",
                 ".....00430",
                 "....0343320",
                 "...034332210",
                 "..03433232210",
                 ".0343323221110",
                 ".0332232211110",
                 "..00000000000",
                 "",
                 "",
                 ""], pal_of(DUST))


def star_atlas_item():
    p = {"o": HIDE[0], "h": HIDE[5], "m": HIDE[3], "d": HIDE[2], "s": HIDE[1], "l": LACE[1], "L": LACE[3],
         "p": SEPIA[4], "q": SEPIA[1], "P": SEPIA_OUT, "r": BRAND[1], "f": HIDE[4], "F": HIDE[2]}
    return tile(["",
                 "..ooooooooooo",
                 ".ohhhhhhhhhhmo",
                 ".oLmmmmmmmmmdo",
                 ".olmmmrrrmmmdoo",
                 ".oLmmrmmmrmmddo",
                 ".olmmrmrmrmmdso",
                 ".oLmmrmmmrmmdoo",
                 ".olmmmrrrmmmdo",
                 ".oLmmmmmmmmmdo",
                 ".oldddddddddso",
                 ".oPpqpqpqpqpPo",
                 ".osssssssssso",
                 "..fF.fF.fF.fF",
                 "..f..fF.f..fF",
                 ".....f.....f"], p)


def disc_item(cx, cy, r_out, r_in, rim, inner):
    """A round brass thing: a rim lit from the top left with a dark outline, and whatever is inside it."""
    c = Cv(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r_out:
                continue
            f = (-dx - dy) / (max(d, 0.01) * 1.414)
            if d > r_out - 1:
                c.p(x, y, rim[0])
            elif d > r_in:
                c.p(x, y, rim[4] if f > 0.6 else rim[3] if f > 0.0 else rim[2] if f > -0.6 else rim[1])
            else:
                c.p(x, y, inner(dx, dy, d, f))
    return c


def star_lens():
    def glass(dx, dy, d, f):
        if d > 4.0:
            return BRASS[0] if f > 0 else BRASS[1]               # the cell's inner wall
        if abs(dx - dy) < 0.8 and -2.6 < dx + dy < -0.4:
            return STARLIGHT[4]                                  # the glint
        return STARLIGHT[3] if f > 0.45 else STARLIGHT[2] if f > -0.3 else STARLIGHT[1]
    c = disc_item(8, 8, 7.2, 5.0, BRASS, glass)
    c.p(10, 10, STARLIGHT[3])
    c.p(11, 9, STARLIGHT[3])
    return c


def nebula_filter():
    p = pal_of(GLASS_N, {"o": BRASS[0], "b": BRASS[1], "m": BRASS[2], "B": BRASS[3], "y": BRASS[4], "t": (70, 150, 150, 255),
                         "T": (130, 200, 190, 255)})
    return tile(["",
                 "............oo",
                 "..oooooooooobyo",
                 ".oyyyyyyyyyyBbo",
                 ".oyBooooooooBmo",
                 ".oyo12234tTo.mbo"[:16],
                 ".oyo1223tT4omb",
                 ".oyo223tT43omb",
                 ".oyo23tT432omb",
                 ".oyo3tT4322omb",
                 ".oyotT43221omb",
                 ".oyBoooooooomb",
                 ".oBmmmmmmmmmbo",
                 "..obbbbbbbbbo",
                 "...ooooooooo",
                 ""], p)


NEEDLE = [STARLIGHT[2], STARLIGHT[3], STARLIGHT[4]]


def star_compass(frame):
    """Frame 0 points up, each frame turns the needle 22.5 degrees clockwise (the original frames' order). Nothing
    but the needle differs between frames."""
    def dial(dx, dy, d, f):
        if d > 3.7:
            return BRASS[0] if f > 0 else BRASS[1]
        return NIGHT[4] if f > 0.3 else NIGHT[3]
    c = Cv(16, 16)
    lid = disc_item(8.5, 5.0, 5.3, 3.4, BRASS, lambda dx, dy, d, f: BRASS[1] if f > 0 else BRASS[2])
    for y in range(0, 5):                                        # the lid, hinged open behind the case
        for x in range(16):
            if lid.px[x, y][3]:
                c.p(x, y, lid.px[x, y])
    c.paste(disc_item(8.5, 9.5, 6.4, 4.6, BRASS, dial), 0, 0)
    c.fill(7, 3, 10, 5, BRASS[0])                                # the hinge
    c.p(8, 3, BRASS[4])
    c.p(8, 4, BRASS[2])
    a = math.radians(frame * 22.5)
    sx, sy = math.sin(a), -math.cos(a)
    for t in (-2, -1):
        c.p(int(math.floor(8.5 + sx * t)), int(math.floor(9.5 + sy * t)), BRAND[1])
    for i, t in enumerate((1, 2, 3)):
        c.p(int(math.floor(8.5 + sx * t * 1.02)), int(math.floor(9.5 + sy * t * 1.02)), NEEDLE[i])
    c.p(8, 9, BRASS[4])                                          # the pivot
    return c


# ------------------------------------------------------------------------------------------------ particles, beam
MOTES = [["", "", "...ll", "..lccl", "..lccl", "...ll", "", ""],
         ["", "...b", "...l", ".blclb", "...l", "...b", "", ""],
         ["", "", "", "...cl", "...lb", "", "", ""]]


def mote(i):
    return tile(MOTES[i], {"b": STARLIGHT[1], "l": STARLIGHT[3], "c": STARLIGHT[4]}, w=8)


BEAM_COL = [140, 168, 196, 220, 240, 255, 255, 255]
BEAM_STREAKS = [(2, 1, 5, -1), (5, 6, 4, 1), (11, 3, 6, -1), (13, 10, 4, 1), (8, 12, 3, -1), (3, 11, 3, 1),
                (9, 0, 2, 1)]


def star_beam():
    """The beam, greyscale because the code tints it: a bright core stepping down to its edges, with a few longer
    and shorter streaks so it reads as light moving when the texture scrolls."""
    c = Cv(16, 16)
    for x in range(16):
        k = min(x, 15 - x)
        for y in range(16):
            v = BEAM_COL[k]
            c.p(x, y, (v, v, v, 255))
    steps = sorted(set(BEAM_COL))
    for x, y, n, d in BEAM_STREAKS:
        k = min(x, 15 - x)
        i = steps.index(BEAM_COL[k])
        v = steps[max(0, min(len(steps) - 1, i + d))]
        for j in range(n):
            c.p(x, (y + j) % 16, (v, v, v, 255))
    return c


def paint_all():
    """name (relative to textures/) -> canvas"""
    out = {"block/starstone": starstone(), "block/starstone_bricks": starstone_bricks(), "block/stardust": stardust(),
           "block/astral_vein": astral_vein(), "block/star_crystal": star_crystal(), "block/fallen_star": fallen_star(),
           "block/star_lamp": star_lamp(), "block/nebula_glass": nebula_glass(), "item/star_shard": star_shard(),
           "item/stardust": stardust_item(), "item/star_atlas": star_atlas_item(), "item/star_lens": star_lens(),
           "item/nebula_filter": nebula_filter(), "entity/star_beam": star_beam()}
    for f in range(16):
        out["item/star_compass_%02d" % f] = star_compass(f)
    for i in range(3):
        out["particle/star_mote_%d" % i] = mote(i)
    return out
