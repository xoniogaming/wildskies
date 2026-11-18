"""The two big planet pieces (1.1.0, owner: "combine them to make something cool, larger than the Orrery"; picked
the Grand Orrery and the ceiling mobile). Same rules and painters as the lamp (tools/lamp/lamp_model.py).

    python tools/lamp/grand_models.py   -> models/grand_orrery/, models/planet_mobile/ (.bbmodel + textures)

Grand Orrery: a 3 x 3 walnut table (origin = bottom centre of its middle block, 48 x 48 px) with the six planets on
arms round a brass column above a carved table, the sun (the Star Lamp's globe) on top. Three blocks tall.
Planet mobile: hangs 2 blocks down from a ceiling hook (origin = bottom centre of its lowest middle block, y 0..32,
the hook at y 32): a hub, the sun hanging under it, the six planets hanging on cords from arms.

Every planet has its own bone (orbit_<id>, turned about the middle at its own speed). Because they all turn at
different speeds, sweep() checks that no two parts in different bones (or a bone and the still parts) ever share a
height and a radius band at once: a part turning about the axis covers the ring from its nearest to its farthest
point. Planet sizes are the lamps' (lamp_model.SIZES).
"""
import importlib.util
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("lm", HERE / "lamp_model.py")
lm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lm)
tm, T = lm.tm, lm.T
Bone, box, Face = T.Bone, T.box, T.Face
BRASS, WALNUT = lm.BRASS, lm.WALNUT
SIZES = lm.SIZES


def p_table(c, f, w, h, rng):
    """The Grand Orrery's walnut top: shaded corner to corner, brass orbit rings inlaid at each planet's radius."""
    R = WALNUT
    i = 1 if f == "down" else 3 if f == "up" else 2   # sides one tone (the game shades them); top lighter
    F = Face(w, h, R[i])
    if f == "up":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                k = i                                               # flat: a big top shaded corner to corner reads as two halves
                F.set(x, y, R[max(0, min(4, k))])
                r = math.hypot(x - cx, y - cy)
                for rr in c.info.get("orbits", []):
                    if abs(r - rr) < 0.5:
                        F.set(x, y, BRASS[3])
    tm.bevel(F, R, i, w, h)
    if f in ("north", "south", "east", "west"):
        for x in range(1, w - 1):
            F.set(x, 0, BRASS[3] if f in ("north", "west") else BRASS[2])
            if h > 3:
                F.set(x, h - 2, BRASS[1])
    return F


def p_cord(c, f, w, h, rng):
    """A mobile's cord: dark waxed thread, a lighter twist every other texel."""
    F = Face(w, h, (58, 42, 30, 255))
    for y in range(0, h, 2):
        for x in range(w):
            F.set(x, y, (92, 70, 48, 255))
    return F


LEATHER = [(46, 22, 18, 255), (78, 36, 28, 255), (112, 52, 36, 255), (146, 74, 48, 255)]
GREEN_BOOK = [(20, 40, 34, 255), (34, 66, 52, 255), (52, 94, 72, 255), (78, 124, 96, 255)]
PAPER = [(196, 176, 136, 255), (226, 210, 172, 255)]
NAIL = (90, 86, 88, 255)
# the planets' sigils, 3 x 3, brass on the apron's panels (Ember's spark, Verdigris's leaf, Old Gold's ring,
# Pale Rider's crescent, Indigo's drop, Cinder's coal)
SIGILS = [["#.#", ".#.", "#.#"], [".#.", "###", ".#."], ["###", "#.#", "###"],
          ["##.", "#..", "##."], [".#.", "#.#", ".#."], ["...", ".#.", "..."]]


def grain(F, R, i, w, h):
    """Wood grain by shape: a darker seam every 4th row, broken in hand-placed gaps (no noise)."""
    for y in range(2, h, 4):
        for x in range(w):
            if (x * 7 + y * 3) % 13 < 3:
                continue
            if F.get(x, y) == R[i]:
                F.set(x, y, R[max(0, i - 1)])


