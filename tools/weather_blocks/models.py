"""0.9.0 block models: the Cloudbuster, the Storm Jar and the Orrery (GeckoLib), by the telescope's rules.

    python tools/weather_blocks/models.py   -> models/<name>/<name>.bbmodel + textures/<name>(_glowmask).png
    python tools/weather_blocks/render.py   -> previews/forgotten/models_*.png (offline, no Blockbench)

custom-block-mods rules: whole pixels (even widths centred on 0), a prop's 5-60 cubes, detail painted not modelled,
ramps (no blends), every face bevelled, light from the top left, inside the block and under the block above (y <= 16),
cutout only (the jar's glass is a rim and two glints round see-through pixels, never half see-through).
Front = north (-Z), like the telescope; the block entity renderer turns it to face the player who placed it.

Bones the Java uses: Cloudbuster: root, pipes, crystal (shown while a Storm Crystal is in), dial_needle (turned by the
recharge). Storm Jar: root, cloud (bobs). Orrery: root, arm_<planet> x6 (turned at their own speeds; the chosen one
raised), vane_clear / vane_cloud / vane_rain / vane_storm (one shown: tomorrow's weather).
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("tm", ROOT / "tools/telescope/telescope_model.py")
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)
T = tm.T
Bone, box, Face, ramp = T.Bone, T.box, T.Face, T.ramp
BRASS, WALNUT, IRON, STAR, NIGHT = tm.BRASS, tm.WALNUT, tm.IRON, tm.STAR, tm.NIGHT
idx, bevel, across, ends = tm.idx, tm.bevel, tm.across, tm.ends
CLEAR = (0, 0, 0, 0)

COPPER = ramp((78, 34, 20), (124, 58, 32), (168, 88, 48), (206, 128, 76), (236, 176, 124))
VERD = ramp((30, 82, 74), (52, 126, 108), (92, 168, 144), (150, 210, 186))
GLASS = ramp((92, 120, 140), (150, 182, 204), (206, 228, 240))
CLOUD = ramp((60, 66, 80), (92, 100, 118), (132, 142, 160), (180, 190, 206))
WATER = ramp((28, 52, 92), (44, 80, 132), (74, 118, 176))
TIN = ramp((70, 72, 78), (112, 116, 124), (160, 164, 170), (206, 210, 214))
VIOLET = ramp((40, 30, 92), (70, 58, 150), (110, 102, 204), (160, 160, 240), (214, 220, 255))
GOLD = ramp((120, 70, 10), (196, 130, 24), (244, 196, 64), (255, 236, 150))
PAPER = ramp((166, 134, 90), (208, 184, 136), (234, 218, 178))
INK = (50, 28, 18, 255)
PLANETS = {
    "ember": ramp((60, 14, 8), (120, 30, 14), (188, 64, 24), (236, 126, 46)),
    "verdigris": ramp((16, 58, 56), (30, 98, 88), (58, 150, 128), (118, 198, 170)),
    "old_gold": ramp((92, 58, 30), (146, 98, 56), (202, 160, 104), (236, 212, 164)),
    "pale_rider": ramp((120, 128, 146), (170, 178, 196), (214, 220, 232), (246, 248, 252)),
    "indigo": ramp((14, 16, 52), (28, 34, 96), (48, 62, 150), (86, 108, 200)),
    "cinder": ramp((34, 32, 32), (62, 58, 56), (96, 90, 86), (134, 128, 122)),
}


def flat(R, mid=2):
    def p(c, f, w, h, rng):
        i = idx(c, f, R, mid)
        F = Face(w, h, R[i])
        bevel(F, R, i, w, h)
        return F
    return p


# ------------------------------------------------------------------ Cloudbuster
def p_drum(c, f, w, h, rng):
    """The iron drum: two riveted bands, the seam, dark underneath."""
    i = idx(c, f, IRON, 2)
    F = Face(w, h, IRON[i])
    if f in ("north", "south", "east", "west"):
        for row in (1, h - 2):
            for x in range(w):
                F.set(x, row, IRON[max(0, i - 1)])
                if x % 3 == 1:
                    F.set(x, row, IRON[min(3, i + 1)])            # rivet heads catch the light
    bevel(F, IRON, i, w, h)
    return F


def p_pipe(c, f, w, h, rng):
    """A copper pipe: lit stripe on its left, a verdigris band, its open mouth dark at the top."""
    if f == "up":
        F = Face(w, h, COPPER[3])
        if w >= 2 and h >= 2:
            F.set(w - 1, h - 1, COPPER[0])
            F.set(0, 0, COPPER[4])
        if w >= 2 and h >= 2:
            for y in range(h):
                for x in range(w):
                    if 0 < x < w - 1 or w == 2:
                        pass
        F.set(w // 2, h // 2, COPPER[0])
        return F
    if f == "down":
        return Face(w, h, COPPER[0])
    i = idx(c, f, COPPER, 2)
    F = Face(w, h, COPPER[i])
    for x in range(w):
        F.set(x, 0, COPPER[min(4, i + 1)])                         # the lip
        F.set(x, c.info.get("band", 3), VERD[2 if x == 0 else 1])  # a green band where the rain sits
    for y in range(1, h):
        if F.get(0, y) == COPPER[i]:
            F.set(0, y, COPPER[min(4, i + 1)])
    return F


def p_dial(c, f, w, h, rng):
    """The brass dial on the drum's front: a cream face with a tick ring (the needle is its own bone)."""
    if f != "north":
        return tm.p_brass(c, f, w, h, rng)
    F = Face(w, h, BRASS[3])
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            F.set(x, y, PAPER[2])
    for x, y in ((1, 1), (w - 2, 1)):
        F.set(x, y, PAPER[0])
    for x in range(w):
        F.set(x, h - 1, BRASS[1])
    return F


