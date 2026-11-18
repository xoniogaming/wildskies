"""The telescope block's model, started over from scratch (0.8.0, owner: "completely start over, start fresh").

    python tools/telescope/telescope_model.py      -> models/telescope/telescope.bbmodel + textures/telescope(_glowmask).png

Built by the custom-block-mods rules (references/models.md, vanilla-style.md):
  - whole pixels: every size and position whole (even widths centred on 0), 1 texel per pixel
  - few thick parts: legs 2 px, tube 4 px; detail painted, not modelled (the leather grip, its lacing, the brass
    bands, the shoes on the legs, the scale on the yoke are all texture)
  - ramps, not blends: brass, walnut, leather, iron, night glass, star glass, nebula glass; light from the top left,
    every face bevelled (lit top/left edge, dark bottom/right edge) so each part reads as a solid piece
  - no two visible faces in one plane facing the same way
A frontier stargazer's brass refractor: walnut tripod with brass shoes and an accessory tray holding two spare
eyepieces, a brass hub and turntable, a yoke with a trunnion bolt, the tube with a dew cap, a leather grip, a raised
ring, a finder scope on two brackets, the focuser and an eyepiece pointing up at the back.

Bones are the contract with client/TelescopeRenderer: root, legs, head, tube, lens_cell (tier >= 1: a Star Lens cell
on the objective, its glint glows), filter_slide (tier 2: the Nebula Filter's slide through the focuser). The model
faces north (-Z): the objective is the front. Origin = bottom centre of the block. The glowmask must never be empty.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / "models" / "telescope"
spec = importlib.util.spec_from_file_location(
    "tmpl", Path.home() / ".claude/skills/boss-mods/scripts/boss_model_template.py")
T = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = [sys.argv[0]]
spec.loader.exec_module(T)
sys.argv = _argv
Bone, box, seg, Face, ramp, mat = T.Bone, T.box, T.seg, T.Face, T.ramp, T.mat

# ------------------------------------------------------------------ ramps (dark -> light), warm hands and cold sky
BRASS = ramp((70, 42, 14), (124, 82, 26), (178, 126, 42), (222, 172, 68), (250, 224, 144))
WALNUT = ramp((46, 28, 18), (72, 45, 28), (100, 64, 39), (128, 86, 53), (156, 112, 70))
LEATHER = ramp((42, 20, 14), (70, 34, 22), (100, 52, 32), (132, 76, 46))
LACE = ramp((40, 20, 12), (176, 132, 86))
IRON = ramp((32, 32, 38), (58, 58, 66), (90, 90, 98), (130, 130, 136))
NIGHT = ramp((8, 12, 30), (18, 28, 62), (34, 52, 98))
STAR = ramp((60, 100, 170), (120, 168, 226), (190, 224, 252), (242, 250, 255))
NEBULA = ramp((58, 22, 70), (102, 42, 110), (154, 82, 158), (206, 140, 204))

ELEV = 30          # the tube's fixed rest elevation (degrees, objective up)
PIVOT = (0, 20, 0)  # the trunnion: where the tube turns in the yoke

# ------------------------------------------------------------------ light: shade by the face's world normal
NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0),
           "down": (0, -1, 0)}


def light_pass(root):
    """c.info['shade'][face]: +1 lit (facing up), 0 front/left, -1 side away, -2 underneath."""
    for b, c in T.all_cubes(root):
        R = b.R() @ (mat(c.rot) if c.rot else np.eye(3))
        sh = {}
        for f, n in NORMALS.items():
            w = R @ np.array(n, float)
            v = 0.9 * w[1] + 0.35 * w[0] - 0.25 * w[2]
            sh[f] = 1 if v > 0.55 else 0 if v > -0.05 else -1 if v > -0.6 else -2
        c.info["shade"] = sh


def idx(c, f, R, mid):
    return max(0, min(len(R) - 1, mid + c.info["shade"][f]))


def ends(c):
    """The faces the cube's long axis comes out of."""
    return ("north", "south") if c.info.get("axis") == "z" else ("up", "down")


def across(c, f, w, h, at):
    """Texels of a ring round the cube `at` px along its long axis (from the -Z end for tube parts, from the bottom
    for sticks), on face f."""
    if c.info.get("axis") == "z":
        n = c.size()[2]
        if f in ("east", "west"):
            col = at if f == "west" else n - 1 - at
            return [(col, y) for y in range(h)] if 0 <= col < w else []
        if f in ("up", "down"):
            return [(x, at) for x in range(w)] if 0 <= at < h else []
        return []
    if f in ("up", "down"):
        return []
    y = h - 1 - at
    return [(x, y) for x in range(w)] if 0 <= y < h else []


