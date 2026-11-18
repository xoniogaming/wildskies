"""The North Star Lodestone's model (redo 2026-11-18, owner picked "a brass star on a post that turns to face north").

    python tools/lodestone/lodestone_model.py   -> models/north_star_lodestone/north_star_lodestone.bbmodel + textures

By the telescope's rules (tools/telescope/telescope_model.py): whole pixels, even widths centred on 0, detail painted,
ramps, every face bevelled, light from the top left, inside the block (y <= 16), cutout only.

A squat lodestone (the vanilla block it is made from: dark magnetic stone, iron straps, brass corner caps), a walnut
cap with a compass-rose inlay, an iron post with a brass collar, and on it the `star` bone: an eight-point brass star
standing up with a pale blue heart, and under it a needle whose pale blue tip points north (-Z). The renderer turns the
`star` bone so the tip points to the world's north whichever way the block was placed (it only moves while it settles).

Bones the Java uses: root, star (turned about Y), heart (its glow: brighter while the viewer is bound here).
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
BRASS, WALNUT, IRON, STAR = tm.BRASS, tm.WALNUT, tm.IRON, tm.STAR
idx, bevel = tm.idx, tm.bevel

LODE = ramp((34, 32, 36), (52, 50, 56), (74, 72, 78), (100, 98, 104))   # vanilla lodestone's dark stone, cooler


def p_lode(c, f, w, h, rng):
    """The lodestone: dark stone in chiselled courses, an iron strap round its middle, rivets on the strap."""
    i = idx(c, f, LODE, 2)
    F = Face(w, h, LODE[i])
    if f in ("north", "south", "east", "west"):
        for x in range(1, w - 1):                     # a chisel line under the cap and one above the foot
            F.set(x, 1, LODE[max(0, i - 1)])
        for y in range(2, h - 1):                     # joints, staggered by the course
            for x in (w // 3, 2 * w // 3):
                F.set(x, y, LODE[max(0, i - 1)])
        for (x, y) in ((w // 3 + 1, 3), (2 * w // 3 - 2, h - 2)):     # the lodestone's pale blue glints
            F.set(x, y, STAR[1])
        mid = h // 2                                  # the iron strap and its rivets
        for x in range(w):
            F.set(x, mid, IRON[1])
            F.set(x, mid + 1, IRON[0])
        for x in (2, w - 3):
            F.set(x, mid, IRON[3])
    elif f == "up":
        for x in range(w):
            for y in range(h):
                if (x + 2 * y) % 7 == 0 and 0 < x < w - 1 and 0 < y < h - 1:
                    F.set(x, y, LODE[min(3, i + 1)])
    bevel(F, LODE, i, w, h)
    return F


def p_corner(c, f, w, h, rng):
    """A brass corner cap: bevelled, a lit rivet head in the middle of each side, its top a pyramid of light."""
    i = idx(c, f, BRASS, 2)
    F = Face(w, h, BRASS[i])
    bevel(F, BRASS, i, w, h)
    if f in ("north", "south", "east", "west") and h >= 3:
        F.set(w // 2, 1, BRASS[min(4, i + 2)])
        F.set(w // 2, 2, BRASS[max(0, i - 1)])
    return F


def p_cap(c, f, w, h, rng):
    """The walnut cap: on top a brass compass rose inlay (N arm pale blue); a brass line round its sides."""
    R = WALNUT
    i = idx(c, f, R, 2)
    F = Face(w, h, R[i])
    bevel(F, R, i, w, h)
    if f == "up":
        cx, cy = w // 2, h // 2
        for k in range(1, cx - 1):
            F.set(cx - 1, cy - 1 - k, STAR[1] if k > 1 else BRASS[3])     # north (top of the up face = -Z)
            F.set(cx, cy - 1 - k, STAR[2] if k > 1 else BRASS[3])
            F.set(cx - 1, cy + k, BRASS[1])                                # south
            F.set(cx, cy + k, BRASS[2])
            F.set(cx - 1 - k, cy - 1, BRASS[2])                            # west, east
            F.set(cx + k, cy, BRASS[1])
        for (x, y) in ((cx - 1, cy - 1), (cx, cy - 1), (cx - 1, cy), (cx, cy)):
            F.set(x, y, BRASS[3])
    elif f in ("north", "south", "east", "west") and h >= 2:
        for x in range(1, w - 1):
            F.set(x, h - 1, BRASS[1])
    return F


def p_star(c, f, w, h, rng):
    """The brass star: lit faces, a darker groove down each arm on the broad faces."""
    i = idx(c, f, BRASS, 2 + c.info.get("lift", 0))
    F = Face(w, h, BRASS[i])
    if f in ("north", "south") and c.info.get("groove"):
        if w > h:
            for x in range(1, w - 1):
                F.set(x, h // 2, BRASS[max(0, i - 1)])
        elif h > w:
            for y in range(1, h - 1):
                F.set(w // 2, y, BRASS[max(0, i - 1)])
    bevel(F, BRASS, i, w, h)
    return F


def p_heart(c, f, w, h, rng):
    """The pale blue heart in the star's middle: glows (the glowmask)."""
    F = Face(w, h, STAR[1])
    for y in range(h):
        for x in range(w):
            F.shine(x, y, STAR[2] if (x, y) != (0, 0) else STAR[3])
    return F