def p_needle(c, f, w, h, rng):
    return Face(w, h, (146, 48, 28, 255))


def p_crystal(c, f, w, h, rng):
    """A Storm Crystal seated in its slot: violet glass, a lit bolt (glows)."""
    F = Face(w, h, VIOLET[2])
    for x in range(w):
        F.set(x, h - 1, VIOLET[0])
    F.shine(0, 0, VIOLET[4])
    if w > 1 and h > 1:
        F.shine(w - 1, 1, (255, 236, 150, 255))
    return F


def cloudbuster():
    """A cast-iron foot with the dial and the crystal slot on its front, a short post, a brass fork, and in the fork a
    bank of six long copper pipes tilted back at the sky, held by two brass clamps."""
    root = Bone("root", (0, 0, 0))
    box(root, "foot", (-5, 0, -5), (5, 2, 5), "iron")
    box(root, "drum", (-4, 2, -4), (4, 6, 4), "drum")
    box(root, "dial", (-3, 2, -5), (1, 6, -4), "dial")
    box(root, "slot", (2, 3, -5), (4, 5, -4), "iron")
    needle = Bone("dial_needle", (-1, 4, -5), parent=root)
    box(needle, "needle", (-1, 4, -6), (0, 6, -5), "needle")
    crystal = Bone("crystal", (3, 4, -5), parent=root)
    box(crystal, "crystal", (2, 3, -6), (4, 5, -5), "crystal")
    box(root, "post", (-1, 6, -1), (1, 8, 1), "iron")
    box(root, "fork", (-6, 8, -1), (6, 9, 1), "brass")
    box(root, "fork_l", (-6, 9, -1), (-5, 11, 1), "brass")
    box(root, "fork_r", (5, 9, -1), (6, 11, 1), "brass")
    pipes = Bone("pipes", (0, 10, 0), rot=(-32, 0, 0), parent=root)
    for row, z in enumerate((-2, 1)):
        for col, x in enumerate((-4, -1, 2)):
            box(pipes, f"pipe_{row}{col}", (x, 7, z), (x + 2, 17 - row, z + 1 + 1), "pipe", band=3 + (col + row) % 2)
    box(pipes, "clamp_lo", (-5, 9, -3), (5, 10, 4), "brass", lift=-1)
    box(pipes, "clamp_hi", (-5, 14, -3), (5, 15, 4), "brass", lift=-1)
    return root