def lengthwise(c, f, w, h, k):
    """Texels of a line along the cube's long axis, k px in from the face's first edge (z-axis cubes, up face)."""
    if c.info.get("axis") == "z" and f in ("up", "down"):
        return [(k, y) for y in range(h)] if 0 <= k < w else []
    return []


def bevel(F, R, i, w, h):
    """The lit top and left edge, the dark bottom and right edge (only on texels still at the base tone)."""
    if w < 3 or h < 3:
        return
    for x in range(w):
        if F.get(x, 0) == R[i]:
            F.set(x, 0, R[min(len(R) - 1, i + 1)])
        if F.get(x, h - 1) == R[i]:
            F.set(x, h - 1, R[max(0, i - 1)])
    for y in range(1, h - 1):
        if F.get(0, y) == R[i]:
            F.set(0, y, R[min(len(R) - 1, i + 1)])
        if F.get(w - 1, y) == R[i]:
            F.set(w - 1, y, R[max(0, i - 1)])


# ------------------------------------------------------------------ painters
def p_brass(c, f, w, h, rng):
    R = BRASS
    i = idx(c, f, R, 2 + c.info.get("lift", 0))
    F = Face(w, h, R[i])
    if f in ends(c) and c.info.get("hollow") and w >= 3 and h >= 3:   # an open end: a lit lip round a dark bore
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                F.set(x, y, R[0])
        bevel(F, R, i, w, h)
        return F
    for k in c.info.get("bands", []):                      # raised bands: a dark line round the part
        for x, y in across(c, f, w, h, k):
            F.set(x, y, R[max(0, i - 1)])
    for k in c.info.get("knurl", []):                      # a knurled grip: every other line darker
        for x, y in across(c, f, w, h, k):
            if (x + y) % 2 == 0:
                F.set(x, y, R[max(0, i - 1)])
    if c.info.get("scale") and f in ("east", "west"):      # the altitude scale engraved on the yoke's arms
        for y in range(1, h - 1, 2):
            F.set(1, y, R[max(0, i - 1)])
    bevel(F, R, i, w, h)
    return F


