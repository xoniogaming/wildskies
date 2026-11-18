"""The telescope block's model drafts (custom-block-mods skill; GeckoLib, owner: "GeckoLib: yes").

    python tools/telescope/make_telescope.py [a b c]      -> models/telescope/<draft>.bbmodel (+ _pose.bbmodel)

Three silhouettes, as REDESIGN_PLAN.md item 16 asked:
  a  classic brass refractor on a walnut tripod (star diagonal eyepiece, finder scope, altitude arc)
  b  surveyor's scope: short tube in a U-yoke on a brass setting circle, slim legs
  c  long walnut tube with brass bands on a heavy tripod
Each has the tier parts as their own bones (the Java hides them by the blockstate's tier):
  lens_cell    tier >= 1: a brass cell with pale blue glass on the objective (its glint glows)
  filter_slide tier 2:    a coloured glass slide through the eyepiece end
and a "_pose" copy with a grey player kneeling at the eyepiece (the owner: others should see someone stargazing).

Helpers (Bone, box, cbox, seg, Face, the writer) come from the boss-mods template, imported as a module.
Units are model pixels; origin = bottom centre of the block; the model faces north (-Z), +X is its right side.
The tube is aimed at a fixed rest elevation (owner: the tube does not follow the look).
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
Bone, box, cbox, seg, Face, ramp, mat = T.Bone, T.box, T.cbox, T.seg, T.Face, T.ramp, T.mat

# the kit's ramps (tools/art_redo/ramps.py), dark -> light
BRASS = ramp((58, 36, 12), (108, 74, 24), (160, 116, 40), (206, 164, 70), (242, 216, 140))
WALNUT = ramp((40, 24, 16), (62, 38, 24), (88, 56, 34), (118, 80, 50), (150, 108, 70))
LEATHER = ramp((46, 20, 14), (74, 34, 22), (104, 52, 32), (138, 76, 46), (172, 108, 68))
IRON = ramp((30, 28, 32), (56, 54, 58), (90, 86, 88), (134, 130, 126))
NIGHT = ramp((5, 8, 20), (10, 16, 40), (24, 34, 74), (38, 52, 100))
STAR = ramp((52, 80, 138), (88, 124, 186), (134, 176, 228), (188, 220, 250), (236, 246, 255))
NEBULA = ramp((70, 30, 74), (112, 48, 104), (164, 76, 132), (214, 128, 168))
VERDIGRIS = ramp((40, 78, 70), (70, 120, 104), (128, 176, 150))
LACE = ramp((46, 22, 14), (82, 42, 24), (164, 108, 66))
GREY = ramp((70, 72, 78), (98, 100, 108), (128, 130, 138), (160, 162, 170))


# ------------------------------------------------------------------ light: shade by the face's world normal
NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0),
           "down": (0, -1, 0)}


def light_pass(root):
    """c.info['shade'][face] = -2..+1, from the face's world normal (light from above and the model's right/front)."""
    for b, c in T.all_cubes(root):
        R = b.R() @ (mat(c.rot) if c.rot else np.eye(3))
        sh = {}
        for f, n in NORMALS.items():
            w = R @ np.array(n, float)
            v = 0.9 * w[1] + 0.35 * w[0] - 0.25 * w[2]
            sh[f] = 1 if v > 0.55 else 0 if v > -0.05 else -1 if v > -0.6 else -2
        c.info["shade"] = sh


def base(c, f, R, mid=2):
    return max(0, min(len(R) - 1, mid + c.info["shade"][f]))


def along(c, f):
    """Whether the cube's long axis (Y, the way seg builds sticks) runs down this face's rows."""
    return f in ("north", "south", "east", "west")


# ------------------------------------------------------------------ painters (ramps only, light per face)
def across(c, f, w, h, at):
    """Texels of a line round the cube at offset `at` (px from its -Z end for tube parts built along Z, from its bottom
    for sticks built along Y). Returns a list of (x, y) on face f."""
    if c.info.get("axis", "y") == "z":
        n = c.size()[2]
        if f in ("east", "west"):
            col = at if f == "west" else n - 1 - at   # u runs south -> north on the east face
            return [(col, y) for y in range(h)] if 0 <= col < w else []
        if f in ("up", "down"):
            return [(x, at) for x in range(w)] if 0 <= at < h else []
        return []
    if f in ("up", "down"):
        return []
    y = h - 1 - at
    return [(x, y) for x in range(w)] if 0 <= y < h else []


def lengthwise(c, f, w, h, k):
    """Texels of a line running along the cube's long axis, k px in from its first edge."""
    if c.info.get("axis", "y") == "z":
        if f in ("east", "west"):
            return [(x, k) for x in range(w)] if 0 <= k < h else []
        if f in ("up", "down"):
            return [(k, y) for y in range(h)] if 0 <= k < w else []
        return []
    if f in ("up", "down"):
        return []
    return [(k, y) for y in range(h)] if 0 <= k < w else []