# ------------------------------------------------------------------ Storm Jar
def p_glass(c, f, w, h, rng):
    """Cutout glass: a pale rim one pixel wide, two glints down the front-left, the middle see-through."""
    F = Face(w, h, CLEAR)
    for x in range(w):
        F.set(x, 0, GLASS[2])
        F.set(x, h - 1, GLASS[0])
    for y in range(h):
        F.set(0, y, GLASS[2] if f in ("north", "west") else GLASS[1])
        F.set(w - 1, y, GLASS[0])
    if f in ("north", "west") and w > 4 and h > 5:
        for y in range(2, h - 3):
            F.set(2, y, GLASS[2])
        F.set(3, 2, GLASS[2])
    return F


def p_cloud(c, f, w, h, rng):
    """The little storm cloud inside: soft pale grey, lit on top, one shade darker underneath. No stripes."""
    if f == "down":
        return Face(w, h, CLOUD[1])
    if f == "up":
        return Face(w, h, CLOUD[3])
    i = idx(c, f, CLOUD, 2)
    F = Face(w, h, CLOUD[i])
    for x in range(w):
        F.set(x, 0, CLOUD[min(3, i + 1)])
        F.set(x, h - 1, CLOUD[max(1, i - 1)])
    return F


def p_water(c, f, w, h, rng):
    F = Face(w, h, WATER[1])
    if f == "up":
        for x in range(1, w - 1, 3):
            F.set(x, 1, WATER[2])
    return F


def storm_jar():
    root = Bone("root", (0, 0, 0))
    box(root, "plinth", (-5, 0, -5), (5, 2, 5), "walnut_flat")
    box(root, "jar", (-4, 2, -4), (4, 12, 4), "glass", faces={"down": None})
    box(root, "puddle", (-3, 2, -3), (3, 3, 3), "water")
    box(root, "neck", (-3, 12, -3), (3, 13, 3), "glass")
    box(root, "lid", (-4, 13, -4), (4, 14, 4), "tin")
    box(root, "knob", (-1, 14, -1), (1, 15, 1), "tin")
    cloud = Bone("cloud", (0, 9, 0), parent=root)            # three puffs, the middle one higher
    box(cloud, "cloud", (-3, 7, -3), (3, 10, 3), "cloud")
    box(cloud, "puff", (-2, 10, -2), (2, 11, 2), "cloud")
    return root