def p_tip(c, f, w, h, rng):
    """The needle's north tip, pale blue, its top lit (glows faintly)."""
    F = Face(w, h, STAR[1])
    if f == "up":
        for x in range(w):
            F.shine(x, 0, STAR[2])
    return F


def lodestone():
    root = Bone("root", (0, 0, 0))
    box(root, "lode", (-7, 0, -7), (7, 5, 7), "lode")
    for sx in (-1, 1):                                        # brass corner caps over the lodestone's top corners
        for sz in (-1, 1):
            box(root, f"cap_{sx}{sz}", (6 if sx > 0 else -8, 3, 6 if sz > 0 else -8),
                (8 if sx > 0 else -6, 6, 8 if sz > 0 else -6), "corner")
    box(root, "cap", (-6, 5, -6), (6, 7, 6), "cap")
    box(root, "post", (-1, 7, -1), (1, 8, 1), "iron")
    box(root, "collar", (-2, 8, -2), (2, 9, 2), "brass", lift=1)
    star = Bone("star", (0, 9, 0), parent=root)
    # the needle under the star: brass fletch to the south, pale blue tip to the north (-Z)
    box(star, "needle", (-1, 9, -3), (1, 10, 4), "star_part", lift=0)
    box(star, "tip", (-1, 9, -6), (1, 10, -3), "tip")
    box(star, "tail", (-1, 9, 4), (1, 11, 6), "star_part", lift=-1)        # a fletch
    # the eight-point star, standing up, its face to the north: long up/down and side arms, four short points
    box(star, "spine", (-1, 10, -1), (1, 16, 1), "star_part", groove=True, lift=1)
    box(star, "arm_w", (-4, 12, -1), (-1, 14, 1), "star_part")
    box(star, "arm_e", (1, 12, -1), (4, 14, 1), "star_part")
    for (x, y) in ((-2, 14), (1, 14), (-2, 11), (1, 11)):
        box(star, f"pt_{x}_{y}", (x, y, -1), (x + 1, y + 1, 1), "star_part", lift=1)
    heart = Bone("heart", (0, 12, 0), parent=star)
    box(heart, "heart_n", (-1, 12, -2), (1, 14, -1), "heart")
    box(heart, "heart_s", (-1, 12, 1), (1, 14, 2), "heart")
    return root


PAINT = {"brass": tm.p_brass, "corner": p_corner, "iron": tm.p_iron, "lode": p_lode, "cap": p_cap, "star_part": p_star,
         "heart": p_heart, "tip": p_tip}


def main():
    root = lodestone()
    for b, c in T.all_cubes(root):
        assert all(abs(v - round(v)) < 1e-6 for v in c.a + c.b), c.name
        assert max(c.a[1], c.b[1]) <= 16, c.name
    for x in tm.check_planes(root):
        print("same plane:", x)
    tm.light_pass(root)
    T.PAINT, T.NAME, T.ROOT = PAINT, "north_star_lodestone", ROOT / "models" / "north_star_lodestone"
    T.ROOT.mkdir(parents=True, exist_ok=True)
    path, n, size = T.write(root)
    print(path, n, "cubes", size)


if __name__ == "__main__":
    main()