def p_tube(c, f, w, h, rng):
    """The main tube: brass, a leather grip between two brass bands, a laced seam along its top."""
    if f in ends(c):
        return p_brass(c, f, w, h, rng)
    g0, g1 = c.info["grip"]
    i = idx(c, f, BRASS, 2)
    F = Face(w, h, BRASS[i])
    li = idx(c, f, LEATHER, 2)
    for k in range(g0, g1):
        for x, y in across(c, f, w, h, k):
            F.set(x, y, LEATHER[li])
    for k in (g0 - 1, g1):                                  # the bands holding the grip: lit brass
        for x, y in across(c, f, w, h, k):
            F.set(x, y, BRASS[min(4, i + 1)])
    if f == "up":
        for x, y in lengthwise(c, f, w, h, w // 2 - 1):     # the laced seam: thong crossing over a dark seam
            if g0 <= y < g1:
                F.set(x, y, LACE[1] if y % 2 else LEATHER[0])
                F.set(x + 1, y, LEATHER[0] if y % 2 else LACE[1])
    for k in c.info.get("bands", []):
        for x, y in across(c, f, w, h, k):
            F.set(x, y, BRASS[max(0, i - 1)])
    # bevel the brass only (the grip keeps its own tone; its edges are the bands)
    for x in range(w):
        if F.get(x, 0) == BRASS[i]:
            F.set(x, 0, BRASS[min(4, i + 1)])
        if F.get(x, h - 1) == BRASS[i]:
            F.set(x, h - 1, BRASS[max(0, i - 1)])
    for y in range(h):
        if F.get(0, y) == BRASS[i]:
            F.set(0, y, BRASS[min(4, i + 1)])
        if F.get(w - 1, y) == BRASS[i]:
            F.set(w - 1, y, BRASS[max(0, i - 1)])
        if F.get(0, y) == LEATHER[li]:
            F.set(0, y, LEATHER[min(3, li + 1)])
        if F.get(w - 1, y) == LEATHER[li]:
            F.set(w - 1, y, LEATHER[max(0, li - 1)])
    return F


def p_objective(c, f, w, h, rng):
    """The dew cap: brass, and on its mouth dark glass in a brass lip with one cold streak of reflection."""
    if f != "north":
        return p_brass(c, f, w, h, rng)
    F = Face(w, h, BRASS[3])
    for x in range(w):
        F.set(x, h - 1, BRASS[1])
    for y in range(h):
        F.set(w - 1, y, BRASS[1])
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            F.set(x, y, NIGHT[1] if x + y < w else NIGHT[0])
    F.set(1, 1, NIGHT[2])
    F.set(2, 1, NIGHT[2])
    F.set(1, 2, NIGHT[2])
    return F


def p_starglass(c, f, w, h, rng):
    """The Star Lens cell: a brass ring round pale blue glass, its glint glowing (the glowmask's texels)."""
    if f != "north":
        return p_brass(c, f, w, h, rng)
    F = Face(w, h, BRASS[4])
    for x in range(w):
        F.set(x, h - 1, BRASS[2])
    for y in range(h):
        F.set(w - 1, y, BRASS[2])
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            F.set(x, y, STAR[1] if x + y < w else STAR[0])
    F.shine(1, 1, STAR[3])
    F.shine(2, 1, STAR[2])
    F.shine(1, 2, STAR[2])
    return F


def p_finder(c, f, w, h, rng):
    """The finder scope: brass with a band, a tiny dark lens at the front."""
    if f == "north":
        F = Face(w, h, NIGHT[1])
        F.set(0, 0, NIGHT[2])
        return F
    return p_brass(c, f, w, h, rng)


def p_eyepiece(c, f, w, h, rng):
    """The eyepiece standing up at the back: knurled brass, a leather cup on top, dark glass in the cup."""
    if f == "up":
        F = Face(w, h, NIGHT[1])
        F.set(0, 0, NIGHT[2])
        return F
    if f == "down":
        return Face(w, h, BRASS[1])
    i = idx(c, f, BRASS, 2)
    F = Face(w, h, BRASS[i])
    F.set(0, 0, LEATHER[3])
    F.set(1, 0, LEATHER[2])
    for y in range(2, h, 2):
        F.set((y // 2) % 2, y, BRASS[max(0, i - 1)])
    for y in range(1, h):
        if F.get(0, y) == BRASS[i]:
            F.set(0, y, BRASS[min(4, i + 1)])
    return F


def p_walnut(c, f, w, h, rng):
    """A tripod leg: two-tone walnut down the stick (lit side, shade side), a brass shoe at the foot."""
    R = WALNUT
    i = idx(c, f, R, 2)
    if f in ("up", "down"):
        return Face(w, h, R[max(0, i - 1)])
    F = Face(w, h, R[i])
    for y in range(h):
        F.set(0, y, R[min(4, i + 1)])
        F.set(w - 1, y, R[max(0, i - 1)])
    for k in range(c.info.get("shoe", 0)):                  # the brass shoe
        for x, y in across(c, f, w, h, k):
            F.set(x, y, BRASS[3] if x == 0 else BRASS[1] if x == w - 1 else BRASS[2])
    for k in c.info.get("bands", []):                       # a brass collar
        for x, y in across(c, f, w, h, k):
            F.set(x, y, BRASS[3] if x == 0 else BRASS[2])
    return F


def p_tray(c, f, w, h, rng):
    """The accessory tray: walnut boards (a dark seam every 3 px) with a lit front edge."""
    R = WALNUT
    i = idx(c, f, R, 2)
    F = Face(w, h, R[i])
    if f == "up":
        for x in range(2, w, 3):
            for y in range(h):
                F.set(x, y, R[max(0, i - 1)])
    bevel(F, R, i, w, h)
    return F


def p_iron(c, f, w, h, rng):
    R = IRON
    i = idx(c, f, R, 2)
    F = Face(w, h, R[i])
    bevel(F, R, i, w, h)
    return F


def p_filter(c, f, w, h, rng):
    """The Nebula Filter's slide: a brass frame round deep violet glass with one lit corner."""
    i = idx(c, f, BRASS, 2)
    F = Face(w, h, BRASS[i])
    if f in ("north", "south") and w >= 3 and h >= 3:
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                F.set(x, y, NEBULA[1])
        F.set(1, 1, NEBULA[3])
        F.set(2, 1, NEBULA[2])
    bevel(F, BRASS, i, w, h)
    return F


PAINT = {"brass": p_brass, "tube": p_tube, "objective": p_objective, "starglass": p_starglass, "finder": p_finder,
         "eyepiece": p_eyepiece, "walnut": p_walnut, "tray": p_tray, "iron": p_iron, "filter": p_filter}


# ------------------------------------------------------------------ the model
def build():
    root = Bone("root", (0, 0, 0))

    # the tripod: three legs from the hub to the ground, one under the objective, two behind so the user kneels
    # between them; a tray across them with two spare eyepieces
    legs = Bone("legs", (0, 0, 0), parent=root)
    for k, (foot, top) in enumerate((((0, 0, -6), (0, 13, -1)), ((5, 0, 3), (1, 13, 1)), ((-5, 0, 3), (-1, 13, 1)))):
        seg(legs, f"leg_{k}", foot, top, 2, "walnut", shoe=2, bands=[11])
    box(legs, "tray", (-3, 5, -3), (3, 6, 3), "tray")
    box(legs, "spare_a", (-2, 6, 0), (-1, 8, 1), "brass")
    box(legs, "spare_b", (1, 6, -2), (2, 9, -1), "brass")

    # the head: hub over the legs, the turntable, a short iron post, the yoke with its two arms and the trunnion bolt
    head = Bone("head", (0, 13, 0), parent=root)
    box(head, "hub", (-2, 12, -2), (2, 14, 2), "brass", lift=-1)
    box(head, "turntable", (-3, 14, -3), (3, 15, 3), "brass")
    box(head, "post", (-1, 15, -1), (1, 17, 1), "iron")
    box(head, "yoke", (-4, 17, -2), (4, 18, 2), "brass")
    box(head, "arm_r", (3, 18, -2), (4, 22, 2), "brass", scale=True)
    box(head, "arm_l", (-4, 18, -2), (-3, 22, 2), "brass", scale=True)
    box(head, "trunnion", (-5, 19, -1), (5, 21, 1), "iron")

    # the tube, turned up at the rest elevation round the trunnion (objective to the north)
    tube = Bone("tube", PIVOT, rot=(ELEV, 0, 0), parent=root)
    Z = dict(axis="z")
    box(tube, "dew_cap", (-3, 17, -13), (3, 23, -9), "objective", bands=[3], **Z)
    box(tube, "body", (-2, 18, -9), (2, 22, 9), "tube", grip=(4, 13), bands=[16], **Z)
    box(tube, "ring", (-3, 17, 5), (3, 23, 6), "brass", lift=1, **Z)
    box(tube, "focuser", (-1, 19, 9), (1, 21, 15), "brass", knurl=[1, 2], hollow=False, **Z)
    box(tube, "focus_knob_r", (1, 19, 10), (2, 20, 11), "iron")
    box(tube, "focus_knob_l", (-2, 19, 10), (-1, 20, 11), "iron")
    box(tube, "eyepiece", (-1, 21, 13), (1, 25, 15), "eyepiece")
    box(tube, "finder_post_f", (-1, 22, -6), (1, 23, -4), "iron")
    box(tube, "finder_post_b", (-1, 22, -2), (1, 23, 0), "iron")
    box(tube, "finder", (-1, 23, -8), (1, 25, 1), "finder", bands=[1, 7], **Z)

    # tier parts (TelescopeRenderer hides them by the block's tier)
    lens = Bone("lens_cell", PIVOT, parent=tube)
    box(lens, "cell", (-3, 17, -14), (3, 23, -13), "starglass", **Z)
    filt = Bone("filter_slide", PIVOT, parent=tube)
    box(filt, "slide", (-3, 18, 11), (3, 22, 12), "filter")
    return root


def check_planes(root):
    """Rule 2 of models.md: no two faces in one plane facing the same way that overlap (unrotated parts per bone)."""
    bad = []
    for b in root.walk():
        cubes = [c for c in b.cubes if not c.rot]
        for i, c1 in enumerate(cubes):
            for c2 in cubes[i + 1:]:
                for ax in range(3):
                    for side in (0, 1):
                        p1 = c1.a[ax] if side == 0 else c1.b[ax]
                        p2 = c2.a[ax] if side == 0 else c2.b[ax]
                        if abs(p1 - p2) > 1e-6:
                            continue
                        o = [k for k in range(3) if k != ax]
                        if all(min(c1.b[k], c2.b[k]) - max(c1.a[k], c2.a[k]) > 1e-6 for k in o):
                            bad.append((b.name, c1.name, c2.name, "xyz"[ax], "-+"[side]))
    return bad


def main():
    root = build()
    for b, c in T.all_cubes(root):                        # whole pixels: sizes are checked by Cube, positions here
        if not c.rot:
            assert all(abs(v - round(v)) < 1e-6 for v in c.a + c.b), (c.name, c.a, c.b)
    bad = check_planes(root)
    for x in bad:
        print("same plane:", x)
    light_pass(root)
    T.PAINT, T.NAME, T.ROOT = PAINT, "telescope", OUT
    path, n, size = T.write(root)
    print(path, n, "cubes", size)


if __name__ == "__main__":
    main()