# ------------------------------------------------------------------ Orrery
def p_planet(c, f, w, h, rng):
    """0.9.1 (owner: "bigger and more detailed"): each planet painted with its own look, lit from the top left.
    Ember: a red coal with glowing cracks. Verdigris: sea-green with paler bands. Old Gold: gold bands. Pale Rider: white
    with a bright cap. Indigo: deep blue with a dark belt. Cinder: grey with darker pits."""
    pl = c.info["planet"]
    R = PLANETS[pl]
    i = idx(c, f, R, 2)
    F = Face(w, h, R[i])
    if pl == "ember":
        F = Face(w, h, R[max(0, i - 1)])
        cracks = [(0, 1), (1, 1), (1, 2), (2, 0), (w - 1, h - 2), (w - 2, h - 2)]
        for x, y in cracks:
            if 0 <= x < w and 0 <= y < h:
                F.shine(x, y, (255, 168, 72, 255))
        if f == "up":
            F.shine(w // 2, h // 2, (255, 214, 120, 255))
        return F
    if pl in ("verdigris", "old_gold", "indigo") and f not in ("up", "down"):
        for y in range(h):                                # horizontal bands round the ball
            if pl == "indigo" and y == h // 2:
                for x in range(w):
                    F.set(x, y, R[max(0, i - 1)])
            elif pl == "old_gold" and y % 2 == 1:
                for x in range(w):
                    F.set(x, y, R[max(0, i - 2)])
            elif pl == "verdigris" and y == 1:
                for x in range(w):
                    F.set(x, y, R[min(len(R) - 1, i + 1)])
    if pl == "cinder":
        for x, y in ((0, 0), (w - 1, h - 1)):
            if w > 1:
                F.set(x, y, R[max(0, i - 1)])
    if pl == "pale_rider" and f == "up":
        F.set(0, 0, (255, 255, 255, 255))
    bevel(F, R, i, w, h)
    return F


def p_sun(c, f, w, h, rng):
    """The brass sun: gold, its top and a ring of rays lit (glows faintly, it is the lamp of the thing)."""
    i = idx(c, f, GOLD, 2)
    F = Face(w, h, GOLD[i])
    bevel(F, GOLD, i, w, h)
    if f == "up":
        for x in range(1, w - 1):
            for y in range(1, h - 1):
                F.shine(x, y, GOLD[3] if (x + y) % 2 == 0 else GOLD[2])
    elif f == "north" and h >= 3:
        F.shine(w // 2, h // 2, GOLD[3])
    return F


def p_ring(c, f, w, h, rng):
    """Old Gold's ring: pale brass with a dark gap line along it."""
    i = idx(c, f, BRASS, 3)
    F = Face(w, h, BRASS[i])
    if f in ("up", "down") and h >= 3:
        for x in range(w):
            F.set(x, h // 2, BRASS[max(0, i - 2)])
    return F


def p_base(c, f, w, h, rng):
    """The walnut base: bevelled, a brass inlay ring on top (the orbits) and a brass line round its sides."""
    R = WALNUT
    i = idx(c, f, R, 2)
    F = Face(w, h, R[i])
    bevel(F, R, i, w, h)
    if f == "up" and w >= 9:
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if abs(r - 6.0) < 0.5:
                    F.set(x, y, BRASS[2])
                elif abs(r - 3.0) < 0.45:
                    F.set(x, y, BRASS[1])
    elif f in ("north", "south", "east", "west") and h >= 2:
        for x in range(1, w - 1):
            F.set(x, 0, BRASS[2])
    return F


VANES = {   # 0.9.1: four rows, the card is a plaque on the base's front now (below the planets' sweep)
    "clear": ["y.yy.y", ".yyyy.", ".yyyy.", "y.yy.y"],
    "cloud": ["..gg..", ".gggg.", "gggggg", "......"],
    "rain": [".gggg.", "gggggg", ".b.b..", "b.b.b."],
    "storm": [".gggg.", "gggggg", "..yy..", ".y...."],
}


def p_vane(c, f, w, h, rng):
    """A weather card on the Orrery's top: paper in a brass edge, tomorrow's sky in ink and colour on both faces."""
    if f not in ("north", "south"):
        return Face(w, h, BRASS[2])
    F = Face(w, h, PAPER[2])
    for x in range(w):
        F.set(x, 0, BRASS[3])
        F.set(x, h - 1, BRASS[1])
    for y in range(h):
        F.set(0, y, BRASS[3])
        F.set(w - 1, y, BRASS[1])
    pal = {"y": (214, 160, 40, 255), "g": (110, 116, 128, 255), "b": (60, 100, 170, 255)}
    rows = VANES[c.info["kind"]]
    ox, oy = (w - 6) // 2, (h - len(rows)) // 2
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                F.set(ox + i if f == "north" else w - 1 - ox - i, oy + j, pal[ch])
    return F


# 0.9.1, bigger planets (owner: "bigger and more detailed, it feels a bit stale"; then "widen the base since clipping").
# Two columns turn round the stem: close in (x 1..4) Ember and Indigo sit on the stem with no rod; far out (x 4..8)
# Cinder, Pale Rider, Verdigris and Old Gold, each on a 1 px rod that crosses the close-in column at a height no close-in
# planet uses. So no ball or rod ever meets another, whatever their speeds (tools check: sweep test in the 0.9.1 notes).
#   y 4..5 Cinder's rod (ball 4..6)      y 5..8 Ember      y 8..9 Pale Rider's rod (ball 6..9)
#   y 9..10 Verdigris's rod (ball 9..12, its moon)          y 10..13 Indigo
#   y 13..14 Old Gold's rod, out of the sun's side (a squat ball 13..16, its ring 14..15)
# planet, rod y, ball's first x, size, ball's first y
ORBITS = (("cinder", 4, 6, 2, 4), ("ember", None, 1, 3, 5), ("pale_rider", 8, 5, 3, 6), ("verdigris", 9, 5, 3, 9),
          ("indigo", None, 1, 3, 10), ("old_gold", 13, 4, 4, 13))


def orrery():
    """A walnut base on four brass feet with an orbit inlay and tomorrow's weather card on its front edge, a brass stem
    with collars, the sun on top, and the six planets on arms in three bands (they turn at their own speeds)."""
    root = Bone("root", (0, 0, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(root, f"foot_{sx}{sz}", (6 if sx > 0 else -7, 0, 6 if sz > 0 else -7),
                (7 if sx > 0 else -6, 1, 7 if sz > 0 else -6), "brass")
    # 0.9.1: 14 x 14 so the outer planets turn over it, not past it (owner: "widen the base since clipping")
    box(root, "base", (-7, 1, -7), (7, 3, 7), "base")
    box(root, "stem", (-1, 3, -1), (1, 13, 1), "brass", bands=[2, 5, 8])
    box(root, "sun", (-2, 13, -2), (2, 16, 2), "sun")
    for k, (pl, y, x0, s, y0) in enumerate(ORBITS):
        arm = Bone("arm_" + pl, (0, y0, 0), rot=(0, k * 60 + 15, 0), parent=root)
        z0, z1 = (-(s // 2), s // 2) if s % 2 == 0 else (-(s // 2), s // 2 + 1)   # odd sizes centre on the 1 px rod
        if y is not None:
            box(arm, "rod_" + pl, (1, y, 0), (x0, y + 1, 1), "brass")
        tall = 3 if pl == "old_gold" else s                   # the giant is squat (4 wide, 3 tall), clear of Indigo
        box(arm, "ball_" + pl, (x0, y0, z0), (x0 + s, y0 + tall, z1), "planet", planet=pl)
        if pl == "old_gold":                                  # its ring, edge-on along the arm
            box(arm, "ring", (x0 - 1, y0 + 1, -1), (x0 + s + 1, y0 + 2, 1), "ring")
        if pl == "verdigris":                                 # "keeps a little moon"
            box(arm, "moon", (x0 + 1, y0 + 2, 2), (x0 + 2, y0 + 3, 3), "planet", planet="pale_rider")
    for kind in VANES:                                        # one shown: tomorrow's weather
        v = Bone("vane_" + kind, (0, 0, -7), parent=root)
        box(v, "card_" + kind, (-4, 0, -8), (4, 4, -7), "vane", kind=kind)
    return root


PAINT = {"brass": tm.p_brass, "iron": tm.p_iron, "walnut_flat": flat(WALNUT), "drum": p_drum, "pipe": p_pipe,
         "dial": p_dial, "needle": p_needle, "crystal": p_crystal, "glass": p_glass, "cloud": p_cloud,
         "water": p_water, "tin": flat(TIN, 3), "planet": p_planet, "sun": p_sun, "vane": p_vane,
         "ring": p_ring, "base": p_base}


def main():
    only = sys.argv[1:]
    for name, fn in (("cloudbuster", cloudbuster), ("storm_jar", storm_jar), ("orrery", orrery)):
        if only and name not in only:
            continue
        root = fn()
        for b, c in T.all_cubes(root):
            if not c.rot:
                assert all(abs(v - round(v)) < 1e-6 for v in c.a + c.b), (name, c.name)
        for x in tm.check_planes(root):
            print(name, "same plane:", x)
        tm.light_pass(root)
        T.PAINT, T.NAME, T.ROOT = PAINT, name, ROOT / "models" / name
        T.ROOT.mkdir(parents=True, exist_ok=True)
        path, n, size = T.write(root)
        print(path, n, "cubes", size)


if __name__ == "__main__":
    main()
