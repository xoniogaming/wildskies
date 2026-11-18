"""The Star Lamp's new model (1.1.0 redesign, owner: "a mix of 7 and 2": a planet lamp and a little armillary).

    python tools/lamp/lamp_model.py   -> models/star_lamp/star_lamp.bbmodel + textures/star_lamp(_glowmask).png

By the telescope's rules (tools/telescope/telescope_model.py): whole pixels, even widths centred on 0, detail painted,
ramps, bevelled faces, light from the top left, inside the block (y <= 16), cutout only.

A walnut base with a brass inlay ring, a short brass stem, and on it two brass rings that never meet:
  ring_a  a tall upright ring (14 x 12, in its own plane) with an axle top and bottom, turning slowly about the stem
  ring_b  a flat ring round the globe, turning the other way faster, with the globe inside it (they turn together)
The globe is one of seven bones (globe_star, globe_ember ... globe_cinder), all but the chosen one hidden; every
globe texel glows (the glowmask). ring_a sweeps radius 7..8; ring_b, its globe and Old Gold's ring stay within 6.7, so they never cross.

Bones the Java uses: root, ring_a, ring_b, globe_<id>.
"""
import importlib.util
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("wb", ROOT / "tools/weather_blocks/models.py")
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)
tm, T = wb.tm, wb.T
Bone, box, Face = T.Bone, T.box, T.Face
BRASS, WALNUT, STAR = tm.BRASS, tm.WALNUT, tm.STAR
idx, bevel = tm.idx, tm.bevel

# each globe's ramp (dark -> light) is its star-view sprite's own palette (textures/gui/planets.png, planet_<id>_3)
RAMPS = {
    "star": [(40, 70, 140), (70, 110, 186), (120, 168, 226), (170, 210, 246), (214, 236, 255), (246, 252, 255)],
    "ember": [(54, 12, 12), (108, 28, 20), (160, 52, 28), (204, 88, 44), (234, 134, 74), (252, 194, 130)],
    "verdigris": [(14, 48, 56), (26, 88, 88), (48, 130, 116), (92, 174, 146), (150, 212, 180), (214, 240, 214)],
    "old_gold": [(70, 44, 14), (126, 88, 28), (176, 132, 46), (212, 174, 82), (238, 210, 130), (252, 238, 190)],
    "pale_rider": [(70, 80, 110), (122, 134, 166), (172, 184, 210), (212, 220, 238), (238, 242, 252), (255, 255, 255)],
    "indigo": [(16, 18, 58), (32, 38, 102), (52, 64, 146), (82, 100, 186), (126, 148, 220), (184, 202, 246)],
    "cinder": [(26, 24, 30), (50, 46, 52), (78, 72, 76), (110, 102, 102), (144, 136, 132), (184, 176, 166)],
}
RAMPS = {k: [c + (255,) for c in v] for k, v in RAMPS.items()}
GLOBES = list(RAMPS)
LAVA = (252, 194, 130, 255)
WHITE = (238, 242, 252, 255)
CENTRE = 10          # the globe's middle, and both rings'
# globe sizes (owner: "the actual size of the planets"): the Orrery's sizes doubled (Cinder 2, the middle three 3,
# Indigo 3 but an ice giant here, Old Gold 4), the star as big as the biggest
SIZES = {"star": 8, "ember": 6, "verdigris": 6, "old_gold": 8, "pale_rider": 6, "indigo": 8, "cinder": 4}
SIDE_LIGHT = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}   # light from the top left front

# marks on the 8 x 8 side faces, by planet: (x, y, step change or colour); faces get them shifted round by face
MARKS = {
    "ember": [(2, 2, -1), (3, 2, -1), (2, 3, -1), (5, 4, -1), (6, 4, -1), (1, 5, -1), (4, 1, 1), (6, 6, LAVA), (5, 7, LAVA)],
    "cinder": [(2, 2, -1), (3, 3, -1), (2, 1, 1), (5, 5, -1), (6, 5, -1), (5, 4, 1), (1, 6, -1), (6, 2, -1)],
    "verdigris": "bands:2+,3-,5+",
    "old_gold": "bands:1+,3-,4+,6-",
    "pale_rider": "bands:3-,6-",
    "indigo": "bands:1-,4-,6+",
}