def p_top(c, f, w, h, rng):
    """The table's top: walnut with grain, shaded corner to corner; the zodiac ring round the edge (brass rims, a tick
    every 30 degrees, a pale star between ticks), the planets' orbit inlays, a compass rose in the middle (north
    pale blue); its sides grained with a brass edge."""
    R = WALNUT
    i = 1 if f == "down" else 3 if f == "up" else 2   # sides one tone (the game shades them); top lighter
    F = Face(w, h, R[i])
    if f != "up":
        grain(F, R, i, w, h)
        tm.bevel(F, R, i, w, h)
        for x in range(1, w - 1):
            F.set(x, 0, BRASS[3] if f in ("north", "west") else BRASS[2])
        return F
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            k = i                                                   # flat: a 3 x 3 top shaded corner to corner reads as two halves
            F.set(x, y, R[max(0, min(4, k))])
    grain(F, R, i, w, h)

    def lit(x, y):
        return (x - cx) + (y - cy) < 0

    for y in range(h):
        for x in range(w):
            r = math.hypot(x - cx, y - cy)
            ang = math.degrees(math.atan2(y - cy, x - cx)) % 360
            if abs(r - 21.6) < 0.5 or abs(r - 18.6) < 0.5:                 # the zodiac band's two rims
                F.set(x, y, BRASS[3])                                 # one tone all round (half-dark read as half a ring)
            elif 18.6 < r < 21.6:
                if min(ang % 30, 30 - ang % 30) < 3.2:                      # a tick every 30 degrees
                    F.set(x, y, BRASS[2])
                elif abs(r - 20.1) < 0.6 and abs((ang % 30) - 15) < 1.6:   # a little star between ticks
                    F.set(x, y, lm.RAMPS["star"][4])
                else:
                    F.set(x, y, R[max(0, i - 1)])
            elif r < 18:
                for rr in c.info.get("orbits", []):
                    if abs(r - rr) < 0.5:
                        F.set(x, y, BRASS[2])
    # the compass rose round the drum: north (the up face's top = -Z) in the star's pale blue, the others brass
    ix, iy = int(cx), int(cy)
    for k in range(5, 9):
        F.set(ix, iy - k, lm.RAMPS["star"][3])
        F.set(ix + 1, iy - k, lm.RAMPS["star"][2])
        F.set(ix, iy + 1 + k, BRASS[2])
        F.set(ix + 1, iy + 1 + k, BRASS[1])
        F.set(ix - k, iy, BRASS[3])
        F.set(ix - k, iy + 1, BRASS[2])
        F.set(ix + 1 + k, iy, BRASS[2])
        F.set(ix + 1 + k, iy + 1, BRASS[1])
    for k in range(5, 7):
        for (sx, sy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            F.set(ix + (sx > 0) + sx * k, iy + (sy > 0) + sy * k, BRASS[2])
    tm.bevel(F, R, i, w, h)
    return F


def p_apron(c, f, w, h, rng):
    """The apron under the top: grained walnut, a brass-framed panel on each side with the six planets' sigils."""
    R = WALNUT
    i = 1 if f == "down" else 3 if f == "up" else 2   # sides one tone (the game shades them); top lighter
    F = Face(w, h, R[i])
    grain(F, R, i, w, h)
    if f in ("north", "south", "east", "west") and w > 12 and h >= 5:
        x0, x1, y0, y1 = 3, w - 4, 0, h - 1
        for x in range(x0, x1 + 1):
            F.set(x, y0, BRASS[3])
            F.set(x, y1, BRASS[1])
        for y in range(y0, y1 + 1):
            F.set(x0, y, BRASS[3])
            F.set(x1, y, BRASS[1])
        for x in range(x0 + 1, x1):
            for y in range(y0 + 1, y1):
                F.set(x, y, R[max(0, i - 1)])
        step = (x1 - x0) / (len(SIGILS) + 1)
        for k, sg in enumerate(SIGILS):
            sx = int(x0 + step * (k + 1)) - 1
            for yy, row in enumerate(sg):
                for xx, ch in enumerate(row):
                    if ch == "#":
                        F.set(sx + xx, y0 + 1 + yy, BRASS[4] if yy == 0 else BRASS[3])
    tm.bevel(F, R, i, w, h)
    return F


def p_leg(c, f, w, h, rng):
    """A turned walnut leg: carved rings (a dark groove under a light lip) every 3 texels, a brass band at the top."""
    R = WALNUT
    i = 1 if f == "down" else 3 if f == "up" else 2   # sides one tone (the game shades them); top lighter
    F = Face(w, h, R[i])
    if f in ("north", "south", "east", "west"):
        for y in range(3, h - 1, 3):
            for x in range(w):
                F.set(x, y, R[max(0, i - 1)])
                F.set(x, y - 1, R[min(4, i + 1)])
        for x in range(w):
            F.set(x, 0, BRASS[3])
    tm.bevel(F, R, i, w, h)
    return F


def p_shelf(c, f, w, h, rng):
    """The lower shelf: walnut planks with a seam every 6 texels and nails at their ends."""
    R = WALNUT
    i = 1 if f == "down" else 3 if f == "up" else 2   # sides one tone (the game shades them); top lighter
    F = Face(w, h, R[i])
    if f == "up":
        for y in range(5, h, 6):
            for x in range(w):
                F.set(x, y, R[max(0, i - 1)])
        for y in range(2, h, 6):
            for x in (1, w - 2):
                F.set(x, y, NAIL)
                F.set(x, y + 1, NAIL)
    tm.bevel(F, R, i, w, h)
    return F


def p_book(c, f, w, h, rng):
    """A book lying flat: a leather cover, the page block on three sides, gold bands on the spine (west)."""
    L = LEATHER if c.info.get("cover") == "red" else GREEN_BOOK
    i = min(tm.idx(c, f, L, 2), 3)
    F = Face(w, h, L[i])
    if f in ("east", "south", "north") and h >= 2:
        for x in range(1, w - 1):
            for y in range(h):
                if 0 < y < h - 1 or h == 2:
                    F.set(x, y, PAPER[1] if y % 2 else PAPER[0])
    if f == "west":
        for x in range(1, w - 1, 3):
            for y in range(h):
                F.set(x, y, BRASS[3])
                if x + 1 < w - 1:
                    F.set(x + 1, y, BRASS[3])
    if f == "up" and w >= 6:
        for x in range(2, w - 2):
            F.set(x, 1, BRASS[3])
            F.set(x, h - 2, BRASS[2])
    return F


IRON = [(40, 38, 44, 255), (66, 62, 68, 255), (98, 94, 98, 255), (138, 134, 134, 255)]


def p_rose(c, f, w, h, rng):
    """The ceiling rose: a brass plate, a ring of rivets near its edge and a darker boss round the chain."""
    i = tm.idx(c, f, BRASS, 2)
    F = Face(w, h, BRASS[i])
    if f in ("down", "up"):
        for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2), (w // 2, 1), (1, h // 2)):
            F.set(x, y, BRASS[4])
        for x in range(w // 2 - 2, w // 2 + 2):
            for y in range(h // 2 - 2, h // 2 + 2):
                F.set(x, y, BRASS[1])
    tm.bevel(F, BRASS, i, w, h)
    return F


def p_chain(c, f, w, h, rng):
    """Two iron chain links: a lit link over a dark one, the gap of each link dark."""
    F = Face(w, h, IRON[2])
    for y in range(h):
        for x in range(w):
            F.set(x, y, IRON[3] if (y // 1) % 2 == 0 and x == 0 else IRON[1] if y % 2 else IRON[2])
    return F


PAINT = dict(lm.PAINT, table=p_table, cord=p_cord, top=p_top, apron=p_apron, leg=p_leg, shelf=p_shelf, book=p_book,
             rose=p_rose, chain=p_chain)


# ------------------------------------------------------------------ sweep check
def bands(root):
    """[(rotor, name, y0, y1, r0, r1)] for every cube: the ring it covers turning about the middle."""
    out = []
    for b, c in T.all_cubes(root):
        rotor = "still"
        bb = b
        while bb is not None:
            if bb.name.startswith("orbit_") or bb.name in ("hub", "sun_spin"):
                rotor = bb.name
                break
            bb = bb.parent
        x0, x1 = sorted((c.a[0], c.b[0]))
        z0, z1 = sorted((c.a[2], c.b[2]))
        near_x = 0 if x0 <= 0 <= x1 else min(abs(x0), abs(x1))
        near_z = 0 if z0 <= 0 <= z1 else min(abs(z0), abs(z1))
        far = max(math.hypot(x, z) for x in (x0, x1) for z in (z0, z1))
        y0, y1 = sorted((c.a[1], c.b[1]))
        out.append((rotor, c.name, y0, y1, math.hypot(near_x, near_z), far))
    return out


def sweep(root, allow=()):
    bad = []
    bs = bands(root)
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            a, b = bs[i], bs[j]
            if a[0] == b[0] or (a[1], b[1]) in allow or (b[1], a[1]) in allow:
                continue
            if a[2] < b[3] - 1e-6 and b[2] < a[3] - 1e-6 and a[4] < b[5] - 1e-6 and b[4] < a[5] - 1e-6:
                bad.append((a[0], a[1], b[0], b[1]))
    return bad


def planet(parent, gid, r, arm_y, ball_y0, pivot_y, hang=None, ring=True, angle=0):
    """One planet's bone: a collar round the column at arm_y, an arm out to radius r, the ball (and for the mobile a
    cord down to it). The arm's end sits under the ball (or the cord hangs from it)."""
    s = SIZES[gid]
    h = s // 2
    o = Bone("orbit_" + gid, (0, pivot_y, 0), rot=(0, angle, 0), parent=parent)   # rest angle: spread round
    box(o, "collar_" + gid, (-2, arm_y, -2), (2, arm_y + 1, 2), "brass", lift=1)
    box(o, "arm_" + gid, (2, arm_y, -1), (r + 1, arm_y + 1, 1), "ring")
    if hang is not None:                                   # the mobile: a brass knob under the arm's end, the cord
        box(o, "knob_" + gid, (r - 1, arm_y - 1, -1), (r + 1, arm_y, 1), "brass", lift=1)
        if arm_y - 1 > ball_y0 + s:                        # (a ball right under its knob hangs on it directly)
            box(o, "cord_" + gid, (r, ball_y0 + s, 0), (r + 1, arm_y - 1, 1), "cord")
    box(o, "ball_" + gid, (r - h, ball_y0, -h), (r + h, ball_y0 + s, h), "globe", globe=gid)
    if gid == "old_gold" and ring:                         # its ring, flat round its middle
        box(o, "og_ring_" + gid, (r - h - 1, ball_y0 + h, -h - 1), (r + h + 1, ball_y0 + h + 1, h + 1), "ring", lift=1)
    return o


# ------------------------------------------------------------------ Grand Orrery
# A table (its top at y 15) on four carved legs with brass shoes, a shelf with two books, an apron with the planets'
# sigils, a gallery rail with corner finials, a zodiac top with a compass rose round a brass drum. Above it the planets
# in three tiers: in each, an arm that reaches further sits lower, so it passes under the nearer balls; each tier's arms
# sit above the tier below's balls. The sun on the column's top, the top tier's arm under it. Three blocks tall.
UP = 11            # the planets sit this much higher than on the first draft's flat base (the top is at y 15)
GRAND = [  # id, radius, arm y, ball bottom y
    ("cinder", 5, 8 + UP, 9 + UP), ("pale_rider", 11, 7 + UP, 8 + UP), ("old_gold", 19, 6 + UP, 7 + UP),
    ("ember", 6, 16 + UP, 17 + UP), ("indigo", 14, 15 + UP, 16 + UP),
    ("verdigris", 18, 24 + UP, 25 + UP),
]


def grand():
    root = Bone("root", (0, 0, 0))
    orbits = [r for (_, r, _, _) in GRAND]
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, z0 = (18 if sx > 0 else -22), (18 if sz > 0 else -22)
            box(root, f"shoe_{sx}{sz}", (x0 - 1, 0, z0 - 1), (x0 + 5, 2, z0 + 5), "brass")
            box(root, f"leg_{sx}{sz}", (x0, 2, z0), (x0 + 4, 9, z0 + 4), "leg")
    box(root, "shelf", (-18, 4, -18), (18, 5, 18), "shelf")
    box(root, "book_red", (-12, 5, 4), (-2, 7, 12), "book", cover="red")
    box(root, "book_green", (-10, 7, 5), (-4, 8, 11), "book", cover="green")
    box(root, "apron", (-22, 9, -22), (22, 13, 22), "apron")
    box(root, "top", (-24, 13, -24), (24, 15, 24), "top", orbits=orbits)
    box(root, "rail_n", (-22, 15, -24), (22, 16, -23), "ring", lift=1)
    box(root, "rail_s", (-22, 15, 23), (22, 16, 24), "ring", lift=-1)
    box(root, "rail_w", (-24, 15, -22), (-23, 16, 22), "ring")
    box(root, "rail_e", (23, 15, -22), (24, 16, 22), "ring", lift=-1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, z0 = (22 if sx > 0 else -24), (22 if sz > 0 else -24)
            box(root, f"finial_{sx}{sz}", (x0, 15, z0), (x0 + 2, 18, z0 + 2), "brass", lift=1)
    box(root, "drum", (-4, 15, -4), (4, 17, 4), "brass", bands=[1])
    box(root, "column", (-1, 17, -1), (1, 26 + UP, 1), "brass", lift=1)
    for k, (gid, r, ay, by) in enumerate(GRAND):
        planet(root, gid, r, ay, by, ay, ring=False, angle=(k * 137) % 360)   # Old Gold's ring would reach past the top
    sun = Bone("sun_spin", (0, 29 + UP, 0), parent=root)
    box(sun, "sun", (-3, 26 + UP, -3), (3, 32 + UP, 3), "globe", globe="star")
    return root


# ------------------------------------------------------------------ the mobile
# three groups of two hang one under another from the hook (y 32). In each group the outer arm is higher, so it passes
# over the inner planet's cord; each group's arms sit under the group above's balls. The sun hangs at the rod's end.
MOBILE = [  # id, radius, arm y, ball bottom y
    ("ember", 6, 29, 21), ("old_gold", 18, 30, 20),
    ("verdigris", 6, 18, 11), ("indigo", 17, 19, 10),
    ("cinder", 7, 8, 2), ("pale_rider", 16, 9, 1),
]


def mobile():
    root = Bone("root", (0, 0, 0))
    box(root, "rose", (-4, 31, -4), (4, 32, 4), "rose")             # the ceiling rose, riveted to the ceiling
    box(root, "chain", (-1, 29, -1), (1, 31, 1), "chain")
    box(root, "rod", (-1, 7, -1), (1, 29, 1), "brass", bands=[2, 9, 20])
    for k, (gid, r, ay, by) in enumerate(MOBILE):
        planet(root, gid, r, ay, by, ay, hang=True, angle=(k * 137) % 360)
    sun = Bone("sun_spin", (0, 4, 0), parent=root)
    box(sun, "sun", (-3, 1, -3), (3, 7, 3), "globe", globe="star")
    for n, (x0, z0, x1, z1) in enumerate(((3, -1, 4, 1), (-4, -1, -3, 1), (-1, 3, 1, 4), (-1, -4, 1, -3))):
        box(sun, f"ray_{n}", (x0, 3, z0), (x1, 5, z1), "globe", globe="star")   # four short rays round its middle
    return root


def build(name, fn, allow):
    root = fn()
    for b, c in T.all_cubes(root):
        assert all(abs(v - round(v)) < 1e-6 for v in c.a + c.b), (name, c.name)
    clashes = sweep(root, allow)
    for x in clashes:
        print(name, "CLASH:", x)
    for x in tm.check_planes(root):
        print(name, "same plane:", x)
    tm.light_pass(root)
    T.PAINT, T.NAME, T.ROOT = PAINT, name, ROOT / "models" / name
    T.ROOT.mkdir(parents=True, exist_ok=True)
    path, n, size = T.write(root)
    print(path, n, "cubes", size, "clashes", len(clashes))


def main():
    collars = set()
    for gid, *_ in GRAND + MOBILE:
        collars |= {("collar_" + gid, "column"), ("collar_" + gid, "rod"), ("collar_" + gid, "chain")}
    which = sys.argv[1:] or ["grand_orrery", "planet_mobile"]
    if "grand_orrery" in which:
        build("grand_orrery", grand, collars)
    if "planet_mobile" in which:
        build("planet_mobile", mobile, collars)


if __name__ == "__main__":
    main()