def ends(c, f):
    """The faces a cube's long axis comes out of (end caps)."""
    return ("north", "south") if c.info.get("axis", "y") == "z" else ("up", "down")


def p_brass(c, f, w, h, rng):
    R = BRASS
    i = base(c, f, R, 2 + c.info.get("lift", 0))
    F = Face(w, h, R[i])
    if f in ends(c, f) and w >= 3 and h >= 3:          # an end cap: a lit rim round a darker hollow
        for x in range(w):
            for y in range(h):
                edge = x in (0, w - 1) or y in (0, h - 1)
                F.set(x, y, R[min(4, i + 1)] if edge and (x == 0 or y == 0) else R[max(0, i - 1)] if edge else R[i])
        return F
    if c.info.get("knurl"):
        for k in range(0, 99, 2):
            for x, y in across(c, f, w, h, k):
                F.set(x, y, R[max(0, i - 1)])
    for k in c.info.get("bands", []):                    # raised bands: dark line, lit line beside it
        for x, y in across(c, f, w, h, k):
            F.set(x, y, R[max(0, i - 1)])
    if c.info.get("seam") and f == "up":
        for x, y in lengthwise(c, f, w, h, w // 2):
            if F.get(x, y) == R[i]:
                F.set(x, y, R[min(4, i + 1)])
    for k in c.info.get("ticks", []):                    # engraved scale marks (altitude scale on the fork)
        if f == c.info.get("tick_face"):
            for x in range(min(w, 2)):
                F.set(x, h - 1 - k, R[max(0, i - 1)])
    if c.info.get("rimmed") and f == "up" and w >= 3 and h >= 3:
        for x in range(w):
            F.set(x, 0, R[min(4, i + 1)])
            F.set(x, h - 1, R[max(0, i - 1)])
        for y in range(h):
            F.set(0, y, R[min(4, i + 1)])
            F.set(w - 1, y, R[max(0, i - 1)])
    if c.info.get("bevel") and w >= 3 and h >= 3 and f not in ends(c, f):
        for x in range(w):                               # a lit edge on top, a dark one at the foot
            if F.get(x, 0) == R[i]:
                F.set(x, 0, R[min(4, i + 1)])
            if F.get(x, h - 1) == R[i]:
                F.set(x, h - 1, R[max(0, i - 1)])
        for y in range(1, h - 1):
            if F.get(0, y) == R[i]:
                F.set(0, y, R[min(4, i + 1)])
            if F.get(w - 1, y) == R[i]:
                F.set(w - 1, y, R[max(0, i - 1)])
    for x, y in c.info.get("green", {}).get(f, []):    # a little verdigris in a sheltered corner
        F.set(x, y, VERDIGRIS[1] if (x + y) % 2 else VERDIGRIS[0])
    return F


def p_walnut(c, f, w, h, rng):
    R = WALNUT
    i = base(c, f, R, 2)
    F = Face(w, h, R[i])
    if f in ("up", "down"):
        F.fill(R[max(0, i - 1)])
        return F
    if c.info.get("clean"):
        if w >= 2:
            for y in range(h):
                F.set(0, y, R[min(4, i + 1)])
                F.set(w - 1, y, R[max(0, i - 1)])
        for y in c.info.get("bands", []):
            if 0 <= y < h:
                for x in range(w):
                    F.set(x, h - 1 - y, BRASS[3 if c.info["shade"][f] >= 0 else 2])
        return F
    for x in range(w):                                   # grain: short darker runs down the stick
        y = rng.randrange(0, 5)
        while y < h:
            L = rng.randint(2, 4)
            for k in range(L):
                if y + k < h:
                    F.set(x, y + k, R[max(0, i - 1)])
            y += L + rng.randint(3, 7)
    for y in c.info.get("bands", []):
        if 0 <= y < h:
            for x in range(w):
                F.set(x, h - 1 - y, BRASS[3 if c.info["shade"][f] >= 0 else 2])
    return F


def p_leather(c, f, w, h, rng):
    """The tube's leather wrap: darker ends, a laced seam along the top."""
    R = LEATHER
    i = base(c, f, R, 2)
    F = Face(w, h, R[i])
    if f in ends(c, f):
        F.fill(R[max(0, i - 1)])
        return F
    n = c.size()[2] if c.info.get("axis", "y") == "z" else h
    for k in (0, n - 1):
        for x, y in across(c, f, w, h, k):
            F.set(x, y, R[max(0, i - 1)])
    if f == "up":
        for x, y in lengthwise(c, f, w, h, w // 2):
            if 0 < y < h - 1:
                F.set(x, y, LACE[2] if y % 2 else LEATHER[0])
    return F


def p_objective(c, f, w, h, rng):
    """The dew cap's mouth: a brass lip round dark glass, one cold glint top left."""
    if f != c.info.get("mouth", "up"):
        return p_brass(c, f, w, h, rng)
    F = Face(w, h, BRASS[1])
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            F.set(x, y, NIGHT[1] if (x + y) % 5 else NIGHT[2])
    F.set(2, 2, STAR[2])
    return F


def p_starglass(c, f, w, h, rng):
    """The Star Lens cell: brass ring, pale blue glass, a glint that glows."""
    if f != c.info.get("mouth", "up"):
        return p_brass(c, f, w, h, rng)
    F = Face(w, h, BRASS[3])
    for x in range(w):
        F.set(x, h - 1, BRASS[1])
    for y in range(h):
        F.set(w - 1, y, BRASS[1])
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            F.set(x, y, STAR[1] if x + y < w else STAR[0])
    F.shine(2, 2, STAR[4])
    F.shine(3, 2, STAR[3])
    F.shine(2, 3, STAR[3])
    return F


def p_filter(c, f, w, h, rng):
    """The Nebula Filter's slide (0.8.0): a brass frame all round, deep violet glass inside with one lit corner, so
    it reads as a fitted part, not a stray pink block."""
    R = NEBULA
    i = base(c, f, R, 1)
    F = Face(w, h, BRASS[base(c, f, BRASS, 2)])
    if w >= 3 and h >= 3:
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                F.set(x, y, R[i])
        F.set(1, 1, R[min(3, i + 2)])
    for x in range(w):
        F.set(x, h - 1, BRASS[1])
    return F


def p_iron(c, f, w, h, rng):
    return Face(w, h, IRON[base(c, f, IRON, 2)])


def p_grey(c, f, w, h, rng):
    return Face(w, h, GREY[base(c, f, GREY, 2)])


PAINT = {"brass": p_brass, "walnut": p_walnut, "leather": p_leather, "objective": p_objective,
         "starglass": p_starglass, "filter": p_filter, "iron": p_iron, "grey": p_grey}


# ------------------------------------------------------------------ parts
def tripod(root, apex_y, foot_r, t=2, spreader_y=None, heavy=False, clean=False):
    """Three legs from round the head (radius 1.5) to brass feet on the ground at foot_r: one under the objective
    (north), two to the back corners, so the user kneels in the gap at the south."""
    legs = Bone("legs", (0, 0, 0), parent=root)
    tops, feet = [], []
    for k, az in enumerate((180, 60, 300)):              # degrees from +Z: 180 = north
        a = math.radians(az)
        dx, dz = math.sin(a), math.cos(a)
        top = (1.5 * dx, apex_y, 1.5 * dz)
        foot = (foot_r * dx, 1.0, foot_r * dz)
        seg(legs, f"leg_{k}", foot, top, t, "walnut", bands=[1] if heavy else [2] if clean else [], clean=clean)
        cbox(legs, f"foot_{k}", (foot[0], 0.5 if not heavy else 1, foot[2]), (t + 1, 1 if not heavy else 2, t + 1),
             "brass")
        tops.append(top)
        feet.append(foot)
    if spreader_y is not None:
        pts = []
        for top, foot in zip(tops, feet):
            u = (spreader_y - foot[1]) / (top[1] - foot[1])
            pts.append(tuple(foot[i] + u * (top[i] - foot[i]) for i in range(3)))
        for k in range(3):
            p0, p1 = np.array(pts[k]), np.array(pts[(k + 1) % 3])
            seg(legs, f"spreader_{k}", p0 + 0.15 * (p1 - p0), p1 - 0.15 * (p1 - p0), 1, "brass")
    return legs


def tube_bone(root, pivot, elev):
    return Bone("tube", pivot, rot=(elev, 0, 0), parent=root)


def tier_parts(tube, front_z, back_z, size, slide_at, slim=False):
    """lens_cell on the objective (front_z is the mouth's z, the tube runs along -Z), filter_slide across the back."""
    lens = Bone("lens_cell", tube.pivot, parent=tube)
    s = size + 1
    c = box(lens, "cell", (tube.pivot[0] - s / 2, tube.pivot[1] - s / 2, front_z - 1.5),
            (tube.pivot[0] + s / 2, tube.pivot[1] + s / 2, front_z + 0.5), "starglass")
    c.info["mouth"] = "north"
    c.info["axis"] = "z"
    filt = Bone("filter_slide", tube.pivot, parent=tube)
    x0, y0 = tube.pivot[0], tube.pivot[1]
    if slim:                                                    # fitted through the focuser, one finger tab out
        box(filt, "slide", (x0 - 3, y0 - 2, slide_at), (x0 + 3, y0 + 2, slide_at + 1), "filter")
        box(filt, "slide_tab", (x0 - 4, y0 - 1, slide_at - 0.5), (x0 - 3, y0 + 1, slide_at + 1.5), "brass")
    else:
        box(filt, "slide", (x0 - 5, y0 - 2, slide_at), (x0 + 4, y0 + 2, slide_at + 1), "filter")
        box(filt, "slide_tab", (x0 - 6, y0 - 1, slide_at - 0.5), (x0 - 5, y0 + 1, slide_at + 1.5), "brass")
    return lens, filt


# ------------------------------------------------------------------ the three drafts
def draft_a(polish=False):
    """Classic brass refractor: dew cap, leather-wrapped tube, focuser, star diagonal with the eyepiece pointing up,
    finder scope, a brass fork with an altitude arc, walnut tripod with a brass spreader."""
    root = Bone("root", (0, 0, 0))
    tripod(root, 16, 7, spreader_y=6)
    head = Bone("head", (0, 16, 0), parent=root)
    box(head, "plate", (-3, 15, -3), (3, 17, 3), "brass", rimmed=True)
    box(head, "post", (-1, 17, -1), (1, 19, 1), "iron")
    box(head, "fork_r", (2, 17, -2), (3, 23, 2), "brass", lift=-1, ticks=[1, 3, 5], tick_face="east")
    box(head, "fork_l", (-3, 17, -2), (-2, 23, 2), "brass", lift=-1)
    box(head, "fork_base", (-3, 17, -2), (3, 18, 2), "brass")
    tube = tube_bone(root, (0, 21, 0), 28)
    Z = dict(axis="z")
    box(tube, "dew_cap", (-3, 18, -14), (3, 24, -8), "objective", mouth="north", bands=[1], **Z)
    box(tube, "tube_front", (-2, 19, -8), (2, 23, -4), "brass", seam=True, **Z)
    box(tube, "wrap", (-2.5, 18.5, -4), (2.5, 23.5, 3), "leather", **Z)
    box(tube, "tube_back", (-2, 19, 3), (2, 23, 7), "brass", bands=[2], seam=True,
        green={"west": [(1, 3), (2, 3)]}, **Z)
    box(tube, "trunnion", (-2.5, 20.5, -1), (2.5, 21.5, 1), "iron")
    box(tube, "focuser", (-1.5, 19.5, 7), (1.5, 22.5, 11), "brass", knurl=True, lift=-1, **Z)
    box(tube, "focus_knob", (1.5, 20, 8), (3.5, 21, 10), "iron")
    box(tube, "diagonal", (-1.5, 19.5, 11), (1.5, 22.5, 14), "brass", lift=1, **Z)
    box(tube, "eyepiece", (-1, 22.5, 11.5), (1, 26.5, 13.5), "brass", knurl=True)
    box(tube, "eyecup", (-1.5, 26.5, 11), (1.5, 27.5, 14), "leather")
    box(tube, "finder", (-1, 24.5, -6), (1, 26.5, 1), "brass", bands=[0], **Z)
    box(tube, "finder_ring_f", (-0.5, 23.5, -5), (0.5, 24.5, -4), "iron")
    box(tube, "finder_ring_b", (-0.5, 23.5, -1), (0.5, 24.5, 0), "iron")
    if polish:
        polish_a(head, tube)
    tier_parts(tube, -14, 14, 6, 9, slim=polish)
    return root


def polish_a(head, tube):
    """0.8.0, owner: "polish and clean up the actual model": a brass hub where the legs meet, brass rings at the
    tube's joints, a framed filter slide (an altitude arc of brass beads was tried and read as loose bits)."""
    box(head, "hub", (-2, 13, -2), (2, 15, 2), "brass", lift=-1, rimmed=True)
    for k, a in enumerate((60, 180, 300)):                     # a clamp bolt where each leg goes into the hub
        r = math.radians(a)
        box(head, f"clamp_{k}", (2.1 * math.sin(r) - 0.5, 13.5, 2.1 * math.cos(r) - 0.5),
            (2.1 * math.sin(r) + 0.5, 14.5, 2.1 * math.cos(r) + 0.5), "iron")
    Z = dict(axis="z")
    box(tube, "ring_cap", (-2.5, 18.5, -8.5), (2.5, 23.5, -7.5), "brass", lift=1, **Z)
    box(tube, "ring_back", (-2.5, 18.5, 6), (2.5, 23.5, 7), "brass", lift=1, **Z)


def final_a():
    """Draft A redone for the mod (0.8.0, owner: "the telescope still looks off", furniture mods as the reference):
    Let's Do's telescope reads because it is a few chunky parts with a lit edge on every face. So: a fatter tube
    (5 px, wrap 6, dew cap 7) that steps down towards the eyepiece, a shorter star diagonal, a stout fork and hub,
    clean two-tone walnut legs with a brass collar, and every brass face bevelled. Bone names are unchanged."""
    root = Bone("root", (0, 0, 0))
    tripod(root, 15, 7, t=2, spreader_y=6, clean=True)
    head = Bone("head", (0, 15, 0), parent=root)
    BV = dict(bevel=True)
    box(head, "hub", (-2.5, 13, -2.5), (2.5, 15, 2.5), "brass", lift=-1, **BV)
    box(head, "plate", (-3.5, 15, -3.5), (3.5, 16, 3.5), "brass", rimmed=True)
    box(head, "fork_base", (-3.5, 16, -2), (3.5, 17, 2), "brass", **BV)
    box(head, "fork_r", (2.5, 17, -2), (3.5, 23, 2), "brass", lift=-1, ticks=[1, 3, 5], tick_face="east", **BV)
    box(head, "fork_l", (-3.5, 17, -2), (-2.5, 23, 2), "brass", lift=-1, **BV)
    for k, a in enumerate((60, 180, 300)):
        r = math.radians(a)
        box(head, f"clamp_{k}", (2.6 * math.sin(r) - 0.5, 13.5, 2.6 * math.cos(r) - 0.5),
            (2.6 * math.sin(r) + 0.5, 14.5, 2.6 * math.cos(r) + 0.5), "iron")
    tube = tube_bone(root, (0, 21, 0), 28)
    Z = dict(axis="z")
    box(tube, "dew_cap", (-3.5, 17.5, -15), (3.5, 24.5, -9), "objective", mouth="north", bands=[1], bevel=True, **Z)
    box(tube, "ring_cap", (-3, 18, -9), (3, 24, -8), "brass", lift=1, **Z)
    box(tube, "tube_front", (-2.5, 18.5, -8), (2.5, 23.5, -4), "brass", seam=True, bevel=True, **Z)
    box(tube, "wrap", (-3, 18, -4), (3, 24, 3), "leather", **Z)
    box(tube, "tube_back", (-2, 19, 3), (2, 23, 7), "brass", bands=[2], seam=True, bevel=True,
        green={"west": [(1, 3), (2, 3)]}, **Z)
    box(tube, "ring_back", (-2.5, 18.5, 6), (2.5, 23.5, 7), "brass", lift=1, **Z)
    box(tube, "trunnion", (-3, 20.5, -1), (3, 21.5, 1), "iron")
    box(tube, "focuser", (-1.5, 19.5, 7), (1.5, 22.5, 10), "brass", knurl=True, lift=-1, **Z)
    box(tube, "focus_knob", (1.5, 20, 7.5), (3.5, 21, 9.5), "iron")
    box(tube, "diagonal", (-1.5, 19.5, 10), (1.5, 22.5, 13), "brass", lift=1, bevel=True, **Z)
    box(tube, "eyepiece", (-1, 22.5, 10.5), (1, 25.5, 12.5), "brass", knurl=True)
    box(tube, "eyecup", (-1.5, 25.5, 10), (1.5, 26.5, 13), "leather")
    box(tube, "finder", (-1, 25, -6), (1, 27, 1), "brass", bands=[0], bevel=True, **Z)
    box(tube, "finder_ring_f", (-0.5, 24, -5), (0.5, 25, -4), "iron")
    box(tube, "finder_ring_b", (-0.5, 24, -1), (0.5, 25, 0), "iron")
    tier_parts(tube, -15, 13, 7, 8, slim=True)
    return root


def draft_b():
    """Surveyor's scope: a short square brass tube in a U-yoke over a flat brass setting circle, a levelling head with
    three iron screws, slim walnut legs."""
    root = Bone("root", (0, 0, 0))
    tripod(root, 13, 7, t=1)
    head = Bone("head", (0, 13, 0), parent=root)
    box(head, "base", (-3, 12, -3), (3, 14, 3), "walnut")
    for k, (x, z) in enumerate(((0, -2.5), (2.2, 1.3), (-2.2, 1.3))):
        box(head, f"screw_{k}", (x - 0.5, 14, z - 0.5), (x + 0.5, 16, z + 0.5), "iron")
    box(head, "circle", (-5, 16, -5), (5, 17, 5), "brass", rimmed=True)
    box(head, "circle_hub", (-2, 17, -2), (2, 18, 2), "brass", lift=-1)
    box(head, "yoke_r", (3, 17, -1), (4, 24, 1), "brass")
    box(head, "yoke_l", (-4, 17, -1), (-3, 24, 1), "brass")
    box(head, "yoke_base", (-4, 17.5, -1), (4, 18.5, 1), "brass", lift=-1)
    box(head, "compass", (-2, 18, 1.5), (2, 19, 4.5), "iron")
    tube = tube_bone(root, (0, 22, 0), 22)
    box(tube, "hood", (-2.5, 19.5, -11), (2.5, 24.5, -7), "objective", mouth="north")
    box(tube, "tube", (-2, 20, -7), (2, 24, 5), "brass", bands=[3, 8])
    box(tube, "axle", (-3, 21.5, -0.5), (3, 22.5, 0.5), "iron")
    box(tube, "level", (-1, 24, -4), (1, 25, 2), "iron")
    box(tube, "eyepiece", (-1.5, 20.5, 5), (1.5, 23.5, 9), "brass", knurl=True)
    box(tube, "eyecup", (-1, 21, 9), (1, 23, 10), "leather")
    tier_parts(tube, -11, 9, 5, 6)
    return root


def draft_c():
    """Long walnut tube with brass bands and a brass objective, on a heavy walnut tripod with a brass head block."""
    root = Bone("root", (0, 0, 0))
    tripod(root, 15, 7, t=2, spreader_y=5, heavy=True)
    head = Bone("head", (0, 15, 0), parent=root)
    box(head, "block", (-3, 14, -3), (3, 21, 3), "walnut", bands=[5])
    box(head, "cap", (-3.5, 21, -3.5), (3.5, 22, 3.5), "brass", rimmed=True)
    box(head, "cradle_r", (2, 22, -3), (3, 25, 3), "brass")
    box(head, "cradle_l", (-3, 22, -3), (-2, 25, 3), "brass")
    tube = tube_bone(root, (0, 24.5, 0), 32)
    box(tube, "objective", (-3, 21.5, -15), (3, 27.5, -12), "objective", mouth="north")
    box(tube, "barrel_f", (-2.5, 22, -12), (2.5, 27, 0), "walnut", bands=[2, 9])
    box(tube, "barrel_b", (-2, 22.5, 0), (2, 26.5, 10), "walnut", bands=[1, 8])
    box(tube, "clamp", (-3, 21.5, -2), (3, 27.5, 1), "brass", lift=-1)
    box(tube, "drawtube", (-1.5, 23, 10), (1.5, 26, 13), "brass", bands=[1])
    box(tube, "eyepiece", (-1, 23.5, 13), (1, 25.5, 16), "brass", knurl=True)
    tier_parts(tube, -15, 16, 6, 11)
    return root


DRAFTS = {"a": ("telescope_a", draft_a), "b": ("telescope_b", draft_b), "c": ("telescope_c", draft_c)}


# ------------------------------------------------------------------ a grey player kneeling at the eyepiece (preview only)
def limb(bone, name, p0, p1, w, d, m):
    """A w x L x d box from p0 towards p1 (world = bone space for root children), like seg but not square."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    v = p1 - p0
    L = float(np.linalg.norm(v))
    v /= L
    n = max(1, int(round(L)))
    rx = math.degrees(math.asin(max(-1, min(1, v[2]))))
    rz = math.degrees(math.atan2(-v[0], v[1]))
    return box(bone, name, (p0[0] - w / 2, p0[1], p0[2] - d / 2), (p0[0] + w / 2, p0[1] + n, p0[2] + d / 2), m,
               rot=(round(rx, 2), 0.0, round(rz, 2)), pivot=tuple(p0))


def kneeling_player(root, eye, hands):
    """A grey player in vanilla's crouch (sneak) pose behind the eyepiece, head bowed over the eyecup, hands on the
    tube's back end. Crouching is a pose the game already has, so the Java only has to hold it. Preview only."""
    ex, ey, ez = eye
    p = Bone("player", (0, 0, 0), parent=root)
    hc = np.array([ex, ey + 4.0, ez + 2.0])
    head = Bone("p_head", tuple(hc + np.array([0, -4, 0])), rot=(-40, 0, 0), parent=p)
    cbox(head, "p_head", tuple(hc), (8, 8, 8), "grey")
    neck = hc + np.array([0, -4.5, 1.5])
    dy = neck[1] - 12.0
    hip = np.array([ex, 12.0, neck[2] + math.sqrt(max(0.0, 144 - dy * dy))])
    limb(p, "p_torso", hip, neck, 8, 4, "grey")
    up = (neck - hip) / np.linalg.norm(neck - hip)
    for s_, dx in (("r", -6), ("l", 6)):
        sh = hip + up * 10 + np.array([dx, 0, 0])
        limb(p, f"p_arm_{s_}", sh, np.array(hands[s_]) + np.array([dx * 0.4, 0, 0]), 4, 4, "grey")
        box(p, f"p_leg_{s_}", (ex + dx / 3 - 2, 0, hip[2] - 2), (ex + dx / 3 + 2, 12, hip[2] + 2), "grey")
    return p


def tube_point(root, q):
    t = {b.name: b for b in root.walk()}["tube"]
    return t.world(q)


def eye_point(root):
    bones = {b.name: b for b in root.walk()}
    t = bones["tube"]
    tops = []
    for c in t.cubes:
        if c.name in ("eyecup", "eyepiece"):
            for q in c.corners():
                tops.append(t.world(q))
    tops = np.array(tops)
    return float(tops[:, 0].mean()), float(tops[:, 1].max()), float(tops[:, 2].mean())


def write(name, root):
    light_pass(root)
    T.PAINT, T.NAME, T.ROOT = PAINT, name, OUT
    return T.write(root)


def report(name, root):
    pts = np.array([b.world(p) for b, c in T.all_cubes(root) for p in c.corners() if not b.name.startswith("p_")
                    and b.name != "player"])
    lo, hi = pts.min(0), pts.max(0)
    print(f"{name}: x {lo[0]:.1f}..{hi[0]:.1f}  y {lo[1]:.1f}..{hi[1]:.1f}  z {lo[2]:.1f}..{hi[2]:.1f}  "
          f"{sum(1 for _ in T.all_cubes(root))} cubes")


HANDS = {"a": ((-2.5, 21, 9), (3.5, 20.5, 9)), "b": ((-2, 22, 6), (2, 22, 6)), "c": ((-2, 24.5, 11), (2, 24.5, 11))}


def strip(root, names):
    for b in root.walk():
        b.bones = [x for x in b.bones if x.name not in names]


def final():
    """The picked draft (A, owner 2026-11-12) as the mod's model: every bone, the Java hides by tier."""
    root = final_a()
    write("telescope", root)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["final"]:
        final()
        return
    for key in (sys.argv[1:] or list(DRAFTS)):
        name, fn = DRAFTS[key]
        for tier, gone in ((0, {"lens_cell", "filter_slide"}), (1, {"filter_slide"}), (2, set())):
            root = fn()
            strip(root, gone)
            if tier == 2:
                report(name, root)
            write(f"{name}_t{tier}", root)
        posed = fn()
        strip(posed, {"lens_cell", "filter_slide"})
        r_, l_ = HANDS[key]
        kneeling_player(posed, eye_point(posed), {"r": tube_point(posed, r_), "l": tube_point(posed, l_)})
        write(name + "_pose", posed)
        print(f"  eye at {np.round(eye_point(posed), 1)}")


if __name__ == "__main__":
    main()