def p_globe(c, f, w, h, rng):
    """A globe shaded like a ball: each face lit by its side (top brightest, bottom darkest), brighter toward the
    top-left and darker toward its edges, so the cube reads round; then the planet's own marks (bands, craters,
    Ember's lava, Verdigris's and Indigo's storm spots, the star's sparkle). Every texel glows (the glowmask)."""
    g = c.info["globe"]
    R = RAMPS[g]
    F = Face(w, h, R[2])
    side = f in ("north", "south", "east", "west")
    turn = {"north": 0, "east": 2, "south": 4, "west": 6, "up": 1, "down": 3}[f]
    marks = MARKS.get(g, [])
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5
            k = SIDE_LIGHT[f] - (dx + dy) * 1.6 - (dx * dx + dy * dy) * 3.2
            if g == "star":
                k += 1
            if isinstance(marks, str) and side:
                for b in marks[6:].split(","):
                    if int(b[:-1]) == y:
                        k += 1 if b[-1] == "+" else -1
            F.set(x, y, R[max(0, min(5, int(round(k))))])
    if isinstance(marks, list):
        for (mx, my, d) in marks:
            x, y = (mx + turn) % w, (my + (turn // 2)) % h
            if isinstance(d, tuple):
                if side:
                    F.set(x, y, d)
            else:
                cur = R.index(F.get(x, y)) if F.get(x, y) in R else 2
                F.set(x, y, R[max(0, min(5, cur + d))])
    if g == "verdigris" and f == "north":
        F.set(5, 2, WHITE)
    if g == "indigo" and f == "west":
        F.set(2, 4, R[5])
        F.set(3, 4, WHITE)
    if g == "star" and f in ("north", "west", "up"):
        F.set(2, 2, (255, 255, 255, 255))
    for y in range(h):
        for x in range(w):
            F.shine(x, y, F.get(x, y))
    return F


def p_base(c, f, w, h, rng):
    """The walnut base: bevelled and shaded (lit at the top-left, dark at the bottom-right), a brass inlay ring with
    its own light and dark side on top, a brass line round its sides."""
    R = WALNUT
    i = idx(c, f, R, 2)
    F = Face(w, h, R[i])
    if f == "up":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                k = i - round(((x - cx) + (y - cy)) / w * 1.4)
                F.set(x, y, R[max(0, min(4, k))])
                r = math.hypot(x - cx, y - cy)
                if abs(r - 4.6) < 0.5:
                    F.set(x, y, BRASS[3])
    bevel(F, R, i, w, h)
    if f in ("north", "south", "east", "west") and h >= 2:
        for x in range(1, w - 1):
            F.set(x, 0, BRASS[3] if f in ("north", "west") else BRASS[2])
    return F


def p_ring(c, f, w, h, rng):
    """A brass ring's bar: shaded from a bright end to a dark end along its length (the light is up-left),
    graduated with a dark tick every other texel, bevelled."""
    i = idx(c, f, BRASS, 2 + c.info.get("lift", 0))
    F = Face(w, h, BRASS[i])
    n = max(w, h)
    for y in range(h):
        for x in range(w):
            t = (x if w >= h else y) / max(1, n - 1)
            k = i + (1 if t < 0.25 else 0 if t < 0.7 else -1) if n <= 16 else i   # long rails stay one tone
            F.set(x, y, BRASS[max(0, min(4, k))])
    if c.info.get("ticks") and f in ("north", "south"):
        if w > h:
            for x in range(1, w - 1, 2):
                F.set(x, 0, BRASS[max(0, i - 2)])
        else:
            for y in range(1, h - 1, 2):
                F.set(0, y, BRASS[max(0, i - 2)])
    bevel(F, BRASS, i, w, h)
    return F


def lamp():
    root = Bone("root", (0, 0, 0))
    box(root, "base", (-6, 0, -6), (6, 2, 6), "base")
    box(root, "stem", (-1, 2, -1), (1, 3, 1), "brass", lift=1)
    a = Bone("ring_a", (0, CENTRE, 0), parent=root)              # 16 wide, 13 tall: sweeps radius 7..8
    box(a, "a_bottom", (-8, 3, -1), (8, 4, 1), "ring", ticks=True)
    box(a, "a_top", (-8, 15, -1), (8, 16, 1), "ring", ticks=True, lift=1)
    box(a, "a_west", (-8, 4, -1), (-7, 15, 1), "ring", ticks=True)
    box(a, "a_east", (7, 4, -1), (8, 15, 1), "ring", ticks=True, lift=-1)
    box(a, "axle_low", (-1, 4, -1), (1, 6, 1), "brass")
    box(a, "axle_high", (-1, 14, -1), (1, 15, 1), "brass")
    b = Bone("ring_b", (0, CENTRE, 0), parent=root)              # an open octagon band: corners at radius 6.4
    box(b, "b_north", (-4, 10, -5), (4, 11, -4), "ring", lift=1)
    box(b, "b_south", (-4, 10, 4), (4, 11, 5), "ring", lift=-1)
    box(b, "b_west", (-5, 10, -4), (-4, 11, 4), "ring")
    box(b, "b_east", (4, 10, -4), (5, 11, 4), "ring", lift=-1)
    for gid in GLOBES:
        g = Bone("globe_" + gid, (0, CENTRE, 0), parent=b)
        r = SIZES[gid] // 2                                       # its size, like the Orrery's planets
        box(g, "ball_" + gid, (-r, CENTRE - r, -r), (r, CENTRE + r, r), "globe", globe=gid)
        if r < 4:                                                 # pins up to the axles (6 and 14), so it doesn't float
            box(g, "pin_lo_" + gid, (-1, 6, -1), (1, CENTRE - r, 1), "brass")
            box(g, "pin_hi_" + gid, (-1, CENTRE + r, -1), (1, 14, 1), "brass")
        if gid == "old_gold":                                     # Old Gold's own ring, out past the band
            box(g, "og_n", (-3, 10, -6), (3, 11, -5), "ring", lift=1)
            box(g, "og_s", (-3, 10, 5), (3, 11, 6), "ring", lift=-1)
            box(g, "og_w", (-6, 10, -3), (-5, 11, 3), "ring")
            box(g, "og_e", (5, 10, -3), (6, 11, 3), "ring", lift=-1)
    return root


PAINT = {"brass": tm.p_brass, "base": p_base, "ring": p_ring, "globe": p_globe}


def main():
    root = lamp()
    for bn, c in T.all_cubes(root):
        assert all(abs(v - round(v)) < 1e-6 for v in c.a + c.b), c.name
        assert max(c.a[1], c.b[1]) <= 16, c.name
    for x in tm.check_planes(root):
        if "ball_" in x[1] and "ball_" in x[2]:
            continue                       # the seven globes share one place: only one is ever shown
        print("same plane:", x)
    tm.light_pass(root)
    T.PAINT, T.NAME, T.ROOT = PAINT, "star_lamp", ROOT / "models" / "star_lamp"
    T.ROOT.mkdir(parents=True, exist_ok=True)
    path, n, size = T.write(root)
    print(path, n, "cubes", size)


if __name__ == "__main__":
    main()
